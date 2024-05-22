"""
karapace - schema tests

Copyright (c) 2023 Aiven Ltd
See LICENSE for details
"""
from karapace.client import Client

import json

baseurl = "http://localhost:8081"


async def test_avro_references(registry_async_client: Client) -> None:
    schema_country = {
        "type": "record",
        "name": "Country",
        "namespace": "com.netapp",
        "fields": [{"name": "name", "type": "string"}, {"name": "code", "type": "string"}],
    }

    schema_address = {
        "type": "record",
        "name": "Address",
        "namespace": "com.netapp",
        "fields": [
            {"name": "street", "type": "string"},
            {"name": "city", "type": "string"},
            {"name": "postalCode", "type": "string"},
            {"name": "country", "type": "Country"},
        ],
    }

    schema_job = {
        "type": "record",
        "name": "Job",
        "namespace": "com.netapp",
        "fields": [{"name": "title", "type": "string"}, {"name": "salary", "type": "double"}],
    }

    schema_person = {
        "type": "record",
        "name": "Person",
        "namespace": "com.netapp",
        "fields": [
            {"name": "name", "type": "string"},
            {"name": "age", "type": "int"},
            {"name": "address", "type": "Address"},
            {"name": "job", "type": "Job"},
        ],
    }

    res = await registry_async_client.post("subjects/country/versions", json={"schema": json.dumps(schema_country)})
    assert res.status_code == 200
    assert "id" in res.json()

    country_references = [{"name": "country.avsc", "subject": "country", "version": 1}]
    res = await registry_async_client.post(
        "subjects/address/versions",
        json={"schemaType": "AVRO", "schema": json.dumps(schema_address), "references": country_references},
    )
    assert res.status_code == 200
    assert "id" in res.json()
    address_id = res.json()["id"]

    # Check if the schema has now been registered under the subject

    res = await registry_async_client.post(
        "subjects/address",
        json={"schemaType": "AVRO", "schema": json.dumps(schema_address), "references": country_references},
    )
    assert res.status_code == 200
    assert "subject" in res.json()
    assert "id" in res.json()
    assert address_id == res.json()["id"]
    assert "version" in res.json()
    assert "schema" in res.json()

    res = await registry_async_client.post("subjects/job/versions", json={"schema": json.dumps(schema_job)})
    assert res.status_code == 200
    assert "id" in res.json()

    two_references = [
        {"name": "address.avsc", "subject": "address", "version": 1},
        {"name": "job.avsc", "subject": "job", "version": 1},
    ]

    res = await registry_async_client.post(
        "subjects/person/versions",
        json={"schemaType": "AVRO", "schema": json.dumps(schema_person), "references": two_references},
    )
    assert res.status_code == 200
    assert "id" in res.json()

    result = {
        "id": 4,
        "references": [
            {"name": "address.avsc", "subject": "address", "version": 1},
            {"name": "job.avsc", "subject": "job", "version": 1},
        ],
        "schema": json.dumps(
            {
                "fields": [
                    {"name": "name", "type": "string"},
                    {"name": "age", "type": "int"},
                    {"name": "address", "type": "Address"},
                    {"name": "job", "type": "Job"},
                ],
                "name": "Person",
                "namespace": "com.netapp",
                "type": "record",
            },
            separators=(",", ":"),
        ),
        "subject": "person",
        "version": 1,
    }

    res = await registry_async_client.get("subjects/person/versions/latest")
    assert res.status_code == 200
    assert res.json() == result

    schema_person["fields"] = [
        {"name": "name", "type": "string"},
        {"name": "age", "type": "long"},
        {"name": "address", "type": "Address"},
        {"name": "job", "type": "Job"},
    ]

    res = await registry_async_client.post(
        "compatibility/subjects/person/versions/latest",
        json={"schemaType": "AVRO", "schema": json.dumps(schema_person), "references": two_references},
    )
    assert res.status_code == 200
    assert res.json() == {"is_compatible": True}

    schema_person["fields"] = [
        {"name": "name", "type": "string"},
        {"name": "age", "type": "string"},
        {"name": "address", "type": "Address"},
        {"name": "job", "type": "Job"},
    ]
    res = await registry_async_client.post(
        "compatibility/subjects/person/versions/latest",
        json={"schemaType": "AVRO", "schema": json.dumps(schema_person), "references": two_references},
    )

    assert res.status_code == 200
    assert res.json() == {"is_compatible": False}

    schema_union = {
        "type": "record",
        "namespace": "com.netapp",
        "name": "Person2",
        "fields": [
            {"name": "name", "type": "string"},
            {"name": "age", "type": "int"},
            {"name": "address", "type": "Address"},
            {"name": "job", "type": "Job"},
            {
                "name": "children",
                "type": [
                    "null",
                    {
                        "type": "record",
                        "name": "child",
                        "fields": [{"name": "name", "type": "string"}, {"name": "age", "type": "int"}],
                    },
                ],
            },
        ],
    }

    res = await registry_async_client.post(
        "subjects/person2/versions",
        json={"schemaType": "AVRO", "schema": json.dumps(schema_union), "references": two_references},
    )
    assert res.status_code == 200
    assert "id" in res.json()
