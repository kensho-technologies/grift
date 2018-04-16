# Copyright 2017 Kensho Technologies, LLC.
from contextlib import closing, contextmanager
import json
import six
import time

from schematics.exceptions import ConversionError, ValidationError
from schematics.types import BaseType, StringType


class DictType(BaseType):
    """A validation type for dict properties"""

    def to_native(self, value):
        """Return the value as a dict, raising error if conversion to dict is not possible"""
        if isinstance(value, dict):
            return value
        elif isinstance(value, six.string_types):
            native_value = json.loads(value)
            if isinstance(native_value, dict):
                return native_value
            else:
                raise ConversionError(u'Cannot load value as a dict: {}'.format(value))


class ListType(BaseType):
    """A validation type for list properties"""

    def __init__(self, member_type=None, string_delim='|', min_length=None, max_length=None,
                 *args, **kwargs):
        """Optionally specify constraints for the list

        Args:
            member_type: a BaseType to load/validate members of the value list. If None, the list
                members are kept as is (loading and validation are skipped).
            string_delim: a delimiter to load a string as a list. Note: whitespace is not stripped,
                and consecutive delimiters are respected (e.g. 'a ||b' is loaded as ['a ', '', 'b'])
            min_length: specify a minimum length for the list (validated)
            max_length: specify a maximum length for the list (validated)
        """
        super(ListType, self).__init__(*args, **kwargs)
        self.member_type = member_type
        self.string_delim = string_delim
        self.min_length = min_length
        self.max_length = max_length

    def to_native(self, value):
        """Load a value as a list, converting items if necessary"""
        if isinstance(value, six.string_types):
            value_list = value.split(self.string_delim)
        else:
            value_list = value

        to_native = self.member_type.to_native if self.member_type is not None else lambda x: x
        return [to_native(item) for item in value_list]

    def validate_member_type(self, value):
        """Validate each member of the list, if member_type exists"""
        if self.member_type:
            for item in value:
                self.member_type.validate(item)

    def validate_length(self, value):
        """Validate the length of value, if min_length or max_length was specified"""
        list_len = len(value) if value else 0

        if self.max_length is not None and list_len > self.max_length:
            raise ValidationError(
                u'List has {} values; max length is {}'.format(list_len, self.max_length))

        if self.min_length is not None and list_len < self.min_length:
            raise ValidationError(
                u'List has {} values; min length is {}'.format(list_len, self.min_length))


class NetworkType(StringType):

    def __init__(self, max_tries=5, max_wait=10, *args, **kwargs):
        """Validation type for external resources

        Attempts to connect to the resource, backing off on failure.

        Args:
            max_tries: Max number of times to attempt a connection before failing
            max_wait: Max number of seconds to wait between connection attempts. This can be
               used to cap the exponential backoff.
        """
        self._max_tries = max_tries
        if self._max_tries < 1:
            raise TypeError('max_tries must be a positive integer')
        self._max_wait = max_wait
        if self._max_wait < 1:
            raise TypeError('max_wait must be >= 1')
        super(NetworkType, self).__init__(*args, **kwargs)

    @staticmethod
    def _test_connection(url):
        """Attempt to connect to resource. Raise ValidationError on failure"""
        raise NotImplementedError

    def validate_resource(self, value):
        """Validate the network resource with exponential backoff"""

        def do_backoff(*args, **kwargs):
            """Call self._test_connection with exponential backoff, for self._max_tries attempts"""
            attempts = 0
            while True:
                try:
                    self._test_connection(*args, **kwargs)
                    break
                except ValidationError:
                    wait_secs = min(self._max_wait, 2 ** attempts)
                    attempts += 1
                    if attempts < self._max_tries:
                        time.sleep(wait_secs)
                    else:
                        raise

        do_backoff(value)


class HTTPType(NetworkType):
    """Validation type for an HTTP resource"""

    @staticmethod
    def _test_connection(url):
        """Attempt to connect to http

        Args:
            url: string in the form "http://[host]"
        """
        import requests
        try:
            # Don't care about status code here as long as the connection was successful
            requests.head(url)
        except requests.exceptions.ConnectionError as e:
            raise ValidationError(e)


@contextmanager
def _disconnecting(obj):
    """Context manager to call .disconnect() on an object after use"""
    try:
        yield obj
    finally:
        obj.connection_pool.disconnect()


class RedisType(NetworkType):
    """Validation type for a redis resource"""

    @staticmethod
    def _test_connection(url):
        """Attempt to connect to redis

        Args:
            url: string in the form "redis://[:password@]host[:port][/db-number][?option=value]"
        """
        import redis
        try:
            with _disconnecting(redis.StrictRedis.from_url(url)) as conn:
                conn.ping()
        except redis.connection.ConnectionError as e:
            raise ValidationError(e)


class PostgresType(NetworkType):
    """Validation type for a Postgres resource"""

    @staticmethod
    def _test_connection(url):
        """Attempt to connect to postgres

        Args:
            url: string in the form "postgres://[user]:[password]@[host][:port][/database]"
        """
        import psycopg2
        try:
            with closing(psycopg2.connect(dsn=url)) as conn:
                conn.cursor()
        except psycopg2.OperationalError as e:
            raise ValidationError(e)


class AMQPType(NetworkType):
    """Validation type for an AMQP resource"""

    @staticmethod
    def _test_connection(url):
        """Attempt to connect to amqp

        Args:
            url: string in the form "amqp://[user]:[password]@[host]"
        """
        import pika
        try:
            with closing(pika.BlockingConnection(pika.URLParameters(url))) as conn:
                conn.channel()
        except pika.exceptions.ConnectionClosed as e:
            raise ValidationError(e)


class ETCDType(NetworkType):
    """Validation type for an ETCD resource"""

    @staticmethod
    def _test_connection(url):
        """Attempt to connect to etcd

        Args:
            url: string in the form "[host]:[port]"
        """
        import etcd
        host, port = url.split(':')
        try:
            etcd.Client(host=host, port=int(port)).get('/')
        except etcd.EtcdConnectionFailed as e:
            raise ValidationError(e)
