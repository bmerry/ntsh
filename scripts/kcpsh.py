#!/usr/bin/env python3

import sys
import contextlib
import asyncio
import prompt_toolkit
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.layout.containers import VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, TokenListControl
from prompt_toolkit.shortcuts import create_asyncio_eventloop, create_prompt_application
from prompt_toolkit.token import Token


class KatcpProtocol(asyncio.Protocol):
    def __init__(self, cli):
        self.ready = asyncio.Event()
        self.connected = False
        self._cli = cli

    def connection_made(self, transport):
        self.connected = True
        self.ready.set()
        print('Connected')

    def connection_lost(self, exc):
        self.ready.set()
        self.connected = False
        print('Connection lost')
        if exc:
            print(exc)

    def data_received(self, data):
        # TODO: split at newlines
        text = data.decode('utf-8', errors='replace')
        #sys.stdout.write(data.decode('utf-8', errors='replace'))
        def print_text():
            self._cli.print_tokens([(Token.Keyword, text)])
        self._cli.run_in_terminal(print_text)

    def pause_writing(self):
        self.ready.clear()

    def resume_writing(self):
        self.ready.set()


async def test(queue):
    while True:
        command = await queue.get()


async def main():
    loop = asyncio.get_event_loop()
    application = create_prompt_application(
        '(kcpsh) ',
        enable_history_search=True,)
    with contextlib.closing(create_asyncio_eventloop()) as eventloop:
        cli = CommandLineInterface(application=application, eventloop=eventloop)
        sys.stdout = cli.stdout_proxy()
        try:
            transport, protocol = await loop.create_connection(
                lambda: KatcpProtocol(cli), 'localhost', 8888)
        except OSError as error:
            print('Could not connect to {}: {}'.format('localhost:8888', error.strerror), file=sys.stderr)
            return 1
        with contextlib.closing(transport):
            while True:
                try:
                    command = (await cli.run_async()).text
                    await protocol.ready.wait()
                    if not protocol.connected:
                        break
                    print('Command: {}'.format(command))
                    transport.writelines([command.encode('utf-8'), b'\n'])
                except (EOFError, KeyboardInterrupt):
                    break
    return 0


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    ret = loop.run_until_complete(main())
    loop.close()
    sys.exit(ret)
