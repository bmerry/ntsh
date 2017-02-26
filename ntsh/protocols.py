from prompt_toolkit.token import Token
from prompt_toolkit.layout.lexers import SimpleLexer


class ProtocolArgumentError(ValueError):
    pass


class UnknownProtocolArgument(ProtocolArgumentError):
    def __init__(self, protocol, key):
        super(UnknownProtocolArgument, self).__init__()
        self.protocol = protocol
        self.key = key

    def __str__(self):
        return "'{}' is not a valid argument for protocol {}".format(
            self.key, self.protocol.name)


class MissingArgumentValue(ProtocolArgumentError):
    def __init__(self, protocol, key):
        super(UnknownProtocolArgument, self).__init__()
        self.protocol = protocol
        self.key = key

    def __str__(self):
        return "Argument '{}' for protocol {} requires a value".format(
            self.key, self.protocol.name)


class InvalidProtocolArgument(ProtocolArgumentError):
    def __init__(self, protocol, key, value):
        super(InvalidProtocolArgument, self).__init__()
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
    ARGS = {}

    def __init__(self, name, arglist):
        self.name = name
        self.lexer = SimpleLexer(Token.Text)
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

    def lex(self, text, is_input):
        return [(Token.Text, text)]


PROTOCOLS = {'plain': Protocol}


def get_protocol(value):
    fields = value.split(':')
    name = fields[0]
    try:
        protocol_cls = PROTOCOLS[name]
    except KeyError:
        raise UnknownProtocolError(name)
    return protocol_cls(name, fields[1:])
