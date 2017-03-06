# ntsh: an interactive tool for line-based protocols
# Copyright (C) 2017  Bruce Merry
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

import pygments
from prompt_toolkit.token import Token
from prompt_toolkit.layout.lexers import PygmentsLexer
from .. import protocols
from .lexer import KatcpLexer


class KatcpProtocol(protocols.Protocol):
    ARGS = {
        'unescape': protocols.Argument(bool)
    }

    @classmethod
    def _unescape(cls, tokens):
        escapes = {
            r'\\': '\\',
            r'\_': ' ',
            r'\n': '\n',
            r'\@': '',
            r'\0': '\0',
            r'\e': '\033',
            r'\t': '\t',
            r'\r': '\r'
        }
        for token, text in tokens:
            if token is Token.String.Escape and text in escapes:
                yield (Token.String, escapes[text])
            else:
                yield (token, text)

    def __init__(self, name, arglist):
        self.unescape = False
        super(KatcpProtocol, self).__init__(name, arglist)
        self.lexer = PygmentsLexer(KatcpLexer)

    def lex(self, text, is_input):
        tokens = pygments.lex(text, self.lexer.pygments_lexer)
        if self.unescape:
            tokens = self._unescape(tokens)
        return tokens


protocols.PROTOCOLS['katcp'] = KatcpProtocol
