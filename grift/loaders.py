# Copyright 2017 Kensho Technologies, Inc.
from abc import ABCMeta, abstractmethod
import json
import os

import requests


class AbstractLoader(object):
    """Base class for loading configuration settings from a source"""
    __metaclass__ = ABCMeta

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


class VaultTokenLoader(DictLoader):
    def __init__(self, url, path, token):
        """Load secrets from a Vault path, using token authentication

        See https://www.vaultproject.io/docs

        Args:
            url: Vault url
            path: Vault path to fetch secrets from
            vault_token: token (must have access to vault path)
        """
        self._vault_url = url
        self._path = path
        self._token = token
        source_dict = self._fetch_secrets()
        super(VaultTokenLoader, self).__init__(source_dict)

    @property
    def _headers(self):
        """Return token header to access vault"""
        return {'X-Vault-Token': self._token}

    def _fetch_secrets(self):
        """Read data from the vault path"""
        url = '{}/v1/{}'.format(self._vault_url, self._path)
        resp = requests.get(url, headers=self._headers)
        resp.raise_for_status()
        data = resp.json()
        return data['data']

    def reload(self):
        """Reread secrets from the vault path"""
        self._source = self._fetch_secrets()

    def lookup_token(self):
        """Convenience method: look up the vault token"""
        url = '{}/v1/auth/token/lookup-self'.format(self._vault_url)
        resp = requests.get(url, headers=self._headers)
        resp.raise_for_status()
        data = resp.json()
        if data.get('errors'):
            raise ValueError(u'Error looking up vault token: {}'.format(data['errors']))
        return data

    def renew_token(self):
        """Convenience method: renew vault token"""
        url = '{}/v1/auth/token/renew-self'.format(self._vault_url)
        resp = requests.get(url, headers=self._headers)
        resp.raise_for_status()
        data = resp.json()
        if data.get('errors'):
            raise ValueError(u'Error renewing vault token: {}'.format(data['errors']))
        return data


class VaultAppRoleLoader(VaultTokenLoader):
    def __init__(self, url, path, role_id, secret_id):
        """Load secrets from a Vault path, using the AppRole auth backend

        See https://www.vaultproject.io/docs/auth/approle.html

        Args:
            url: Vault url
            path: Vault path to fetch secrets from
            role_id: Vault RoleID
            secret_id: Vault SecretID
        """
        self._role_id = role_id
        self._secret_id = secret_id
        token = self._fetch_token()
        super(VaultAppRoleLoader, self).__init__(url, path, token=token)

    def _fetch_token(self):
        """Get a Vault token, using the RoleID and SecretID"""
        url = '{}/v1/auth/approle/login'.format(self._vault_url)
        resp = requests.post(url, data={'role_id': self._role_id, 'secret_id': self._secret_id})
        resp.raise_for_status()
        data = resp.json()
        return data['auth']['client_token']


# Default loaders, for convenience. Prefers the EnvLoader (env vars), with a fallback on a json
# file if $SETTINGS_PATH is defined in the env (a path to a json file)
if 'SETTINGS_PATH' in os.environ:
    DEFAULT_LOADERS = (
        EnvLoader(),
        JsonFileLoader(os.environ['SETTINGS_PATH'])
    )
else:
    DEFAULT_LOADERS = (EnvLoader(),)
