import argparse
import sys
import contextlib
import asyncio
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.shortcuts import (
    create_asyncio_eventloop, create_prompt_application)
from prompt_toolkit.token import Token
from prompt_toolkit.buffer import AcceptAction
from . import protocols, katcp


class Main(object):
    def __init__(self, cli, reader, writer, protocol):
        self._cli = cli
        self.reader = reader
        self.writer = writer
        self.protocol = protocol
        cli.application.buffer.accept_action = \
            AcceptAction(self._accept_handler)

    def _print_tokens(self, tokens):
        self._cli.run_in_terminal(lambda: self._cli.print_tokens(tokens))

    def _print_line(self, text, is_input):
        self._print_tokens(self.protocol.lex(text, is_input))

    async def _run_reader(self):
        while True:
            line = await self.reader.readline()
            if line == b'':
                break
            if line[-1:] == b'\n':
                line = line[:-1]
            text = line.decode('utf-8', errors='replace') + '\n'
            self._print_line(text, True)
        self.writer.close()

    def _accept_handler(self, cli, buffer):
        text = buffer.document.text
        self._print_line(text + '\n', False)
        self.writer.writelines([text.encode('utf-8'), b'\n'])
        buffer.reset(append_to_history=True)

    async def _run_prompt(self):
        try:
            await self._cli.run_async()
        except (EOFError, KeyboardInterrupt):
            pass

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
    parser = argparse.ArgumentParser(
        description='Interactive tool for line-based TCP protocols')
    parser.add_argument('remote', type=endpoint, metavar='HOST:PORT',
                        help='Remote endpoint')
    parser.add_argument('-p', '--protocol',
                        metavar='PROTOCOL[:OPTION=VALUE...]',
                        default='plain', help='Protocol [%(default)s]')
    args = parser.parse_args()
    try:
        args.protocol = protocols.get_protocol(args.protocol)
    except ValueError as error:
        parser.error(str(error))
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
        '(ntsh) ',
        erase_when_done=True,
        enable_history_search=True,
        lexer=args.protocol.lexer,
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
        main = Main(cli, reader, writer, args.protocol)
        with contextlib.closing(writer):
            await main.run()
    return 0


def main():
    loop = asyncio.get_event_loop()
    with contextlib.closing(loop):
        return loop.run_until_complete(async_main())


if __name__ == '__main__':
    sys.exit(main())