# Design - Protobuf support in Aiven Karapace 

## Requirements

Karapace is a 1-to-1 replacement for Confluent’s Schema Registry but it lacks Google’s Protocol Buffers (Protobuf) support.

The aim of the project is to add Protobuf support to Aiven’s Karapace tool.

The following functionality should be implemented for MVP:

* Validating, storing, and versioning Protobuf schemas
* Protobuf schema evolution and compatibility
* Protobuf messages serialization/deserialization

Out of scope (not required for MVP):

* Custom references support for Protobuf schemas \
_Schema Registry supports references for Avro, JSON and Protobuf formats that was released in version 5.5. In Protobuf format references are external “.proto” files specified in “import” statements. \
Unfortunately Karapace doesn’t support references. It means that before implementing Protobuf “import” support common functionality to manage references for all the formats should be designed and implemented._
* Protobuf known dependencies \
_Known dependencies are predefined “.proto” files specified in “import” statements: Well-Known Types (part of Protobuf standard), Google Common Types, two Confluent .proto files. They are specific to Protobuf and differ from custom references: don’t affect public APIs, should be bundled with the distribution, not stored in Kafka. Custom references functionality is not required to implement this feature._
* Exhaustive tests \
_In scope of this MVP only required tests should be implemented. Test coverage can be improved with time by the community._
* Performance tests \
_Schema Registry has its own benchmark framework (modules and tests) for performance testing. The tests are not going to be provided with this MVP._

## Solution Design 

### Validating and Storing Protobuf Schemas

#### Overview

* Port required Square Wire code with tests (already ported)
* Implement Validation (already implemented)
* Implement storing & versioning (already implemented)
* Implement required tests
* &lt;include additional subtasks here>

#### Detail

Schema Registry Protobuf schema format management (parsing, validating, storing, comparing etc.) relies on Square Wire ([https://github.com/square/wire](https://github.com/square/wire)) Kotlin library.

To provide 1-to-1 compatibility with Schema Registry the subset of Wire Protobuf schema support functionality has been already ported to Python.

The following functionality has been already implemented and PR created:

1. Validating is based on the Wire functionality. If the schema is successfully parsed by Wire ProtoParser then we assume it is valid.
2. To store schema it has to be parsed and then serialized again using Wire library because Schema Registry code relies on binary equality when comparing Protobuf schemas.
3. Storing and Versioning of schemas in Kafka is already part of the current Karapace project and Protobuf integration relies on this code.

### Protobuf Schema Evolution and Compatibility

#### Overview

* Port required Square Wire code with tests (already ported)
* Implement Protobuf schema comparison and compatibility check functionality
* Implement required tests

#### Detail

Schema Registry compares schemas when a new version of the schema is going to be stored. It decides if these schemas are compatible by computing compatibility level.

The similar functionality is already developed for Avro schemas in Karapace. Comparison of Protobuf schemas is going to be implemented with the knowledge of Schema Registry protobuf comparison code.

The implementation will be compatible with Schema Registry but will be coded using Karapace approaches and common functionality (similar to Avro).

Comparison of Wire ProtoFileElement fields will be implemented inside of ported Wire classes. Other logic is going to be implemented in ProtobufSchema class. Code will be written from scratch and as a part of functionality will be added to Square Wire ported classes. 

Endpoints which will have compatibility support and will be directly affected by it 

1. POST /compatibility/subjects/&lt;subject:path>/versions/&lt;version:path> 
2. POST /subjects/(string: subject)

Interface of the endpoints must be unchanged. Protobuf schema type support will be added.

### Protobuf Message Serialization/Deserialization

#### Overview

* Implement creation of Python modules using protoc
* Load the dynamic modules in runtime to serialize/deserialize/verify Protobuf messages
* Implement required tests

#### Detail

Confluent REST Proxy features serialization and deserialization functionality that is partially implemented in Karapace in “kafka_rest_apis” folder of the repository for Avro and JSON formats.

##### Suggested approach

1. Run Google protoc in runtime to compile Protobuf schemas into modules
2. Load the modules dynamically and run them to serialize/deserialize messages

##### Offered deserialization procedure

1. Receive Confluent serialized data record. Its format is described in confluent docs and looks like : [Magic Byte] + [SchemaID] + [Message Index Data] + [Message Payload].
2. Get schema by SchemaID from Kafka. 
3. Get indexes of corresponding messages
4. Find the name of the message type by these indexes
5. If the corresponding Google Protobuf module for the schema is already loaded then use it to parse MessagePayload.
6. If the corresponding Google Protobuf module for the schema is not loaded in memory then store the schema to a predefined place in the file system with a unique file name and package name.
7. Compile the stored schema by protoc to get Google Protobuf Python module capable for deserialization of this schema.
8. Import the corresponding Python module into the Karapace process and use it to parse MessagePayload.

##### Caching modules

Different strategies are applicable. Modules can be kept in the file system and reused or remove from FS right after importing in python

##### Memory usage

Python is a dynamic language and its memory usage is controlled by a garbage collector that must release not referenced resources. Generated by protoc Python modules contain classes. These classes depend on the Python Google.protobuf library. 

In the process of importing the classes are registered and referenced by Google.protobuf library. It is not possible to unload modules out of the Python process as soon as registering/deregistering methods in Google.protobuf are undocumented.

##### Advantages

* The Python modules generated by protoc have full serialization/deserialization support of messages by given schema (.proto fil)e and do not require additional testing
* A few tests are required only to verify integration with Karapace
* The modules are proved to be efficient

## Public Interfaces 

Protobuf support should be added as a new schema format only to existing API endpoints and should not affect existing (Avro and JSON) schema format functionality.

The API endpoints for all the schema formats should work in 1-to-1 compatible to Schema Registry after adding Protobuf integration.

## Test plan

Each module/class will have a minimal set of unit tests. Also, high level functional should have at least a few integration tests.

Changes to Karapace should not affect most of the existing tests.

### Required tests

1. Schema validation tests. Most of the functionality is already covered by Wire library tests ported to Python. Initial integration of Karapace with Wire that features schema validation has been already implemented in “protobuf-mvp” branch on github.com/instaclustr/karapace with a few basic tests.
2. Message serialization/deserialization basic unit and integration tests covering success and failure scenarios.
3. Compatibility. At least a few tests for each compatibility level covering success and failure scenarios.

## Alternatives considered

Message Serialization/Deserialization can be implemented using alternative Python libraries that can parse Protobuf messages. But so far we do not have a good library with such functionality.

### BlackBox Protobuf Burp Extension

Serialization/deserialization alternative

#### Advantages

* It can be used as a static Python module that is better for distribution
* Doesn’t use file system and external tools (unlike protoc approach)
* Better memory consumption (single module unlike multiple in protoc approach)

#### Disadvantages

* It doesn’t support importing .proto files. It means that parsing of .proto schema should be implemented using different library (e.g. Square Wire) and then converted to type definition supported by this library for encoding
* Doesn’t support “import” statements. Resolving even well-known dependencies will require development
* Performance most likely is not so good as protoc generated modules that are proved to be very efficient and use C libraries as the backend
* Decodes raw binary data. It doesn’t support validation and mapping against a .proto schema. All the logic of mapping against .proto schema should be implemented manually including support of Protobuf features like: oneof, enum, option
* Doesn’t allow encoding by provided schema. It should be provided with fields data and corresponding fields types to encode a message.
* Unlike protoc approach requires developing multiple unit-tests to ensure that decoding and encoding works correctly against Protobuf schemas and all its features (oneof, enum, option, import)
