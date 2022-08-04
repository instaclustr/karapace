# Ported from square/wire:
# wire-library/wire-schema/src/commonMain/kotlin/com/squareup/wire/schema/Schema.kt
# Ported partially for required functionality.
from karapace.protobuf.compare_result import CompareResult
from karapace.protobuf.enum_element import EnumElement
from karapace.protobuf.exception import IllegalArgumentException
from karapace.protobuf.known_dependency import DependenciesHardcoded, KnownDependency
from karapace.protobuf.location import Location
from karapace.protobuf.message_element import MessageElement
from karapace.protobuf.one_of_element import OneOfElement
from karapace.protobuf.option_element import OptionElement
from karapace.protobuf.proto_file_element import ProtoFileElement
from karapace.protobuf.proto_parser import ProtoParser
from karapace.protobuf.type_element import TypeElement
from karapace.protobuf.utils import append_documentation, append_indented
from karapace.schema_references import References
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from karapace.schema_reader import KafkaSchemaReader


def add_slashes(text: str) -> str:
    escape_dict = {
        "\a": "\\a",
        "\b": "\\b",
        "\f": "\\f",
        "\n": "\\n",
        "\r": "\\r",
        "\t": "\\t",
        "\v": "\\v",
        "'": "\\'",
        '"': '\\"',
        "\\": "\\\\",
    }
    trans_table = str.maketrans(escape_dict)
    return text.translate(trans_table)


def message_element_string(element: MessageElement) -> str:
    result = []
    append_documentation(result, element.documentation)
    result.append(f"message {element.name} {{")
    if element.reserveds:
        result.append("\n")
        for reserved in element.reserveds:
            append_indented(result, reserved.to_schema())

    if element.options:
        result.append("\n")
        for option in element.options:
            append_indented(result, option_element_string(option))

    if element.fields:
        result.append("\n")
        for field in element.fields:
            append_indented(result, field.to_schema())

    if element.one_ofs:
        result.append("\n")
        for one_of in element.one_ofs:
            append_indented(result, one_of.to_schema())

    if element.groups:
        result.append("\n")
        for group in element.groups:
            append_indented(result, group.to_schema())

    if element.extensions:
        result.append("\n")
        for extension in element.extensions:
            append_indented(result, extension.to_schema())

    if element.nested_types:
        result.append("\n")
        for nested_type in element.nested_types:
            if isinstance(nested_type, MessageElement):
                append_indented(result, message_element_string(nested_type))

        for nested_type in element.nested_types:
            if isinstance(nested_type, EnumElement):
                append_indented(result, enum_element_string(nested_type))

    result.append("}\n")
    return "".join(result)


def enum_element_string(element: EnumElement) -> str:
    return element.to_schema()


def option_element_string(option: OptionElement) -> str:
    result: str
    if option.kind == OptionElement.Kind.STRING:
        name: str
        if option.is_parenthesized:
            name = f"({option.name})"
        else:
            name = option.name
        value = add_slashes(str(option.value))
        result = f'{name} = "{value}"'
    else:
        result = option.to_schema()

    return f"option {result};\n"


class Dependency:
    def __init__(self, name: str, subject: str, version: int, schema: "ProtobufSchema") -> None:
        self.name = name
        self.subject = subject
        self.version = version
        self.schema = schema

    def identifier(self) -> str:
        return self.name + "_" + self.subject + "_" + str(self.version)


class DependencyVerifierResult:
    def __init__(self, result: bool, message: Optional[str] = ""):
        self.result = result
        self.message = message


class DependencyVerifier:
    def __init__(self):
        self.declared_types = list()
        self.used_types = list()
        self.import_path = list()

    def add_declared_type(self, full_name: str):
        self.declared_types.append(full_name)

    def add_used_type(self, parent: str, element_type: str):
        if element_type.find("map<") == 0:
            end = element_type.find(">")
            virgule = element_type.find(",")
            key = element_type[4:virgule]
            value = element_type[virgule + 1 : end]
            value = value.strip()
            self.used_types.append(parent + ";" + key)
            self.used_types.append(parent + ";" + value)
            # raise ProtobufUnresolvedDependencyException(f"Error in parsing string: {parent+'.'+element_type}")
        else:
            self.used_types.append(parent + ";" + element_type)

    def add_import(self, import_name: str):
        self.import_path.append(import_name)

    def verify(self) -> DependencyVerifierResult:
        declared_index = set(self.declared_types)
        for used_type in self.used_types:
            delimiter = used_type.rfind(";")
            used_type_with_scope = ""
            if delimiter != -1:
                used_type_with_scope = used_type[:delimiter] + "." + used_type[delimiter + 1 :]
                used_type = used_type[delimiter + 1 :]

            # TODO: it must be improved !!!
            if not (
                used_type in DependenciesHardcoded.index
                or KnownDependency.index_simple.get(used_type) is not None
                or KnownDependency.index.get(used_type) is not None
                or used_type in declared_index
                or (delimiter != -1 and used_type_with_scope in declared_index)
                or "." + used_type in declared_index
            ):
                return DependencyVerifierResult(False, f"type {used_type} is not defined")

        # result: DependencyVerifierResult = self.verify_ciclyc_dependencies()
        # if not result.result:
        #    return result
        return DependencyVerifierResult(True)

    # def verify_ciclyc_dependencies(self) -> DependencyVerifierResult:

    # TODO: add recursion detection
    #   return DependencyVerifierResult(True)


def _process_one_of(verifier: DependencyVerifier, package_name: str, parent_name: str, one_of: OneOfElement):
    parent = package_name + "." + parent_name
    for field in one_of.fields:
        verifier.add_used_type(parent, field.element_type)


class ProtobufSchema:
    DEFAULT_LOCATION = Location.get("")

    def __init__(
        self, schema: str, references: Optional[References] = None, schema_reader: Optional["KafkaSchemaReader"] = None
    ) -> None:
        if type(schema).__name__ != "str":
            raise IllegalArgumentException("Non str type of schema string")
        self.dirty = schema
        self.cache_string = ""
        self.schema_reader = schema_reader
        self.proto_file_element = ProtoParser.parse(self.DEFAULT_LOCATION, schema)
        self.references = references
        self.dependencies: Dict[str, Dependency] = dict()
        self.reslove_dependencies()

    def gather_deps(self) -> DependencyVerifier:
        verifier = DependencyVerifier()
        self.collect_dependencies(verifier)
        return verifier

    def verify_schema_dependencies(self) -> DependencyVerifierResult:
        verifier = DependencyVerifier()
        self.collect_dependencies(verifier)
        return verifier.verify()

    def collect_dependencies(self, verifier: DependencyVerifier):

        for key in self.dependencies:
            self.dependencies[key].schema.collect_dependencies(verifier)
        # verifier.add_import?? we have no access to own Kafka structure from this class...
        # but we need data to analyse imports to avoid ciclyc dependencies...

        package_name = self.proto_file_element.package_name
        if package_name is None:
            package_name = ""
        else:
            package_name = "." + package_name
        for element_type in self.proto_file_element.types:
            type_name = element_type.name
            full_name = package_name + "." + type_name
            verifier.add_declared_type(full_name)
            verifier.add_declared_type(type_name)
            if isinstance(element_type, MessageElement):
                for one_of in element_type.one_ofs:
                    _process_one_of(verifier, package_name, type_name, one_of)
                for field in element_type.fields:
                    verifier.add_used_type(full_name, field.element_type)
            for nested_type in element_type.nested_types:
                self._process_nested_type(verifier, package_name, type_name, nested_type)

    def _process_nested_type(self, verifier: DependencyVerifier, package_name: str, parent_name, element_type: TypeElement):

        verifier.add_declared_type(package_name + "." + parent_name + "." + element_type.name)
        verifier.add_declared_type(parent_name + "." + element_type.name)

        if isinstance(element_type, MessageElement):
            for one_of in element_type.one_ofs:
                _process_one_of(verifier, package_name, parent_name, one_of)
            for field in element_type.fields:
                verifier.add_used_type(parent_name, field.element_type)
        for nested_type in element_type.nested_types:
            self._process_nested_type(verifier, package_name, parent_name + "." + element_type.name, nested_type)

    def __str__(self) -> str:
        if not self.cache_string:
            self.cache_string = self.to_schema()
        return self.cache_string

    def to_schema(self) -> str:
        strings = []
        shm: ProtoFileElement = self.proto_file_element
        if shm.syntax:
            strings.append('syntax = "')
            strings.append(str(shm.syntax))
            strings.append('";\n')

        if shm.package_name:
            strings.append("package " + str(shm.package_name) + ";\n")

        if shm.imports or shm.public_imports:
            strings.append("\n")

            for file in shm.imports:
                strings.append('import "' + str(file) + '";\n')

            for file in shm.public_imports:
                strings.append('import public "' + str(file) + '";\n')

        if shm.options:
            strings.append("\n")
            for option in shm.options:
                strings.append(option_element_string(option))

        if shm.types:
            strings.append("\n")
            for type_element in shm.types:
                if isinstance(type_element, MessageElement):
                    strings.append(message_element_string(type_element))
            for type_element in shm.types:
                if isinstance(type_element, EnumElement):
                    strings.append(enum_element_string(type_element))

        if shm.extend_declarations:
            strings.append("\n")
            for extend_declaration in shm.extend_declarations:
                strings.append(str(extend_declaration.to_schema()))

        if shm.services:
            strings.append("\n")
            for service in shm.services:
                strings.append(str(service.to_schema()))
        return "".join(strings)

    def compare(self, other: "ProtobufSchema", result: CompareResult) -> CompareResult:
        self.proto_file_element.compare(other.proto_file_element, result)

    def reslove_dependencies(self):
        if self.references is None:
            return
        try:
            for r in self.references.val():
                subject = r["subject"]
                version = r["version"]
                name = r["name"]
                subject_data = self.schema_reader.subjects.get(subject)
                schema_data = subject_data["schemas"][version]
                schema = schema_data["schema"].schema_str
                references = schema_data.get("references")
                parsed_schema = ProtobufSchema(schema, references)
                self.dependencies[name] = Dependency(name, subject, version, parsed_schema)
        except Exception as e:
            # TODO: need the exception?
            raise e
