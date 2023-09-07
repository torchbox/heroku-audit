# Heroku-audit

Command-line tool for reporting on specific attributes of a Heroku environment.

## Components

- Apps
- Users
- Environment Variables
- Heroku Postgres
- Heroku Data for Redis

## Installation

```
$ pip install heroku-audit
```

Alternatively, you can download the pre-compiled binary from the releases.

## Usage

Note: See `heroku-audit --help` for further details.

Authentication is handled through the `$HEROKU_API_KEY` environment variable, which must be set to a valid Heroku API key. Alternatively, you can create a `heroku-api-key.txt` file in the config directory (`heroku-audit --show-config-dir`).

Each components is its own sub-command, containing a number of pre-made reports. `heroku-audit --list` will list all available commands.

To audit for a single team, add `--team=<team>`.

### Output Format

By default, a pretty table is output, for easy consumption by humans. `--format` can be specified to all commands to change the format:

- `table` (Default)
- `csv`
- `json`

Progress output is automatically removed when running non-interactively.
