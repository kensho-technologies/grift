# Copyright 2017 Kensho Technologies, LLC.
import os
from unittest import TestCase

from schematics.exceptions import ConversionError
from schematics.types import StringType, IntType
import six

from grift.config import BaseConfig, ConfigProperty
from grift.loaders import DictLoader, EnvLoader, JsonFileLoader
from grift.utils import in_same_dir


SAMPLE_FILE_PATH = in_same_dir(__file__, 'sample_config.json')


class SampleConfig(BaseConfig):
    STRING_PROP = ConfigProperty(property_type=StringType(), required=True, exclude_from_varz=True)
    INT_PROP = ConfigProperty(property_type=IntType(), required=True, default=0)
    ONLY_IN_ENV = ConfigProperty(
        property_type=StringType(), required=False, exclude_from_varz=False)
    ANY_TYPE_PROP = ConfigProperty(
        property_key='ANY_TYPE_PROP', required=False, exclude_from_varz=False)
    DIFFERENT_KEY_PROP = ConfigProperty(
        property_key='DifferentKey', required=False, exclude_from_varz=False)


class TestValidatingConfig(TestCase):
    def setUp(self):
        self.env_keys_set = ['STRING_PROP', 'ONLY_IN_ENV', 'NOT_A_PROPERTY']
        # set some env variables
        os.environ['STRING_PROP'] = 'let\'s see if overrides work'
        os.environ['ONLY_IN_ENV'] = 'this is only in the env!'
        os.environ['NOT_A_PROPERTY'] = 'this key is not clear to land'

    def tearDown(self):
        # remove env variables
        for prop in self.env_keys_set:
            del os.environ[prop]

    def test_from_dict(self):
        config_dict = {
            'STRING_PROP': '1',
            'INT_PROP': '2',
            'ANY_TYPE_PROP': [1, 2, 3],
            'NOT_A_PROPERTY': 'boo'
        }

        # construct config from dict
        config = SampleConfig(loaders=[DictLoader(config_dict)])

        self.assertEqual(config.STRING_PROP, '1')
        self.assertEqual(config.INT_PROP, 2)
        self.assertEqual(config.ANY_TYPE_PROP, [1, 2, 3])
        with self.assertRaises(AttributeError):
            config.NOT_A_PROPERTY

    def test_loader_priority(self):
        config_dict = {
            'STRING_PROP': '1',
            'INT_PROP': '2',
            'ANY_TYPE_PROP': [1, 2, 3],
            'NOT_A_PROPERTY': 'boo'
        }

        # construct config with env overrides
        config_with_env = SampleConfig(loaders=[EnvLoader(), DictLoader(config_dict)])

        self.assertEqual(config_with_env.STRING_PROP, 'let\'s see if overrides work')
        self.assertEqual(config_with_env.INT_PROP, 2)
        self.assertEqual(config_with_env.ONLY_IN_ENV, 'this is only in the env!')
        with self.assertRaises(AttributeError):
            config_with_env.NOT_A_PROPERTY

    def test_allow_nones(self):
        # test that intentional None value in first priority loader is not overriden
        config_dict = {
            'STRING_PROP': '1',
            'INT_PROP': 3,
            'ANY_TYPE_PROP': None
        }

        os.environ['ANY_TYPE_PROP'] = 'this should not get through'
        self.env_keys_set.append('ANY_TYPE_PROP')

        config_env_second = SampleConfig(loaders=[DictLoader(config_dict), EnvLoader()])
        self.assertIsNone(config_env_second.ANY_TYPE_PROP)

    def test_from_file(self):
        config = SampleConfig(loaders=[JsonFileLoader(SAMPLE_FILE_PATH)])

        self.assertEqual(config.STRING_PROP, '1')
        self.assertEqual(config.INT_PROP, 2)
        self.assertEqual(config.ANY_TYPE_PROP, [1, 2, 3])
        with self.assertRaises(AttributeError):
            config.NOT_A_PROPERTY

    def test_fail_validation(self):
        config_dict = {'STRING_PROP': '1',
                       'INT_PROP': 'not an int'}
        with self.assertRaises(ConversionError):
            SampleConfig(loaders=[DictLoader(config_dict)])

    def test_missing_required(self):
        # should raise an error if the value is required and no default is provided (STRING_PROP)
        config_dict = {
            'INT_PROP': 2
        }
        with self.assertRaises(ValueError):
            SampleConfig(loaders=[DictLoader(config_dict)])

        # should not raise an error if the value is required and a default is provided (INT_PROP)
        config_dict = {
            'STRING_PROP': 'blah blah'
        }
        config = SampleConfig(loaders=[DictLoader(config_dict)])
        self.assertEqual(config.INT_PROP, 0)
        self.assertEqual(config.STRING_PROP, 'blah blah')

    def test_varz(self):
        config_dict = {
            'STRING_PROP': 'abc',
            'INT_PROP': 2,
            'DifferentKey': ['whatever']
        }
        config = SampleConfig([DictLoader(config_dict)])

        expected_varz = {
            'INT_PROP': 2,
            'DIFFERENT_KEY_PROP': ['whatever'],
            'ONLY_IN_ENV': None,
            'ANY_TYPE_PROP': None
        }
        self.assertDictEqual(config.varz, expected_varz)

    def test_as_dict(self):
        config_dict = {
            'STRING_PROP': '1',
            'INT_PROP': '2',
            'ANY_TYPE_PROP': [1, 2, 3],
        }
        expected_dict = {
            'STRING_PROP': u'1',
            'INT_PROP': 2,
            'ANY_TYPE_PROP': [1, 2, 3],
            'DIFFERENT_KEY_PROP': None,
            'ONLY_IN_ENV': None
        }
        config = SampleConfig(loaders=[DictLoader(config_dict)])
        self.assertDictEqual(expected_dict, config.as_dict())

    def test_reload(self):
        # load initial config
        config = SampleConfig(loaders=[EnvLoader()])
        self.assertEqual(config.STRING_PROP, 'let\'s see if overrides work')

        # set something else in env
        os.environ['STRING_PROP'] = 'new value!'

        config.reload()
        self.assertEqual(config.STRING_PROP, 'new value!')
