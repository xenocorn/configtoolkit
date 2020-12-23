from dataclasses import dataclass
from typing import Any, Callable
import json
import sys
import os
import yaml
import importlib
import toml
from configparser import ConfigParser


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
        or from data dict and nested dictionaries or arrays by keys
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
        get value from data dict by key
        or from data dict and nested dictionaries or arrays by keys

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
