"""NervesHub User API client."""

import base64
import binascii
import importlib.resources
import os
import os.path
from tempfile import NamedTemporaryFile
from typing import Any, List, Optional

import requests
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import load_pem_x509_certificate

from .exceptions import NervesHubAPIError

NERVES_HUB_BASE_URL_DEFAULT = "https://api.nerves-hub.org"


class NervesHubAPI:
    """
    NervesHub API client.

    The canonical implementation is in the Elixir project
    [nerves_hub_user_api](https://github.com/nerves-hub/nerves_hub_user_api).
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        organization: str,
        product: str,
        cert: Any,
        key: Any,
        base_url: Optional[str] = None,
        ca_cert: Optional[bytes] = None,
    ):
        """
        Initialize NervesHubAPI.

        Params
        ------
        organization
            NervesHub organization name
        product
            NervesHub product
        cert
            Client certificate
        key
            Client private key
        base_url
            NervesHub API base url
        ca_cert
            NervesHub API domain Certificate Authority Certificate
        """
        self._organization = organization
        self._product = product
        self._cert, self._cert_paths = self._init_cert(cert, key)
        if base_url is None:
            base_url = NERVES_HUB_BASE_URL_DEFAULT
        self._base_url = base_url
        if ca_cert is None:
            with importlib.resources.path(
                "nerves_hub_client.resources", "nerveshub_ca_certs.pem"
            ) as path:
                with open(path, "rb") as f:
                    ca_cert = f.read()
        self._ca_cert, self._ca_cert_path = self._init_ca_cert(ca_cert)

    @classmethod
    def from_env(cls):
        """
        Create an instance using environment variables for initialization.

        The following environment variables are supported:
        * NERVES_HUB_BASE_URL - optional and defaults to https://api.nerves-hub.org
        * NERVES_HUB_ORG - selects the organization to use, required
        * NERVES_HUB_PRODUCT - selects the product in the organization to user, required
        * NERVES_HUB_CERT - PEM encoded certificate string for API client
        * NERVES_HUB_KEY - PEM encoded private key string for API client
        * NERVES_HUB_CA_CERT - PEM encoded CA Certificates for NERVES_HUB_BASE_URL, optional
        """
        org = os.environ["NERVES_HUB_ORG"]
        product = os.environ["NERVES_HUB_PRODUCT"]
        cert = load_pem_x509_certificate(cls._get_env_b64("NERVES_HUB_CERT"))
        key = serialization.load_pem_private_key(
            cls._get_env_b64("NERVES_HUB_KEY"), None
        )
        base_url = os.environ.get("NERVES_HUB_BASE_URL")
        ca_cert = os.environ.get("NERVES_HUB_CA_CERT")
        return cls(org, product, cert, key, base_url, ca_cert)

    @classmethod
    def _get_env_b64(cls, key):
        val = bytes(os.environ[key], "utf-8")
        try:
            return base64.b64decode(val, validate=True)
        except binascii.Error:
            return val

    @classmethod
    def _init_cert(cls, cert, key):
        """
        Initialize SSL client certificate.

        The certificate and key are stored in temporary files because
        requests doesn't support passing them in directly from memory.
        """
        cert_data = cert.public_bytes(serialization.Encoding.PEM)
        key_data = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        # This implementation of using temporary files is due to a limitation of
        # Python's SSL library handles client side certs and cert checking.
        # It only supports passing in paths, not data.
        # Needs to live for the lifetime of the class
        #  pylint: disable=consider-using-with
        cert_file = NamedTemporaryFile()
        # Needs to live for the lifetime of the class
        #  pylint: disable=consider-using-with
        key_file = NamedTemporaryFile()
        cert_file.write(cert_data)
        cert_file.seek(0)
        key_file.write(key_data)
        key_file.seek(0)
        return ((cert_file, key_file), (cert_file.name, key_file.name))

    @classmethod
    def _init_ca_cert(cls, ca_cert):
        """
        Initialize SSL CA Certificate used to verify the server.

        The CA Certificate is stored in temporary files because
        requests doesn't support passing them in directly from memory.
        """
        #  pylint: disable=consider-using-with
        ca_cert_file = NamedTemporaryFile()
        ca_cert_file.write(ca_cert)
        ca_cert_file.seek(0)
        return (ca_cert_file, ca_cert_file.name)

    def _url(self, path):
        url = self._base_url + path
        return url

    def _common_kwargs(self):
        return dict(cert=self._cert_paths, verify=self._ca_cert_path)

    @staticmethod
    def _raise_for_stats(resp):
        try:
            resp.raise_for_status()
        except requests.HTTPError as http_error:
            raise NervesHubAPIError(str(http_error), resp.status_code) from http_error

    def _get(self, path):
        url = self._url(path)
        resp = requests.get(url, **self._common_kwargs())
        self._raise_for_stats(resp)
        return resp

    def _post(self, path, data):
        url = self._url(path)
        resp = requests.post(url, data, **self._common_kwargs())
        self._raise_for_stats(resp)
        return resp

    def _delete(self, path):
        url = self._url(path)
        resp = requests.delete(url, **self._common_kwargs())
        self._raise_for_stats(resp)
        return resp

    def _device_path(self, identifier=None):
        path = f"/orgs/{self._organization}/products/{self._product}/devices"
        if identifier is not None:
            path += f"/{identifier}"
        return path

    def _device_cert_path(self, identifier):
        path = self._device_path(identifier) + "/certificates"
        return path

    def device_list(self) -> dict:
        """Get a list of devices."""
        path = self._device_path()
        resp = self._get(path)
        return resp.json()

    def device_create(
        self,
        identifier: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> dict:
        """
        Create a new device.

        Params
        ------
        identifier
            Unique identifier for the device
        description
            Text description of the device
        tags
            List of tags
        """
        path = self._device_path()
        if tags is None:
            tag_str = ""
        else:
            tag_str = ",".join(tags)
        data = {
            "identifier": identifier,
            "description": description,
            "tags": tag_str,
        }
        resp = self._post(path, data)
        return resp.json()

    def device_cert_create(self, identifier: str, cert: bytes) -> dict:
        """
        Create a certificate for the specified device.

        Params
        ------
        identifier
            Unique identifier for the device
        cert
            PEM encoded certificate data
        """
        path = self._device_cert_path(identifier)
        data = {"identifier": identifier, "cert": base64.b64encode(cert)}
        resp = self._post(path, data)
        return resp.json()

    def device_cert_list(self, identifier: str) -> dict:
        """
        Get the certificates associated with the specified device.

        Params
        ------
        identifier
            Unique identifier for the device
        """
        path = self._device_cert_path(identifier)
        resp = self._get(path)
        return resp.json()

    def device_delete(self, identifier: str) -> bool:
        """
        Delete the specified device.

        The device will still need to be "destroyed" in the UI before
        the identifier can be used again.

        Params
        ------
        identifier
            Unique identifier for the device
        """
        path = self._device_path(identifier)
        resp = self._delete(path)
        return resp.status_code == 204
