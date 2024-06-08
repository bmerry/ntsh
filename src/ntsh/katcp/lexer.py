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

from pygments.lexer import RegexLexer, bygroups, default
from pygments.token import Name, Number, Text, Punctuation, String


class KatcpLexer(RegexLexer):
    name = 'Katcp'

    tokens = {
        'root': [
            (r'\?[A-Za-z][A-Za-z0-9-]*', Name.Request, ('body', 'msgid')),
            (r'![A-Za-z][A-Za-z0-9-]*', Name.Reply, ('body', 'msgid')),
            (r'#[A-Za-z][A-Za-z0-9-]*', Name.Inform, ('body', 'msgid')),
            (r'\n', Text),
        ],
        'msgid': [
            (r'(\[)([1-9][0-9]*)(\])',
             bygroups(Punctuation, Number, Punctuation),
             '#pop'),
            default('#pop')
        ],
        'body': [
            (r'[ \t]*\n', Text, '#pop'),
            (r'[ \t]+', Text, 'argument'),
        ],
        'argument': [
            (r'(?<=[ \t])(?:0|-?[1-9][0-9]*)(?=[ \t]|$)', Number.Integer),
            (r'(?<=[ \t])[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?(?=[ \t]|$)',
                Number.Float),
            (r'\\[\\_0nret@]', String.Escape),
            (r'[^\\ \0\n\r\033\t]+', String),
            default('#pop')
        ]
    }

    def __init__(self, **options):
        super().__init__(**options)
        self.unescape = options.get('unescape', False)

    def get_tokens_unprocessed(self, text):
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

        orig = super().get_tokens_unprocessed(text)
        if self.unescape:
            for index, tokentype, value in orig:
                if tokentype is String.Escape and value in escapes:
                    yield (index, String, escapes[value])
                else:
                    yield (index, tokentype, value)
        else:
            yield from orig
