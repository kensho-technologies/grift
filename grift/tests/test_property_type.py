# Copyright 2017 Kensho Technologies, LLC.
import unittest

from schematics.exceptions import ConversionError, ValidationError
from schematics.types import StringType, IntType

from grift.property_types import DictType, ListType, HTTPType


class TestDictType(unittest.TestCase):
    def test_dict(self):
        d = {'a': 1, 'b': ['one', 'two']}
        self.assertDictEqual(d, DictType().to_native(d))

    def test_string_dict(self):
        d = '{"a": 1, "b": ["one", "two"]}'
        self.assertDictEqual({'a': 1, 'b': ['one', 'two']}, DictType().to_native(d))

    def test_string_list(self):
        # even if you can json.loads a string, may not be a dict
        with self.assertRaises(ConversionError):
            DictType().to_native('[1, 2, 3]')


class TestListType(unittest.TestCase):

    def test_untyped(self):
        untyped_list = ListType(member_type=None)

        native = untyped_list.to_native([1, 'a', None])
        self.assertEqual(native, [1, 'a', None])

        native = untyped_list.to_native('1|a|')
        self.assertEqual(native, ['1', 'a', ''])

        native = untyped_list.to_native(['a', [1, 2]])
        self.assertEqual(native, ['a', [1, 2]])

    def test_delim(self):
        untyped_list = ListType(member_type=None, string_delim='#')

        # test specifying another delimiter
        native = untyped_list.to_native('a#b#c')
        self.assertEqual(native, ['a', 'b', 'c'])

        # test consecutive delimiters/whitespace padding
        native = untyped_list.to_native(' a## b #c ')
        self.assertEqual(native, [' a', '', ' b ', 'c '])

    def test_typed(self):
        typed_list = ListType(member_type=StringType())

        # check good conversion
        native = typed_list.to_native([1, 'a'])
        self.assertEqual(native, ['1', 'a'])

        native = typed_list.to_native('1|a')
        self.assertEqual(native, ['1', 'a'])

        # test conversion failure
        with self.assertRaises(ConversionError):
            typed_list.to_native(['a', [1, 2]])

    def test_nested(self):
        inner_list = ListType(StringType(), string_delim='#')
        nested_list = ListType(member_type=inner_list, string_delim='|')

        # test conversion of inner list
        native = nested_list.to_native([[1, 2], [3, 4, 5], ['abc']])
        self.assertEqual(native, [['1', '2'], ['3', '4', '5'], ['abc']])

        native = nested_list.to_native('1#2|3#4#5|abc')
        self.assertEqual(native, [['1', '2'], ['3', '4', '5'], ['abc']])

        with self.assertRaises(ConversionError):
            nested_list.to_native([['a', 'b'], [{'a': 1}]])

    def test_validate_length(self):
        list_type = ListType(min_length=2, max_length=4)

        # test edges
        list_type.validate([1, 2])
        list_type.validate([1, 2, 3, 4])

        with self.assertRaises(ValidationError):
            list_type.validate([1])

        with self.assertRaises(ValidationError):
            list_type.validate([1, 2, 3, 4, 5])

        with self.assertRaises(ValidationError):
            list_type.validate(None)

    def test_validate_member_type(self):
        list_type = ListType(member_type=IntType(choices=[1, 2]))

        list_type.validate([1, 2])

        with self.assertRaises(ConversionError):
            list_type.validate(['a', 'b'])

        with self.assertRaises(ValidationError):
            list_type.validate([1, 3])


class TestHTTPType(unittest.TestCase):

    def test_http(self):
        network_type = HTTPType(max_tries=2)
        network_type.validate('http://google.com')

        with self.assertRaises(ValidationError):
            network_type.validate('http://bad_http_url')
