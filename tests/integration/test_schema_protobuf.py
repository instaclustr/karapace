"""
karapace - schema tests

Copyright (c) 2019 Aiven Ltd
See LICENSE for details
"""
from karapace.client import Client
from karapace.protobuf.kotlin_wrapper import trim_margin
from tests.utils import create_subject_name_factory

import logging
import pytest

baseurl = "http://localhost:8081"


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


log = logging.getLogger(__name__)


@pytest.mark.parametrize("trail", ["", "/"])
async def test_protobuf_schema_compatibility(registry_async_client: Client, trail: str) -> None:
    subject = create_subject_name_factory(f"test_protobuf_schema_compatibility-{trail}")()

    res = await registry_async_client.put(f"config/{subject}{trail}", json={"compatibility": "BACKWARD"})
    assert res.status_code == 200

    original_schema = """
            |syntax = "proto3";
            |package a1;
            |message TestMessage {
            |    message Value {
            |        string str2 = 1;
            |        int32 x = 2;
            |    }
            |    string test = 1;
            |    .a1.TestMessage.Value val = 2;
            |}
            |"""

    original_schema = trim_margin(original_schema)

    res = await registry_async_client.post(
        f"subjects/{subject}/versions{trail}", json={"schemaType": "PROTOBUF", "schema": original_schema}
    )
    assert res.status_code == 200
    assert "id" in res.json()

    evolved_schema = """
            |syntax = "proto3";
            |package a1;
            |message TestMessage {
            |    message Value {
            |        string str2 = 1;
            |        Enu x = 2;
            |    }
            |    string test = 1;
            |    .a1.TestMessage.Value val = 2;
            |    enum Enu {
            |        A = 0;
            |        B = 1;
            |    }
            |}
            |"""
    evolved_schema = trim_margin(evolved_schema)

    res = await registry_async_client.post(
        f"compatibility/subjects/{subject}/versions/latest{trail}",
        json={"schemaType": "PROTOBUF", "schema": evolved_schema},
    )
    assert res.status_code == 200
    assert res.json() == {"is_compatible": True}

    res = await registry_async_client.post(
        f"subjects/{subject}/versions{trail}", json={"schemaType": "PROTOBUF", "schema": evolved_schema}
    )
    assert res.status_code == 200
    assert "id" in res.json()

    res = await registry_async_client.post(
        f"compatibility/subjects/{subject}/versions/latest{trail}",
        json={"schemaType": "PROTOBUF", "schema": original_schema},
    )
    assert res.json() == {"is_compatible": True}
    assert res.status_code == 200
    res = await registry_async_client.post(
        f"subjects/{subject}/versions{trail}", json={"schemaType": "PROTOBUF", "schema": original_schema}
    )
    assert res.status_code == 200
    assert "id" in res.json()


async def test_protobuf_schema_references(registry_async_client: Client) -> None:

    customer_schema = """
            |syntax = "proto3";
            |package a1;
            |message Customer {
            |        string name = 1;
            |        int32 code = 2;
            |}
            |"""

    customer_schema = trim_margin(customer_schema)
    res = await registry_async_client.post(
        "subjects/customer/versions", json={"schemaType": "PROTOBUF", "schema": customer_schema}
    )
    assert res.status_code == 200
    assert "id" in res.json()
    original_schema = """
            |syntax = "proto3";
            |package a1;
            |import "Customer.proto";
            |message TestMessage {
            |    message Value {
            |        Customer customer = 1;
            |        int32 x = 2;
            |    }
            |    string test = 1;
            |    .a1.TestMessage.Value val = 2;
            |}
            |"""

    original_schema = trim_margin(original_schema)
    references = [{"name": "Customer.proto", "subject": "customer", "version": 1}]
    res = await registry_async_client.post(
        "subjects/test_schema/versions",
        json={"schemaType": "PROTOBUF", "schema": original_schema, "references": references},
    )
    assert res.status_code == 200
    assert "id" in res.json()
    res = await registry_async_client.get("subjects/test_schema/versions/latest", json={})
    assert res.status_code == 200
    myjson = res.json()
    assert "id" in myjson
    references = [{"name": "Customer.proto", "subject": "customer", "version": 1}]
    refs2 = myjson["references"]
    assert not any(x != y for x, y in zip(refs2, references))
