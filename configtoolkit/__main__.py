from dataclasses import dataclass
from typing import Any, Callable
import json
import sys
import os
import yaml
import importlib
import toml

DEFAULT_PYTHON_CONFIG_MODULE = "local_config"
DEFAULT_JSON_CONFIG_FILE = "local_config.json"
DEFAULT_YAML_CONFIG_FILE = "local_config.yaml"
DEFAULT_TOML_CONFIG_FILE = "local_config.toml"


@dataclass
class ConfigValue:
    """
    Container for values coming from config providers

    Attributes
    ----------
    value : Any
        value from config provider
    exist : bool
        flag indicating the presence of this value in the config

    Methods
    -------
    apply_to_value(self, function: Callable, ignore_exceptions: bool = False)
        Applies a function to a stored value
    """
    value: Any  # value from config provider
    exist: bool  # flag indicating the presence of this value in the config

    def apply_to_value(self, function: Callable, ignore_exceptions: bool = False):
        """
        Applies a function to a stored value

        do not work if self.exist is False

        Parameters
        ----------
        function : Callable
            function to apply to value
        ignore_exceptions: bool = False
            flag; toggles ignoring errors
        """
        if self.exist:
            try:
                self.value = function(self.value)
            except Exception as e:
                if not ignore_exceptions:
                    raise e
                else:
                    pass
        return self


class ImpossibleToGetValue(Exception):
    """
    Exception throws in get_config_value function if there are no valid values
    """


def not_none_config_value(value):
    """
    Convert incoming value to ConfigValue
    Turns ConfigValue.exist to False if incoming value is None

    Parameters
    ----------
    value : Any
    """
    if value is None:
        return ConfigValue(None, False)
    return ConfigValue(value, True)


def get_config_value(values: list, value_type: type = None, validator: Callable = lambda value: True, **kwargs):
    """
    Select first valid value from list of incoming values

    Can validate value using type checking and/or custom validator function
    Can accept ConfigValue type values
        In this case, the value is considered valid only if value.exist is True
    Or can accept any other values type
        In this case, to accept the value as valid, it is enough to match the value_type and pass the validator

    Parameters
    ----------
    values : list
        list of values to select
    value_type : type = None
        the type to which the value must match
        value is not checking if the value_type is None
    validator : Callable = lambda value: True
        the function to which every value is passed to be checked
    default : Any (option)
        add to the end of values

    Raises
    ------
    ImpossibleToGetValue
        If there are no valid values
    """
    if "default" in kwargs:
        values.append(kwargs["default"])
    for value in values:
        if isinstance(value, ConfigValue):
            if not value.exist:
                continue
            value = value.value
        if value_type is not None:
            if type(value) != value_type:
                continue
        if not validator(value):
            continue
        return value
    raise ImpossibleToGetValue("no matching values")


class ArgsConfigProvider:
    """
    Class to getting config from command line arguments

    Attributes
    ----------
    args : list
        list of string args

    Methods
    -------
    get_value_for_key(key: str) -> ConfigValue
        Return ConfigValue(value, True) if there is a value related to the key in args
        or ConfigValue(None, False) else
    if_key_contains(key: str) -> ConfigValue
        Return ConfigValue(True, True) if there is a key in args
        or ConfigValue(None, False) else
    if_not_key_contains(key: str) -> ConfigValue
        Return ConfigValue(False, True) if there is not a key in args
        or ConfigValue(None, False) else
    is_key_contains(key: str) -> ConfigValue:
        Return ConfigValue(True, True) if there is a key in args
        or ConfigValue(False, True) else
    """

    def __init__(self, args: list):
        """
        Parameters
        ----------
        args : list
            list of string args
        """
        self.args = args

    def get_value_for_key(self, key: str) -> ConfigValue:
        """
        Return ConfigValue(value, True) if there is a value related to the key in args
        or ConfigValue(None, False) else

        Parameters
        ----------
        key : str
            list of string args
        """
        for i in range(len(self.args)):
            arg = self.args[i]
            if arg == key:
                if i < len(self.args) - 1:
                    return ConfigValue(self.args[i + 1], True)
                break
        return ConfigValue(None, False)

    def if_key_contains(self, key: str) -> ConfigValue:
        """
        Return ConfigValue(True, True) if there is a key in args
        or ConfigValue(None, False) else

        Parameters
        ----------
        key : str
            list of string args
        """
        for i in range(len(self.args)):
            arg = self.args[i]
            if arg == key:
                return ConfigValue(True, True)
        return ConfigValue(None, False)

    def if_not_key_contains(self, key: str) -> ConfigValue:
        """
        Return ConfigValue(False, True) if there is not a key in args
        or ConfigValue(None, False) else

        Parameters
        ----------
        key : str
            list of string args
        """
        for i in range(len(self.args)):
            arg = self.args[i]
            if arg == key:
                return ConfigValue(None, False)
        return ConfigValue(False, True)

    def is_key_contains(self, key: str) -> ConfigValue:
        """
        Return ConfigValue(True, True) if there is a key in args
        or ConfigValue(False, True) else

        Parameters
        ----------
        key : str
            list of string args
        """
        for i in range(len(self.args)):
            arg = self.args[i]
            if arg == key:
                return ConfigValue(True, True)
        return ConfigValue(False, True)


class SysArgsConfigProvider(ArgsConfigProvider):
    """
    Class to getting config from system arguments

    automatically gets the arguments passed to the script
    """

    def __init__(self):
        super(SysArgsConfigProvider, self).__init__(sys.argv)


class DictConfigProvider:
    """
    Class to getting config from dictionary

    Retrieves data by key from a dictionary
    Can work with nested dictionaries and arrays

    Methods
    -------
    get(*keys) -> ConfigValue
        get value from data dict by key
        or nested dictionaries or arrays by keys
        typical use: get("key1", "key2", "key3" ... "keyN" )
    """

    def __init__(self, data: dict):
        """
        Parameters
        ----------
        data : dict
            incoming dictionary
        """
        self.data = data

    def get(self, *keys) -> ConfigValue:
        """
        get value from data structure by key
        or from nested dictionaries or arrays by keys

        typical use: get("key1", "key2", "key3" ... "keyN" )

        Parameters
        ----------
        *keys : Any
            some keys

        Returns
        -------
        ConfigValue
            ConfigValue(value, True) where value is founded by keys value
            or ConfigValue(None, False) if nothing is founded
        """
        try:
            value = self.data
            for arg in keys:
                value = value[arg]
            return ConfigValue(value, True)
        except:
            return ConfigValue(None, False)


class EnvironConfigProvider(DictConfigProvider):
    """
    Class to getting config from os environment

    Retrieves data by key from a os environment
    Can work with nested dictionaries and arrays

    Methods
    -------
    get(*keys) -> ConfigValue
        get value from os environment by key
        or from nested dictionaries or arrays by keys
        typical use: get("key1", "key2", "key3" ... "keyN" )
    """

    def __init__(self):
        super().__init__(dict(os.environ))


class PyObjectConfigProvider(DictConfigProvider):
    """
    Class to getting config from python object fields

    Can work with nested dictionaries, arrays and other objects

    Methods
    -------
    get(*keys) -> ConfigValue
        get value from object
        or from nested dictionaries, arrays or objects by keys
        typical use: get("key1", "key2", "key3" ... "keyN" )
    """

    def __init__(self, pyobject):
        """
        Parameters
        ----------
        pyobject : any
            incoming python object
        """
        super().__init__({})
        self.pyobject = pyobject

    def get(self, *args) -> ConfigValue:
        """
        get value from data structure by key
        or from nested dictionaries or arrays by keys

        typical use: get("key1", "key2", "key3" ... "keyN" )

        Parameters
        ----------
        *keys : Any
            some keys

        Returns
        -------
        ConfigValue
            ConfigValue(value, True) where value is founded by keys value
            or ConfigValue(None, False) if nothing is founded
        """
        try:
            value = self.pyobject
            for arg in args:
                if hasattr(value, '__getitem__'):
                    if arg in value:
                        value = value[arg]
                        continue
                value = getattr(value, arg)
            return ConfigValue(value, True)
        except:
            return ConfigValue(None, False)


class PyModuleConfigProvider(PyObjectConfigProvider):
    """
    Class to getting config from python module content

    Can work with nested dictionaries, arrays and other objects

    Methods
    -------
    get(*keys) -> ConfigValue
        get value from module
        or from nested dictionaries, arrays or objects by keys
        typical use: get("key1", "key2", "key3" ... "keyN" )
    """

    def __init__(self, module_name: str = DEFAULT_PYTHON_CONFIG_MODULE, ignore_import_errors: bool = False):
        """
        Parameters
        ----------
        module_name : str = DEFAULT_PYTHON_CONFIG_MODULE
            name of python module to import
        ignore_import_errors: bool = False
            flag to ignoring errors while importing
        """
        try:
            module = importlib.import_module(module_name)
            super(PyModuleConfigProvider, self).__init__(module)
        except ModuleNotFoundError as me:
            if not ignore_import_errors:
                raise me


class JSONConfigProvider(DictConfigProvider):
    """
    Class to getting config from json string

    Methods
    -------
    get(*keys) -> ConfigValue
        get value from json
        typical use: get("key1", "key2", "key3" ... "keyN" )
    """

    def __init__(self, json_str: str, ignore_decode_error: bool = False):
        """
        Parameters
        ----------
        json_str : str
            json string
        ignore_decode_error: bool = False
            flag to ignoring errors while decoding json
        """
        super().__init__({})
        try:
            self.data = json.loads(json_str)
        except json.decoder.JSONDecodeError as de:
            if not ignore_decode_error:
                raise de


class JSONFileConfigProvider(JSONConfigProvider):
    """
    Class to getting config from json file

    Methods
    -------
    get(*keys) -> ConfigValue
        get value from json
        typical use: get("key1", "key2", "key3" ... "keyN" )
    """

    def __init__(self, file_name: str = DEFAULT_JSON_CONFIG_FILE, ignore_decode_error: bool = False,
                 ignore_file_reading_error: bool = False):
        """
        Parameters
        ----------
        file_name : str = DEFAULT_JSON_CONFIG_FILE
            json file name
        ignore_decode_error: bool = False
            flag to ignoring errors while decoding json
        ignore_file_reading_error: bool = False
            flag to ignoring errors while reading file
        """
        try:
            with open(file_name, 'r') as file:
                self.data = json.load(file, ignore_decode_error=ignore_decode_error)
                super().__init__(file.read())
        except FileNotFoundError as fe:
            super().__init__("{}")
            if not ignore_file_reading_error:
                raise fe


class YAMLConfigProvider(DictConfigProvider):
    """
    Class to getting config from yaml string

    Methods
    -------
    get(*keys) -> ConfigValue
        get value from yaml
        typical use: get("key1", "key2", "key3" ... "keyN" )
    """

    def __init__(self, yaml_str: str):
        """
        Parameters
        ----------
        yaml_str : str
            yaml config string
        """
        super().__init__(yaml.full_load(yaml_str))


class YAMLFileConfigProvider(YAMLConfigProvider):
    """
    Class to getting config from yaml file

    Methods
    -------
    get(*keys) -> ConfigValue
        get value from yaml
        typical use: get("key1", "key2", "key3" ... "keyN" )
    """

    def __init__(self, file_name: str = DEFAULT_YAML_CONFIG_FILE, ignore_file_reading_error: bool = False):
        """
        Parameters
        ----------
        file_name: str = DEFAULT_YAML_CONFIG_FILE
            yaml config file name
        ignore_file_reading_error: bool = False
            flag to ignoring errors while reading file
        """
        try:
            with open(file_name, 'r') as file:
                super().__init__(file.read())
        except FileNotFoundError as fe:
            super().__init__("")
            if not ignore_file_reading_error:
                raise fe


class TOMLConfigProvider(DictConfigProvider):
    """
    Class to getting config from toml string

    Methods
    -------
    get(*keys) -> ConfigValue
        get value from toml
        typical use: get("key1", "key2", "key3" ... "keyN" )
    """

    def __init__(self, toml_str: str, ignore_decode_error: bool = False):
        """
        Parameters
        ----------
        toml_str : str
            yaml config string
        ignore_decode_error: bool = False
            flag to ignoring errors while decoding json
        """
        try:
            super().__init__(toml.loads(toml_str))
        except toml.decoder.TomlDecodeError as te:
            if not ignore_decode_error:
                raise te


class TOMLFileProvider(TOMLConfigProvider):
    """
    Class to getting config from toml file

    Methods
    -------
    get(*keys) -> ConfigValue
        get value from toml
        typical use: get("key1", "key2", "key3" ... "keyN" )
    """

    def __init__(self, file_name: str = DEFAULT_TOML_CONFIG_FILE, ignore_decode_error: bool = False,
                 ignore_file_reading_error: bool = False):
        """
        Parameters
        ----------
        file_name: str = DEFAULT_YAML_CONFIG_FILE
            yaml config file name
        ignore_decode_error: bool = False
            flag to ignoring errors while decoding json
        ignore_file_reading_error: bool = False
            flag to ignoring errors while reading file
        """
        self.data = {}
        try:
            with open(file_name, 'r') as file:
                super().__init__(file.read(), ignore_decode_error=ignore_decode_error)
        except FileNotFoundError as fe:
            if not ignore_file_reading_error:
                raise fe
