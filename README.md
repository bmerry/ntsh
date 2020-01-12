# ntsh

ntsh is an interactive tool for line-based protocols, such as HTTP
or SMTP. It can be thought of as a netcat that's better suited to
interactive use by a human. Features include an editable prompt,
history, and syntax highlighting, and asynchronous replies from
the server won't interfere with the prompt.

## Installation

ntsh is a pure-Python package, although Python 3.6 is required. To install,
unpack the source tarball (or pull from github), and in the source directory,
run `pip install .` (or `pip3 install .`, if that is the path for your Python
3-compatible `pip`).

## Usage

To connect to a remote host *host* on port *port*, run
```sh
ntsh host:port
```
This makes no assumptions about protocol. To specify a protocol, pass it with
`-p protocol[:options]`. At present the only supported protocol is
[katcp](https://katcp-python.readthedocs.io/en/latest/).

## Revision history

### 1.1

- Switch to prompt\_toolkit 3

### 1.0

- Switch to prompt\_toolkit 2

### 0.1.2

- Fix crash when long lines are received from the remote (#2)

### 0.1.1

- Depend on prompt\_toolkit 1.0.15 instead of using an internal hack

### 0.1

- Initial release

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
