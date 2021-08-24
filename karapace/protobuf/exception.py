def error(message: str):
    raise Exception(message)


class ProtobufParserRuntimeException(Exception):
    pass


class IllegalStateException(Exception):
    def __init__(self, message="IllegalStateException"):
        self.message = message
        super().__init__(self.message)


class IllegalArgumentException(Exception):
    def __init__(self, message="IllegalArgumentException"):
        self.message = message
        super().__init__(self.message)


class Error(Exception):
    """Base class for errors in this module."""


class ProtobufException(Error):
    """Generic Protobuf schema error."""


class SchemaParseException(ProtobufException):
    """Error while parsing a Protobuf schema descriptor."""

# ------------------------------------------------------------------------------
# Exceptions


class ProtobufTypeException(ProtobufException):
    """Raised when datum is not an example of schema."""

    def __init__(self, expected_schema, datum):
        pretty_expected = json.dumps(json.loads(str(expected_schema)), indent=2)
        fail_msg = "The datum %s is not an example of the schema %s" \
                   % (datum, pretty_expected)
        ProtobufSchema.ProtobufException.__init__(self, fail_msg)


class ProtobufSchemaResolutionException(ProtobufException):
    def __init__(self, fail_msg, writer_schema=None, reader_schema=None):
        pretty_writers = json.dumps(json.loads(str(writer_schema)), indent=2)
        pretty_readers = json.dumps(json.loads(str(reader_schema)), indent=2)
        if writer_schema: fail_msg += "\nWriter's Schema: %s" % pretty_writers
        if reader_schema: fail_msg += "\nReader's Schema: %s" % pretty_readers
        ProtobufSchema.ProtobufException.__init__(self, fail_msg)