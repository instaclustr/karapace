from google.protobuf.descriptor import FieldDescriptor

sTypeMap = {
    "double": FieldDescriptor.TYPE_DOUBLE,
    "float": FieldDescriptor.TYPE_FLOAT,
    "int32": FieldDescriptor.TYPE_INT32,
    "int64": FieldDescriptor.TYPE_INT64,
    "uint32": FieldDescriptor.TYPE_UINT32,
    "uint64": FieldDescriptor.TYPE_UINT64,
    "sint32": FieldDescriptor.TYPE_SINT32,
    "sint64": FieldDescriptor.TYPE_SINT64,
    "fixed32": FieldDescriptor.TYPE_FIXED32,
    "fixed64": FieldDescriptor.TYPE_FIXED64,
    "sfixed32": FieldDescriptor.TYPE_SFIXED32,
    "sfixed64": FieldDescriptor.TYPE_SFIXED64,
    "bool": FieldDescriptor.TYPE_BOOL,
    "string": FieldDescriptor.TYPE_STRING,
    "bytes": FieldDescriptor.TYPE_BYTES
    # "enum": FieldDescriptor.TYPE_ENUM,   SchemaRegistry not support it yet
    # "message": FieldDescriptor.TYPE_MESSAGE,
    # "group": FieldDescriptor.TYPE_GROUP,
}

sLabelMap = {
    "optional": FieldDescriptor.LABEL_OPTIONAL,
    "required": FieldDescriptor.LABEL_REQUIRED,
    "repeated": FieldDescriptor.LABEL_REPEATED,
}
class imdict(dict):
    def __hash__(self):
        return id(self)

    def _immutable(self, *args, **kws):
        raise TypeError('object is immutable')

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear       = _immutable
    update      = _immutable
    setdefault  = _immutable
    pop         = _immutable
    popitem     = _immutable



class ProtobufSchema:


    def __init__(self, schema_string, name, version=None, references=None, dependencies=None):
        self._name = name
        self._schema_string = schema_string
        self._references = references
        self._version = version
        if references : self._references = imdict(references)
        if dependencies : self._dependencies = tuple(resolved_references)


    

    def schema_type(self) -> str:
        return


    def __getattr__(self, name):
        return


    def get_canonical_string(self) -> str:
        return ""


    def references(self) -> dict:
        return {}


    def validate(self) -> bool:
        return True


    def is_backward_compatible(self, previous_schema ) -> bool:
        return True


    def is_compatible(self)-> bool:
        return True

# CompatibilityLevel level, List<? extends ParsedSchema> previousSchemas) {
#   for (ParsedSchema previousSchema : previousSchemas) {
#     if (!schemaType().equals(previousSchema.schemaType())) {
#       return Collections.singletonList("Incompatible because of different schema type");
#     }
#   }
#   return CompatibilityChecker.checker(level).isCompatible(this, previousSchemas);


    def raw_schema(self) -> object:
        return None


    def deep_equals(self, schema) -> bool:
        return self.raw_schema() == schema.raw_schema()


    def parse_schema(self, schema_string: str) -> bool:
        return True

