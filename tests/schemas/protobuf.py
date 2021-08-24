schema_protobuf_plain = """syntax = "proto3";
package com.codingharbour.protobuf;

option java_outer_classname = "SimpleMessageProtos";
message SimpleMessage {
  string content = 1;
  string date_time = 2;
  string content2 = 3;
}
"""

schema_protobuf_schema_registry1 = """
|syntax = "proto3";
|package com.codingharbour.protobuf;
|
|message SimpleMessage {
|  string content = 1;
|  string my_string = 2;
|  int32 my_int = 3;
|}
|
"""

schema_protobuf_order_before = """
|syntax = "proto3";
|
|option java_package = "com.codingharbour.protobuf";
|option java_outer_classname = "TestEnumOrder";
|
|enum Enum {
|  HIGH = 0;
|  MIDDLE = 1;
|  LOW = 2;
|}
|message Message {
|  int32 query = 1;
|}
"""

schema_protobuf_order_after = """
|syntax = "proto3";
|
|option java_package = "com.codingharbour.protobuf";
|option java_outer_classname = "TestEnumOrder";
|
|message Message {
|  int32 query = 1;
|}
|enum Enum {
|  HIGH = 0;
|  MIDDLE = 1;
|  LOW = 2;
|}
|
"""

schema_protobuf_order_before1 = """
|syntax = "proto2";
|
|package tutorial;
|
|message Person {
|  optional string name = 1;
|  optional int32 id = 2;
|  optional string email = 3;
|
|  enum PhoneType {
|    MOBILE = 0;
|    HOME = 1;
|    WORK = 2;
|  }
|
|  message PhoneNumber {
|    optional string number = 1;
|    optional PhoneType type = 2 [default = HOME];
|  }
|
|  repeated PhoneNumber phones = 4;
|}
|
|message AddressBook {
|  repeated Person people = 1;
|}
|
"""