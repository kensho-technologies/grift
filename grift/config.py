# Copyright 2017 Kensho Technologies, LLC.
import inspect
from schematics.types import BaseType


class ConfigProperty(object):

    def __init__(self, property_key=None, property_type=None, required=True, default=None,
                 exclude_from_varz=False):
        """Define the schema for a property of a BaseConfig subclass

        Args:
            property_key: None | string
                Key of the property to get from a loader. Defaults to name of the attribute name in
                the BaseConfig class.
            property_type: None | schematics BaseType
                If property_type is specified, the loaded value is passed through to_native()
                and validate(). If the value is invalid, an exception is raised.
                If property_type is None (default), conversion and validation steps are skipped.
            required: bool
                True if the Config should require a value for this property. If a default value is
                specified to be anything except None, the requirement is always satisfied (i.e.
                this is effectively False).
            default: default value
            exclude_from_varz: bool
                Determines if the property should be included in the BaseConfig's varz dict. If
                True, the value is not added.
        """
        self.property_key = property_key
        self.property_type = property_type
        self.required = required
        self.default = default
        self.exclude_from_varz = exclude_from_varz

    def load(self, value):
        """Load a value, converting it to the proper type if validation_type exists."""
        if self.property_type is None:
            return value
        elif not isinstance(self.property_type, BaseType):
            raise TypeError('property_type must be schematics BaseType')
        else:
            native_value = self.property_type.to_native(value)
            self.property_type.validate(native_value)
            return native_value


class BaseConfig(object):
    """Base class to hold configuration settings"""

    def __init__(self, loaders):
        """Load values into the class's ConfigProperty attributes (validating types if possible)

        Args:
            loaders: iterable of AbstractLoader instances
                ConfigProperty values are loaded from these sources; and the order indicates
                preference.
        """
        if not loaders:
            # Require loaders only if the class has ConfigProperty attributes
            if any(self._iter_config_props()):
                raise AssertionError('Class has ConfigProperty attributes: must provide loader(s)')

        self._update_property_keys()

        self.varz = {}
        self._loaders = loaders
        self._load()

    @classmethod
    def _iter_config_props(cls):
        """Iterate over all ConfigProperty attributes, yielding (attr_name, config_property) """
        props = inspect.getmembers(cls, lambda a: isinstance(a, ConfigProperty))
        for attr_name, config_prop in props:
            yield attr_name, config_prop

    @classmethod
    def _update_property_keys(cls):
        """Set unspecified property_keys for each ConfigProperty to the name of the class attr"""
        for attr_name, config_prop in cls._iter_config_props():
            if config_prop.property_key is None:
                config_prop.property_key = attr_name

    def _set_instance_prop(self, attr_name, config_prop, value):
        """Set instance property to a value and add it varz if needed"""
        setattr(self, attr_name, value)

        # add to varz if it is not private
        if not config_prop.exclude_from_varz:
            self.varz[attr_name] = value

    def _load(self):
        """Load values for all ConfigProperty attributes"""
        for attr_name, config_prop in self._iter_config_props():
            found = False
            for loader in self._loaders:
                if loader.exists(config_prop.property_key):
                    raw_value = loader.get(config_prop.property_key)
                    converted_value = config_prop.load(raw_value)

                    self._set_instance_prop(attr_name, config_prop, converted_value)
                    found = True
                    break

            if not found:
                if not config_prop.required or config_prop.default is not None:
                    self._set_instance_prop(attr_name, config_prop, config_prop.default)
                else:
                    raise ValueError('Missing required ConfigProperty {}'.format(attr_name))

    def reload(self):
        """Reload all ConfigProperty values (reading from loader sources again, if applicable)"""
        for loader in self._loaders:
            loader.reload()

        self.varz = {}  # reset varz
        self._load()

    def as_dict(self):
        """Return all properties and values in a dictionary (includes private properties)"""
        return {config_name: getattr(self, config_name)
                for config_name, _ in self._iter_config_props()}
