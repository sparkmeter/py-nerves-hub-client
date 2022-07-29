import base64
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
import responses
from cryptography.x509 import Certificate

from nerves_hub_client import NervesHubAPI, NervesHubAPIError


@pytest.fixture
def nh():
    ca_cert = MagicMock(spec=Certificate)
    with responses.mock, patch("nerves_hub_client.client.NamedTemporaryFile") as _f:
        nh = NervesHubAPI(
            organization="organization",
            product="product",
            token="token",
            ca_cert=ca_cert,
        )
        yield nh


def resource_path(path):
    return os.path.join(os.path.dirname(__file__), "resources", path)


def ca_cert():
    with open(resource_path("ca_certs.pem"), "rb") as f:
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
        "NERVES_HUB_TOKEN": "token",
    },
)
def test_from_env():
    nh = NervesHubAPI.from_env()
    tempdir = tempfile.gettempdir()

    assert nh._base_url == "https://api.nerves-hub.org"
    assert nh._organization == "org"
    assert nh._product == "prod"
    assert nh._token == "token"

    # Not direcly used, but good to confirm it was written to disk correctly
    assert nh._ca_cert.read() == ca_cert()

    # Ensure the ca_cert_path is in the temp dir
    assert nh._ca_cert_path.startswith(tempdir)


@patch.dict(
    os.environ,
    {
        "NERVES_HUB_BASE_URL": "https://api.example.org",
        "NERVES_HUB_ORG": "org",
        "NERVES_HUB_PRODUCT": "prod",
        "NERVES_HUB_TOKEN": "token",
        "NERVES_HUB_CA_CERT": ca_cert().decode("utf-8"),
    },
)
def test_from_env_self_hosted():
    nh = NervesHubAPI.from_env()
    tempdir = tempfile.gettempdir()

    assert nh._base_url == "https://api.example.org"
    assert nh._organization == "org"
    assert nh._product == "prod"
    assert nh._token == "token"

    # Not direcly used, but good to confirm it was written to disk correctly
    assert nh._ca_cert.read() == ca_cert()

    # Ensure the ca_cert_path is in the temp dir
    assert nh._ca_cert_path.startswith(tempdir)


@patch.dict(
    os.environ,
    {
        "NERVES_HUB_BASE_URL": "https://api.example.org",
        "NERVES_HUB_ORG": "org",
        "NERVES_HUB_PRODUCT": "prod",
        "NERVES_HUB_TOKEN": "token",
    },
)
def test_from_env_self_hosted_no_ca_cert():
    with pytest.raises(Exception) as e:
        NervesHubAPI.from_env()
        assert (
            e.message == "NERVES_HUB_CA_CERT is required for self-hosted installations."
        )
