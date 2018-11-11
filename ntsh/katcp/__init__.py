# ntsh: an interactive tool for line-based protocols
# Copyright (C) 2017, 2018  Bruce Merry
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

from .. import protocols
from .lexer import KatcpLexer

from prompt_toolkit.lexers import PygmentsLexer


class KatcpProtocol(protocols.Protocol):
    ARGS = {
        'unescape': protocols.Argument(bool)
    }

    def __init__(self, name, arglist):
        self.unescape = False
        super().__init__(name, arglist)
        self.prompt_lexer = PygmentsLexer(KatcpLexer)
        self.input_lexer = self.output_lexer = KatcpLexer(
            stripnl=False, stripall=False, ensurenl=False,
            unescape=self.unescape)


protocols.PROTOCOLS['katcp'] = KatcpProtocol
