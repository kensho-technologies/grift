# Copyright 2017 Kensho Technologies, LLC.
from abc import ABCMeta, abstractmethod
import json
import os

import requests
import six


@six.add_metaclass(ABCMeta)
class AbstractLoader(object):
    """Base class for loading configuration settings from a source"""

    def reload(self):
        """Reload values from the designated source, if possible"""

    @abstractmethod
    def get(self, property_key):
        """Return the value for a key."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, property_key):
        """Return True if the property_key exists in the loader's source"""
        raise NotImplementedError

    def __contains__(self, item):
        """Return True if item is a property key in the loader's source"""
        return self.exists(item)


class DictLoader(AbstractLoader):
    def __init__(self, source_dict):
        """Load config settings from a dict"""
        self._source = source_dict

    def get(self, property_key):
        """Get a key from the source dict"""
        return self._source[property_key]

    def exists(self, property_key):
        """Return True if property_key is a key in the source dict"""
        return property_key in self._source


class JsonFileLoader(DictLoader):
    def __init__(self, file_path):
        """Load config settings from a JSON file"""
        self._file_path = file_path
        source_dict = self._read_file()
        super(JsonFileLoader, self).__init__(source_dict)

    def _read_file(self):
        """Read in file from file path"""
        with open(self._file_path) as f:
            return json.load(f)

    def reload(self):
        """Read in values from the file at self.file_path"""
        self._source = self._read_file()


class EnvLoader(DictLoader):
    def __init__(self):
        """Load config settings from the environment"""
        super(EnvLoader, self).__init__(os.environ)

    def reload(self):
        """Read in values from the env"""
        self._source = os.environ


class VaultException(Exception):
    """Custom exception raised if Vault response contains error message"""


def _url_joiner(*args):
    """Helper: construct an url by joining sections with /"""
    return '/'.join(s.strip('/') for s in args)


class VaultLoader(DictLoader):
    """Load secrets from a vault path"""

    def __init__(self, source_dict, url, path, token):
        """Initializer.

        Args:
            source_dict: used to initialize the class. Use constructors to read from Vault.
            url: Vault url
            path: Vault path where secrets are stored
            vault_token: token (must have access to vault path)
        """
        self._vault_url = url
        self._path = path
        self._token = token
        super(VaultLoader, self).__init__(source_dict)

    @classmethod
    def from_token(cls, url, path, token):
        """Constructor: use token authentication to read secrets from a Vault path

        See https://www.vaultproject.io/docs/auth/token.html

        Args:
            url: Vault url
            path: Vault path where secrets are stored
            vault_token: token (must have access to vault path)
        """
        source_dict = cls._fetch_secrets(url, path, token)
        return cls(source_dict, url, path, token)

    @classmethod
    def from_app_role(cls, url, path, role_id, secret_id):
        """Constructor: use AppRole authentication to read secrets from a Vault path

        See https://www.vaultproject.io/docs/auth/approle.html

        Args:
            url: Vault url
            path: Vault path where secrets are stored
            role_id: Vault RoleID
            secret_id: Vault SecretID
        """
        token = cls._fetch_app_role_token(url, role_id, secret_id)
        source_dict = cls._fetch_secrets(url, path, token)
        return cls(source_dict, url, path, token)

    @staticmethod
    def _get_headers(token):
        """Return token header to access vault"""
        return {'X-Vault-Token': token}

    @property
    def _headers(self):
        """Return token header to access vault"""
        return self._get_headers(self._token)

    @staticmethod
    def _fetch_secrets(vault_url, path, token):
        """Read data from the vault path"""
        url = _url_joiner(vault_url, 'v1', path)
        resp = requests.get(url, headers=VaultLoader._get_headers(token))
        resp.raise_for_status()
        data = resp.json()
        if data.get('errors'):
            raise VaultException(u'Error fetching Vault secrets from path {}: {}'
                                 .format(path, data['errors']))
        return data['data']

    @staticmethod
    def _fetch_app_role_token(vault_url, role_id, secret_id):
        """Get a Vault token, using the RoleID and SecretID"""
        url = _url_joiner(vault_url, 'v1/auth/approle/login')
        resp = requests.post(url, data={'role_id': role_id, 'secret_id': secret_id})
        resp.raise_for_status()
        data = resp.json()
        if data.get('errors'):
            raise VaultException(u'Error fetching Vault token: {}'.format(data['errors']))
        return data['auth']['client_token']

    def reload(self):
        """Reread secrets from the vault path"""
        self._source = self._fetch_secrets(self._vault_url, self._path, self._token)

    def lookup_token(self):
        """Convenience method: look up the vault token"""
        url = _url_joiner(self._vault_url, 'v1/auth/token/lookup-self')
        resp = requests.get(url, headers=self._headers)
        resp.raise_for_status()
        data = resp.json()
        if data.get('errors'):
            raise VaultException(u'Error looking up Vault token: {}'.format(data['errors']))
        return data

    def renew_token(self):
        """Convenience method: renew Vault token"""
        url = _url_joiner(self._vault_url, 'v1/auth/token/renew-self')
        resp = requests.get(url, headers=self._headers)
        resp.raise_for_status()
        data = resp.json()
        if data.get('errors'):
            raise VaultException(u'Error renewing Vault token: {}'.format(data['errors']))
        return data


# Default loaders, for convenience. Prefers the EnvLoader (env vars), with a fallback on a json
# file if $SETTINGS_PATH is defined in the env (a path to a json file)
if 'SETTINGS_PATH' in os.environ:
    DEFAULT_LOADERS = (
        EnvLoader(),
        JsonFileLoader(os.environ['SETTINGS_PATH'])
    )
else:
    DEFAULT_LOADERS = (EnvLoader(),)
