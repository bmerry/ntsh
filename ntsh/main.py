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

import argparse
import sys
import contextlib
import asyncio
import os
import codecs

from prompt_toolkit.styles import style_from_pygments_dict
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession, print_formatted_text
from prompt_toolkit.formatted_text import PygmentsTokens
from prompt_toolkit.application import run_in_terminal
from pygments.token import Token
import appdirs

from . import protocols
# Protocols are not called directly, but they register themselves on import
from . import katcp       # noqa: F401


STYLE = style_from_pygments_dict({
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
LIMIT = 2**20


class _Printer:
    def __init__(self, protocol, is_input):
        self.is_input = is_input
        self._bol = True
        self._lexer = protocol.input_lexer if is_input \
            else protocol.output_lexer

    def __call__(self, text):
        out_tokens = []
        for line in text.splitlines(True):
            if self.is_input:
                pre = [(Token.Generic.Deleted, '< ')]
            else:
                pre = [(Token.Generic.Inserted, '> ')]
            tokens = self._lexer.get_tokens_unprocessed(line)
            for _, token, data in tokens:
                parts = data.splitlines(True)
                for part in parts:
                    if self._bol:
                        out_tokens.extend(pre)
                        pre[0] = (pre[0][0], '+ ')  # Continuation line
                    # prompt_toolkit asserts that \r is not present.
                    # To allow for receiving \r\n from the network,
                    # strip out all \r.
                    part = part.replace('\r', '')
                    out_tokens.append((token, part))
                    self._bol = part.endswith('\n')

        def printit():
            print_formatted_text(PygmentsTokens(out_tokens), end='',
                                 style=STYLE,
                                 include_default_pygments_style=False)

        run_in_terminal(printit)


class Main:
    def __init__(self, session, reader, writer, protocol):
        self.session = session
        self.reader = reader
        self.writer = writer
        self.protocol = protocol

    async def _run_reader(self):
        printer = _Printer(self.protocol, True)
        decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
        eof = False
        prefix = b''
        while not eof:
            data = await self.reader.read(LIMIT)
            if data == b'':
                eof = True
            data = prefix + data
            last_newline = data.rfind(b'\n')
            if not eof and (len(data) < LIMIT or last_newline != -1):
                # Cut at a newline, to help any parsing
                prefix = data[last_newline + 1 :]
                data = data[: last_newline + 1]
            else:
                prefix = b''
            if data is not None:
                text = decoder.decode(data, eof)
                printer(text)
        self.writer.close()

    async def _get_input(self):
        with patch_stdout():
            try:
                return await self.session.prompt_async()
            except KeyboardInterrupt:
                # KeyboardInterrupt isn't a subclass of Exception, so
                # it doesn't propagate through asyncio quite right.
                # Turn it into an EOFError instead.
                raise EOFError

    async def _run_prompt(self):
        while True:
            future = asyncio.get_event_loop().create_task(self._get_input())
            try:
                # shield to work around
                # https://github.com/prompt-toolkit/python-prompt-toolkit/issues/787
                text = await asyncio.shield(future)
            except EOFError:
                break
            except asyncio.CancelledError:
                # Make the prompt exit cleanly (important to restore
                # terminal settings).
                self.session.app.exit(result='', style='class:exiting')
                await future
                raise
            _Printer(self.protocol, False)(text + '\n')
            self.writer.writelines([text.encode('utf-8'), b'\n'])

    async def run(self):
        futures = [self._run_reader(), self._run_prompt()]
        done, pending = await asyncio.wait(
            futures, return_when=asyncio.FIRST_COMPLETED)
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

    cache_dir = appdirs.user_cache_dir('ntsh')
    try:
        os.makedirs(cache_dir)
    except OSError:
        pass
    if os.path.isdir(cache_dir):
        history = FileHistory(os.path.join(cache_dir, 'history'))
    else:
        history = None

    try:
        reader, writer = await asyncio.open_connection(*args.remote,
                                                       limit=LIMIT)
    except OSError as error:
        print('Could not connect to {}:{}: {}'.format(
                  args.remote[0], args.remote[1], error.strerror),
              file=sys.stderr)
        return 1

    session = PromptSession(
        '> ',
        erase_when_done=True,
        enable_history_search=True,
        history=history,
        lexer=args.protocol.prompt_lexer,
        style=STYLE,
        include_default_pygments_style=False)
    main = Main(session, reader, writer, args.protocol)
    with contextlib.closing(writer):
        await main.run()
    return 0


def main():
    loop = asyncio.get_event_loop()
    with contextlib.closing(loop):
        return loop.run_until_complete(async_main())


if __name__ == '__main__':
    sys.exit(main())
