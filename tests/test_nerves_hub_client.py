import base64
import os
from unittest.mock import patch, MagicMock

import pytest
import responses
from cryptography.x509 import Certificate

from nerves_hub_client import NervesHubAPI, NervesHubAPIError


@pytest.fixture
def nh():
    cert = MagicMock(spec=Certificate)
    key = MagicMock()
    with responses.mock, patch("nerves_hub_client.client.NamedTemporaryFile") as _f:
        nh = NervesHubAPI(
            organization="organization", product="product", cert=cert, key=key
        )
        yield nh


def resource_path(path):
    return os.path.join(os.path.dirname(__file__), "resources", path)


def key():
    with open(resource_path("key_decrypted.pem"), "rb") as f:
        return f.read()


def cert():
    with open(resource_path("cert.pem"), "rb") as f:
        return f.read()


def test_device_create(nh):
    resp = {"data": {"identifier": "123"}}
    responses.add(
        responses.POST,
        "https://api.nerves-hub.org/orgs/organization/products/product/devices",
        json=resp,
        status=200,
    )
    assert resp == nh.device_create("test")


def test_device_create_fails_already_exists(nh):
    resp = {"errors": {"identifier": ["has already been taken"]}}
    responses.add(
        responses.POST,
        "https://api.nerves-hub.org/orgs/organization/products/product/devices",
        json=resp,
        status=422,
    )
    with pytest.raises(NervesHubAPIError) as e:
        nh.device_create("test")
        assert e.status_code == 422


def test_device_cert_create(nh):
    resp = {
        "data": {
            "not_after": "2053-02-01T20:00:00Z",
            "not_before": "2022-02-01T19:00:00Z",
            "serial": "239802987793401573645013872129096179462716958206",
        }
    }
    responses.add(
        responses.POST,
        "https://api.nerves-hub.org/orgs/organization/products/product/devices/123/certificates",
        json=resp,
        status=200,
    )
    assert resp == nh.device_cert_create("123", b"my certificate")


@patch.dict(
    os.environ,
    {
        "NERVES_HUB_ORG": "org",
        "NERVES_HUB_PRODUCT": "prod",
        "NERVES_HUB_KEY": key().decode("utf-8"),
        "NERVES_HUB_CERT": cert().decode("utf-8"),
    },
)
def test_from_env():
    NervesHubAPI.from_env()


@patch.dict(
    os.environ,
    {
        "NERVES_HUB_ORG": "org",
        "NERVES_HUB_PRODUCT": "prod",
        "NERVES_HUB_KEY": base64.b64encode(key()).decode("utf-8"),
        "NERVES_HUB_CERT": base64.b64encode(cert()).decode("utf-8"),
    },
)
def test_from_env_with_b64_encoded_key_and_cert():
    NervesHubAPI.from_env()
