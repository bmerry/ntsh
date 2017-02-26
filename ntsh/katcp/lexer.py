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
