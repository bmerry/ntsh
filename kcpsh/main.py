import argparse
import sys
import contextlib
import asyncio
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.shortcuts import (
    create_asyncio_eventloop, create_prompt_application)
from prompt_toolkit.token import Token
from prompt_toolkit.layout.lexers import PygmentsLexer
import pygments
from .katcp_lexer import KatcpLexer


def unescape(tokens):
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


class State(object):
    def __init__(self, cli, reader, writer, args):
        self._cli = cli
        self.reader = reader
        self.writer = writer
        self.args = args
        self._lexer = KatcpLexer()

    def _print_tokens(self, tokens):
        self._cli.run_in_terminal(lambda: self._cli.print_tokens(tokens))

    async def _run_reader(self):
        while True:
            line = await self.reader.readline()
            if line == b'':
                break
            if line[-1:] == b'\n':
                line = line[:-1]
            text = line.decode('utf-8', errors='replace') + '\n'
            tokens = pygments.lex(text, self._lexer)
            if self.args.unescape:
                tokens = unescape(tokens)
            self._print_tokens(tokens)
        self.writer.close()

    async def _run_prompt(self):
        while True:
            try:
                command = (await self._cli.run_async()).text
            except (EOFError, KeyboardInterrupt):
                break
            self.writer.writelines([command.encode('utf-8'), b'\n'])
            await self.writer.drain()

    async def run(self):
        done, pending = await asyncio.wait(
            [self._run_reader(), self._run_prompt()],
            return_when=asyncio.FIRST_COMPLETED)
        for future in done:
            await future
        for future in pending:
            future.cancel()
            try:
                await future
            except asyncio.CancelledError:
                pass


def endpoint(value):
    colon = value.rfind(':')
    if colon == -1:
        raise ValueError(': not found')
    return value[:colon], value[colon + 1:]


def parse_args():
    parser = argparse.ArgumentParser(description='Connect to a katcp server')
    parser.add_argument('remote', type=endpoint, metavar='HOST:PORT',
                        help='Remote endpoint')
    parser.add_argument('-u', '--unescape', action='store_true',
                        help='Decode escape sequences when printing replies')
    args = parser.parse_args()
    return args


async def async_main():
    args = parse_args()

    style = style_from_dict({
        Token.Name.Request: '#ansifuchsia',
        Token.Name.Reply: '#ansiturquoise',
        Token.Name.Inform: '#ansidarkgray',
        Token.String: '#ansilightgray',
        Token.String.Escape: '#ansiwhite',
        Token.Number: '#ansigreen',
        Token.Number.Integer: '#ansigreen',
        Token.Number.Float: '#ansigreen',
        Token.Error: 'underline'
    })
    application = create_prompt_application(
        '(kcpsh) ',
        enable_history_search=True,
        lexer=PygmentsLexer(KatcpLexer),
        style=style)
    with contextlib.closing(create_asyncio_eventloop()) as eventloop:
        cli = CommandLineInterface(application=application,
                                   eventloop=eventloop)
        sys.stdout = cli.stdout_proxy()
        try:
            reader, writer = await asyncio.open_connection(*args.remote)
        except OSError as error:
            print('Could not connect to {}:{}: {}'.format(
                      args.remote[0], args.remote[1], error.strerror),
                  file=sys.stderr)
            return 1
        state = State(cli, reader, writer, args)
        with contextlib.closing(writer):
            await state.run()
    return 0


def main():
    loop = asyncio.get_event_loop()
    with contextlib.closing(loop):
        return loop.run_until_complete(async_main())


if __name__ == '__main__':
    sys.exit(main())
