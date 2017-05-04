import mock
import os
from unittest import TestCase

from grift.loaders import JsonFileLoader, EnvLoader, DictLoader, VaultLoader, VaultException
from grift.utils import in_same_dir

SAMPLE_FILE_PATH = in_same_dir(__file__, 'sample_config.json')


class TestBasicLoaders(TestCase):

    def test_dict_loader(self):
        config_dict = {
            'KEY': 'value',
            'foo': 'bar'
        }

        loader = DictLoader(config_dict)
        self.assertTrue(loader.exists('KEY'))
        self.assertTrue('KEY' in loader)
        self.assertTrue(loader.exists('foo'))
        self.assertTrue('foo' in loader)
        self.assertFalse(loader.exists('bar'))
        self.assertFalse('bar' in loader)

        self.assertEqual(loader.get('KEY'), 'value')
        self.assertEqual(loader.get('foo'), 'bar')

    def test_env_loader(self):
        os.environ['EXISTING_KEY'] = 'hello'

        loader = EnvLoader()

        # change the env after loader is initialized
        os.environ['EXISTING_KEY'] = 'world'
        os.environ['NEW_KEY'] = 'brand_new'

        self.assertTrue(loader.exists('EXISTING_KEY'))
        self.assertTrue(loader.exists('NEW_KEY'))
        self.assertFalse(loader.exists('BAD_KEY'))

        self.assertEqual(loader.get('EXISTING_KEY'), 'world')
        self.assertEqual(loader.get('NEW_KEY'), 'brand_new')

    def test_json_file_loader(self):
        loader = JsonFileLoader(SAMPLE_FILE_PATH)
        self.assertTrue(loader.exists('STRING_PROP'))
        self.assertTrue(loader.exists('INT_PROP'))
        self.assertFalse(loader.exists('BAD_PROPERTY_NAME'))

        self.assertEqual(loader.get('STRING_PROP'), '1')
        self.assertEqual(loader.get('INT_PROP'), '2')  # unconverted type
        self.assertEqual(loader.get('ANY_TYPE_PROP'), [1, 2, 3])


def _mock_response(json_resp):
    """Return a mock class that returns json_resp when .json() is called (for requests.get)"""
    mock_resp = mock.MagicMock()
    mock_resp.json = mock.MagicMock(return_value=json_resp)
    return mock_resp


class TestVaultLoader(TestCase):
    """Testing logic of accessing Vault via http requests; heavily mocked"""

    def setUp(self):
        self.url = 'https://fake_vault.url'
        self.path = 'fake/vault/path'
        self.token = 'fake_token'

        self.expected_header = {'X-Vault-Token': self.token}

    def test_token_constructor(self):
        secrets = {
            'hello': 'world',
            'foo': 'bar'
        }

        expected_url = '{}/v1/{}'.format(self.url, self.path)

        with mock.patch('requests.get', return_value=_mock_response({'data': secrets})) as mock_get:
            loader = VaultLoader.from_token(self.url, self.path, self.token)

            mock_get.assert_called_once_with(expected_url, headers=self.expected_header)

            self.assertTrue(loader.exists('hello'))
            self.assertTrue(loader.exists('foo'))
            self.assertFalse(loader.exists('bad-key'))

            self.assertEqual(loader.get('hello'), 'world')
            self.assertEqual(loader.get('foo'), 'bar')

    def test_lookup_token(self):
        expected_url = '{}/v1/auth/token/lookup-self'.format(self.url)

        with mock.patch('requests.get', return_value=_mock_response({'data': {}})):
            loader = VaultLoader.from_token(self.url, self.path, self.token)

        with mock.patch('requests.get', return_value=_mock_response({'foo': 'bar'})) as mock_get:
            resp = loader.lookup_token()
            mock_get.assert_called_once_with(expected_url, headers=self.expected_header)

            self.assertDictEqual(resp, {'foo': 'bar'})

    def test_lookup_token_fail(self):
        expected_url = '{}/v1/auth/token/lookup-self'.format(self.url)

        with mock.patch('requests.get', return_value=_mock_response({'data': {}})):
            loader = VaultLoader.from_token(self.url, self.path, self.token)

        with mock.patch('requests.get', return_value=_mock_response({'errors': 'foo'})) as mock_get:
            with self.assertRaises(VaultException):
                loader.lookup_token()

            mock_get.assert_called_once_with(expected_url, headers=self.expected_header)

    def test_renew_token(self):
        expected_url = '{}/v1/auth/token/renew-self'.format(self.url)

        with mock.patch('requests.get', return_value=_mock_response({'data': {}})):
            loader = VaultLoader.from_token(self.url, self.path, self.token)

        with mock.patch('requests.get', return_value=_mock_response({'foo': 'bar'})) as mock_get:
            loader.renew_token()
            mock_get.assert_called_once_with(expected_url, headers=self.expected_header)

    def test_renew_token_fail(self):
        expected_url = '{}/v1/auth/token/renew-self'.format(self.url)

        with mock.patch('requests.get', return_value=_mock_response({'data': {}})):
            loader = VaultLoader.from_token(self.url, self.path, self.token)

        with mock.patch('requests.get', return_value=_mock_response({'errors': 'foo'})) as mock_get:
            with self.assertRaises(VaultException):
                loader.renew_token()

            mock_get.assert_called_once_with(expected_url, headers=self.expected_header)
