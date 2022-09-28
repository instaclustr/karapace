from karapace.config import read_config
from karapace.protobuf.dependency import ProtobufDependencyVerifier
from karapace.serialization import (
    InvalidMessageHeader,
    InvalidMessageSchema,
    InvalidPayload,
    SchemaRegistryDeserializer,
    SchemaRegistrySerializer,
    START_BYTE,
)
from tests.utils import test_fail_objects_protobuf, test_objects_protobuf

import logging
import pytest
import struct

log = logging.getLogger(__name__)


async def test_protobuf_dependency_verifier():
    declared_types = [
        ".a1.Place",
        "Place",
        ".a1.Customer",
        "Customer",
        ".a1.TestMessage",
        "TestMessage",
        ".a1",
        ".TestMessage",
        ".Enum",
        "TestMessage.Enum",
        ".a1.TestMessage.Value",
        "TestMessage.Value",
        ".a1.TestMessage.Value.Label",
        "TestMessage",
        ".Value.Label",
    ]

    used_types = [
        ".a1.Place;string",
        ".a1.Place;int32",
        ".a1.Customer;string",
        ".a1.Customer;int32",
        ".a1.Customer;Place",
        ".a1.TestMessage;int32",
        ".a1.TestMessage;int32",
        ".a1.TestMessage;string",
        ".a1.TestMessage;.a1.TestMessage.Value",
        "TestMessage;Customer",
        "TestMessage;int32",
        "TestMessage.Value;int32",
        "TestMessage.Value;string",
    ]

    verifier = ProtobufDependencyVerifier()
    for declared in declared_types:
        verifier.add_declared_type(declared)
    for used in used_types:
        x = used.split(";")
        verifier.add_used_type(x[0], x[1])

    result = verifier.verify()
    assert result.result, True

    verifier.add_used_type("TestMessage.Delta", "Tag")
    assert result.result, False

