|Build Status| |Coverage Status| |Pyup Updates| |Py3 Ready|

grift
=====

Classes to define, load, validate, and store values for an application's
configuration.

Installation
~~~~~~~~~~~~

::

    pip install grift

Define Configuration Schema
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a class that inherits from ``BaseConfig`` and add a
``ConfigProperty`` for each setting

.. code:: python

    from grift import BaseConfig, ConfigProperty, DictLoader
    from schematics.types import BooleanType, StringType, IntType

    class AppConfig(BaseConfig):
        # defaults can be specified, and properties can be optional
        DEBUG = ConfigProperty(property_type=BooleanType(), required=False, default=False)

        # attribute name does not need to match the property key
        ELASTICSEARCH_HOST = ConfigProperty(property_key='ES_HOST', property_type=StringType())
        ELASTICSEARCH_SHARDS = ConfigProperty(property_key='ES_SHARDS', property_type=IntType(), default=5)

        # properties can be excluded from varz
        AWS_SECRET_KEY = ConfigProperty(property_type=StringType(), exclude_from_varz=True)

``ConfigProperty``
''''''''''''''''''

``property_key`` is the key used to pull a property value from a loader.
If unspecified, defaults to the name of the attribute on the Config
class (e.g. ``'DEBUG'`` and ``'AWS_SECRET_KEY'`` in the example above).

To skip validation, leave ``property_type`` as the default (``None``).
To define new property type classes, subclass
``schematic.types.BaseType`` (see ``.property_types.DictType`` as an
example).

When ``required`` is True, the value cannot be ``None`` (i.e. the value
must exist in one of the loaders or a ``default`` value should be
specified.) However, if a ``default`` is specified (and not ``None``),
the requirement is always satisfied -- ``required`` is effectively
``False``.

``exclude_from_varz`` indicates whether the property should be left out
of BaseConfig's ``varz`` dict (defaults to ``False``).

Load and Validate Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~

Initialize the custom configuration class with one or more loaders. Each
loader specifies a source for loading configuration settings.

.. code:: python

    config_dict = {
        'DEBUG': 1,
        'ES_HOST': 'http://localhost:9200',
        'ES_SHARDS': '1',
        'AWS_SECRET_KEY': 'whatever'
    }
    loaders = [DictLoader(config_dict)]

    app_config = AppConfig(loaders)

The config can be initialized with multiple loaders. Each
``ConfigProperty``'s value is assigned from the first loader that
contains the ``ConfigProperty.property_key``. For example, with
``ES_SHARDS = '5'`` in the environment:

.. code:: python

    loaders = [EnvLoader(), DictLoader(config_dict)]
    app_config2 = AppConfig(loaders)

    app_config2.ELASTICSEARCH_SHARDS  # 5 (from env)
    app_config2.ELASTICSEARCH_HOST  # u'http://localhost:9200'  (from dict)

When the configuration class is initialized, the sequence for loading a
value is as follows, for each ``ConfigProperty``:

-  If ``property_key`` is not defined, use the name of the attribute on
   the class (e.g. ``DEBUG`` in ``AppConfig``).
-  Check whether the ``property_key`` exists in each of the loaders.
   Iterate through the loaders in the order provided, stopping at the
   first loader where the key exists.
-  If the key exists in one of the loaders:

   -  Pull the value of the ``property_key`` from that loader.
   -  If a ``property_type`` class is defined for the ConfigProperty,
      use ``to_native()`` to convert the loaded value to the appropriate
      type and ``validate()`` to check any other assumptions (e.g. max
      string length, connectivity to a network type, etc). An exception
      may be raised at this stage, if the value cannot be converted or
      validated.
   -  If no ``property_type`` was defined, use the value as is.

-  If the key does not exist in any of the loaders:

   -  If a default value was specified, use it.
   -  If no default value was specified AND the property is required,
      raise an exception.
   -  Otherwise, the value of the property is set to ``None``

| Default loaders are available in ``loaders.DEFAULT_LOADERS``. The
  default is to prefer the ``EnvLoader``, which reads in environment
  variables. If ``$SETTINGS_PATH`` is defined in the env, a second
  loader is
| added to pull in settings from a json file at the specified path.

Property Types
~~~~~~~~~~~~~~

Use ``schematics.types`` classes to convert and validate values at load
time.

A custom property type can be created by extending
``schematics.type.BaseType``. Implement ``.to_native()`` to convert a
value type (returning the converted value or raising an exception for
incompatible types). Define one or more methods with names that start
with ``validate_`` (e.g. ``.validate_length()``) to add validation
steps. Validation methods should raise
``schematics.exceptions.ValidationError`` for failed checks.

Access Property Values
~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    >>> app_config.DEBUG
    True
    >>> app_config.ELASTICSEARCH_HOST
    u'http://localhost:9200'
    >>> app_config.ELASTICSEARCH_SHARDS
    1

| Note that when the class is initialized, attributes that are
  ``ConfigProperty`` instances are set to
| the loaded values:

.. code:: python

    >>> type(AppConfig.ELASTICSEARCH_SHARDS)
    grift.config.ConfigProperty
    >>> type(app_config.ELASTICSEARCH_SHARDS)
    int

Get public configuration settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``varz`` property of ``BaseConfig`` classes is a dict with the
values for each ``ConfigProperty`` attribute. Any ``ConfigProperty`` can
be excluded from ``varz`` by specifying ``exclude_from_varz=True``.

::

    >>> app_config.varz
    {
        'DEBUG': True,
        'ELASTICSEARCH_HOST': 'http://localhost:9200',
        'ES_SHARDS': 1
    }

*All* ``ConfigProperty`` values can be accessed in a dict, using
``.as_dict()``:

::

    >>> app_config.as_dict()
    {'AWS_SECRET_KEY': 'whatever'
     'DEBUG': 1,
     'ES_HOST': 'http://localhost:9200',
     'ES_SHARDS': '1'}

Maximizing Startup Guarantees
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may want to set up your config class to maximize startup guarantees
of having the right configuration set. There are a few property types
that attempt to make a basic connection with whatever network resouce is
specified. The supported protocols are http, postgres, redis, amqp, and
etcd. By default, the validator will back off 5 times before giving up,
but that can be overridden with the 'max\_tries' kwarg.

For example:

.. code:: python

    class AppConfig(BaseConfig):
         DATABASE_URL = ConfigProperty(property_type=PostgresType(), default='postgres://...')
         REDIS_URL = ConfigProperty(property_type=RedisType(max_tries=1))
         SHARED_CONFIG =  ConfigProperty(property_type=StringType(), default='A')


    class DeploymentConfig(AppConfig):
        DATABASE_URL = ConfigProperty(property_type=PostgresType())


    ConfigCls = AppConfig if deploy.env not in [STAGE, PROD] else DeployedConfig
    config = ConfigCls(loaders)

An important distinction in this example is that the config schema
changes based on the deploy env. For the staging and production
environments, ``DeploymentConfig`` will fail to initialize if
``DATABASE_URL`` isn't set.

License
=======

Licensed under the Apache 2.0 License. Unless required by applicable law
or agreed to in writing, software distributed under the License is
distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.

Copyright 2017 Kensho Technologies, LLC.


.. |Build Status| image:: https://travis-ci.org/kensho-technologies/grift.svg?branch=master
   :target: https://travis-ci.org/kensho-technologies/grift
.. |Coverage Status| image:: https://coveralls.io/repos/github/kensho-technologies/grift/badge.svg?branch=master
   :target: https://coveralls.io/github/kensho-technologies/grift?branch=master
.. |Pyup Updates| image:: https://pyup.io/repos/github/kensho-technologies/grift/shield.svg
     :target: https://pyup.io/repos/github/kensho-technologies/grift/
     :alt: Updates
.. |Py3 Ready| image:: https://pyup.io/repos/github/kensho-technologies/grift/python-3-shield.svg
     :target: https://pyup.io/repos/github/kensho-technologies/grift/
     :alt: Python 3
