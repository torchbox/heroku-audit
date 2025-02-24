# Heroku-audit

[![CI](https://github.com/torchbox/heroku-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/torchbox/heroku-audit/actions/workflows/ci.yml)![PyPI](https://img.shields.io/pypi/v/heroku-audit.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/heroku-audit.svg)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/heroku-audit.svg)
![PyPI - Status](https://img.shields.io/pypi/status/heroku-audit.svg)
![PyPI - License](https://img.shields.io/pypi/l/heroku-audit.svg)

Command-line tool for reporting on specific attributes of a Heroku environment.

## Components

- Apps
- Users
- Environment Variables
- Heroku Postgres
- Heroku Data for Redis
- Domains

## Installation

### PyPI

```
pip install heroku-audit
```

### Homebrew

Heroku Audit can be installed from Torchbox's [Homebrew tap](https://github.com/torchbox/homebrew-tap).

```
brew tap torchbox/tap
brew install heroku-audit
```

### Arch Linux

Arch users can install [`heroku-audit`](https://aur.archlinux.org/packages/heroku-audit) from the AUR.

```
paru -S heroku-audit
```

### Pre-compiled binaries

You can download the pre-compiled binary from the releases, built with [`pyinstaller`](https://pyinstaller.org/en/stable/).

## Usage

Note: See `heroku-audit --help` for further details.

Authentication is handled through the `$HEROKU_API_KEY` environment variable, which must be set to a valid Heroku API key. Alternatively, you can create a `config.env` file in the config directory (`heroku-audit --show-config-dir`).

Each components is its own sub-command, containing a number of pre-made reports. `heroku-audit --list` will list all available commands.

To audit for a single team, add `--team=<team>`.

### Output Format

By default, a pretty table is output, for easy consumption by humans. `--format` can be specified to all commands to change the format:

- `table` (Default)
- `csv`
- `json`
- `count`

Progress output is automatically removed when running non-interactively.
