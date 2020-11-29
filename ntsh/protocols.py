# ntsh: an interactive tool for line-based protocols
# Copyright (C) 2017, 2018, 2020  Bruce Merry
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from typing import Dict

from prompt_toolkit.lexers import SimpleLexer
from pygments.lexers.special import TextLexer


class ProtocolArgumentError(ValueError):
    pass


class UnknownProtocolArgument(ProtocolArgumentError):
    def __init__(self, protocol, key):
        super().__init__()
        self.protocol = protocol
        self.key = key

    def __str__(self):
        return "'{}' is not a valid argument for protocol {}".format(
            self.key, self.protocol.name)


class MissingArgumentValue(ProtocolArgumentError):
    def __init__(self, protocol, key):
        super().__init__()
        self.protocol = protocol
        self.key = key

    def __str__(self):
        return "Argument '{}' for protocol {} requires a value".format(
            self.key, self.protocol.name)


class InvalidProtocolArgument(ProtocolArgumentError):
    def __init__(self, protocol, key, value):
        super().__init__()
        self.protocol = protocol
        self.key = key
        self.value = value

    def __str__(self):
        return "'{}' is not a valid value for {} in protocol {}".format(
            self.value, self.key, self.protocol.name)


class UnknownProtocolError(ValueError):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "'{}' is not a recognised protocol".format(self.name)


class Argument(object):
    def __init__(self, type):
        self.type = type


class Protocol(object):
    ARGS: Dict[str, Argument] = {}

    def __init__(self, name, arglist):
        self.name = name
        self.prompt_lexer = SimpleLexer()
        self.input_lexer = self.output_lexer = TextLexer(
            stripnl=False, stripall=False, ensurenl=False)
        for item in arglist:
            parts = item.split('=', 1)
            key = parts[0]
            if key not in self.ARGS:
                raise UnknownProtocolArgument(self, key)
            arg = self.ARGS[key]
            if len(parts) < 2:
                if arg.type is not bool:
                    raise MissingArgumentValue(self, item)
                else:
                    value = True
            else:
                try:
                    value = arg.type(parts[1])
                except TypeError as error:
                    raise InvalidProtocolArgument(self, key, parts[1]) \
                        from error
            setattr(self, key, value)


PROTOCOLS = {'plain': Protocol}


def get_protocol(value):
    fields = value.split(':')
    name = fields[0]
    try:
        protocol_cls = PROTOCOLS[name]
    except KeyError:
        raise UnknownProtocolError(name)
    return protocol_cls(name, fields[1:])
