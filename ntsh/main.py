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

import argparse
import sys
import contextlib
import asyncio
import os
import codecs

from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.shortcuts import (
    create_asyncio_eventloop, create_prompt_application)
from prompt_toolkit.token import Token
from prompt_toolkit.buffer import AcceptAction
from prompt_toolkit.history import FileHistory
import appdirs

from . import protocols, katcp


class _Printer:
    def __init__(self, cli, protocol, is_input):
        self.is_input = is_input
        self._bol = True
        self._cli = cli
        self._protocol = protocol

    def __call__(self, text):
        if self.is_input:
            pre = [(Token.Generic.Deleted, '< ')]
        else:
            pre = [(Token.Generic.Inserted, '> ')]
        tokens = self._protocol.lex(text, self.is_input)
        out_tokens = []
        for token, data in tokens:
            parts = data.splitlines(True)
            for part in parts:
                if self._bol:
                    out_tokens.extend(pre)
                    pre[0] = (pre[0][0], '+ ')  # Continuation line
                out_tokens.append((token, part))
                self._bol = part.endswith('\n')
        self._cli.run_in_terminal(lambda: self._cli.print_tokens(out_tokens), cooked_mode=False)


class Main:
    def __init__(self, cli, reader, writer, protocol):
        self._cli = cli
        self.reader = reader
        self.writer = writer
        self.protocol = protocol
        cli.application.buffer.accept_action = \
            AcceptAction(self._accept_handler)

    async def _run_reader(self):
        printer = _Printer(self._cli, self.protocol, True)
        decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
        eof = False
        while not eof:
            try:
                line = await self.reader.readuntil()
            except asyncio.IncompleteReadError as error:
                line = error.partial
                eof = True
            except asyncio.LimitOverrunError as error:
                line = await self.reader.readexactly(error.consumed)
            text = decoder.decode(line, eof)
            printer(text)
        self.writer.close()

    def _accept_handler(self, cli, buffer):
        text = buffer.document.text
        _Printer(self._cli, self.protocol, False)(text + '\n')
        self.writer.writelines([text.encode('utf-8'), b'\n'])
        buffer.reset(append_to_history=True)

    async def _run_prompt(self):
        try:
            await self._cli.run_async()
        except (EOFError, KeyboardInterrupt):
            pass

    async def run(self):
        futures = [self._run_reader(), self._run_prompt()]
        done, pending = await asyncio.wait(
            futures, return_when=asyncio.FIRST_COMPLETED)
        for future in done:
            await future
        # If the network socket finished first, given the prompt time to
        # absorb any CPR responses.
        if futures[1] not in done:
            await asyncio.sleep(0.1)
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

    cache_dir = appdirs.user_cache_dir('ntsh')
    try:
        os.makedirs(cache_dir)
    except OSError:
        pass
    if os.path.isdir(cache_dir):
        history = FileHistory(os.path.join(cache_dir, 'history'))
    else:
        history = None

    style = style_from_dict({
        Token.Generic.Inserted: '#ansifuchsia',
        Token.Generic.Deleted: '#ansiturquoise',
        Token.Name.Request: '#ansifuchsia',
        Token.Name.Reply: '#ansiturquoise',
        Token.Name.Inform: '#ansidarkgray',
        Token.String: '#ansilightgray',
        Token.String.Escape: '#ansiwhite',
        Token.Number: '#ansigreen',
        Token.Number.Integer: '#ansigreen',
        Token.Number.Float: '#ansigreen'
    })

    application = create_prompt_application(
        '> ',
        erase_when_done=True,
        enable_history_search=True,
        history=history,
        lexer=args.protocol.lexer,
        style=style)
    with contextlib.closing(create_asyncio_eventloop()) as eventloop:
        cli = CommandLineInterface(application=application,
                                   eventloop=eventloop)
        sys.stdout = cli.stdout_proxy()
        try:
            reader, writer = await asyncio.open_connection(*args.remote, limit=2**20)
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
