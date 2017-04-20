# Copyright 2017 Kensho Technologies, Inc.
from abc import ABCMeta, abstractmethod
import json
import os


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


# Default loaders, for convenience. Prefers the EnvLoader (env vars), with a fallback on a json
# file if $SETTINGS_PATH is defined in the env (a path to a json file)
if 'SETTINGS_PATH' in os.environ:
    DEFAULT_LOADERS = (
        EnvLoader(),
        JsonFileLoader(os.environ['SETTINGS_PATH'])
    )
else:
    DEFAULT_LOADERS = (EnvLoader(),)
