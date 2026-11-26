# Specification: tree-config

- **Component:** `framework/tree-config`
- **Status:** Draft, implemented in Sprint 002
- **Language:** Python 3.12 (standard library only)

## Purpose

`tree-config` reads and writes TREE OS configuration files. Applications and
services use it instead of writing their own file handling, so every
configuration file is validated the same way and written safely.

It is a framework component, so it must not import application or service code
(CLAUDE.md section 4).

## Scope

In scope:

- Schema-based validation of configuration values.
- JSON configuration files stored under the user's configuration directory.
- Atomic writes that never leave a partially written file behind.

Out of scope (later components):

- System-wide configuration under `/etc`, which needs Polkit (CLAUDE.md
  section 11).
- Change notifications over D-Bus.
- Migration between schema versions.

## File format

- Encoding: UTF-8. Format: a single JSON object at the top level.
- Location: `$XDG_CONFIG_HOME/treeos/<name>.json`. If `XDG_CONFIG_HOME` is unset
  or empty, `~/.config/treeos/<name>.json` is used.
- `<name>` must match `[a-z][a-z0-9-]*`, so it cannot contain path separators.

## Schema

A schema maps each key to a field definition. A field has:

| Attribute | Required | Meaning |
| --- | --- | --- |
| `kind` | yes | One of `bool`, `int`, `str`. |
| `default` | yes | Value used when the key is absent. Must itself be valid. |
| `minimum`, `maximum` | no | Inclusive bounds. Only valid for `int`. |
| `choices` | no | Allowed values. Only valid for `str`. |

## Validation rules

- The top-level JSON value must be an object.
- Every key in the file must be defined in the schema. Unknown keys are an
  error, so typos are reported instead of silently ignored.
- A value must match its field's `kind`. `bool` must be a JSON boolean, not a
  number, because Python treats `True` as an integer.
- `int` bounds and `str` choices are enforced.
- Missing keys take their default value.

## Behavior

### `load(path, schema)`

- If the file does not exist, return the schema defaults. This is not an error.
- If the file exists but cannot be read, is not valid JSON, or fails validation,
  raise `ConfigError`. The error names the file and the offending key where
  possible. The file is never modified by `load`.

### `save(path, schema, values)`

- Validate `values` against the schema before touching the disk. Invalid values
  raise `ConfigError` and nothing is written.
- Write to a temporary file in the same directory, flush and `fsync` it, replace
  the target with `os.replace`, then `fsync` the directory. A crash leaves either
  the old file or the new file, never a partial one.
- Create missing parent directories. The temporary file is created with mode
  `0600`.
- On any failure, remove the temporary file and raise `ConfigError`, chaining
  the original `OSError`.

### `config_path(name)`

- Return the path for a configuration name, following the file format rules
  above. Raise `ConfigError` for an invalid name.

## Errors

All expected failures raise `ConfigError`. Unexpected exceptions are not caught.

## Security

- The module never runs commands and never reads files other than the one it
  was asked to load.
- Configuration values are not secrets. Passwords, tokens and keys must not be
  stored in these files (CLAUDE.md section 11).

## Tests

Automated tests in `tests/unit/test_tree_config.py` cover: defaults for a
missing file, valid load and save round trips, invalid JSON, non-object JSON,
unknown keys, wrong types (including booleans given as integers), bounds and
choices, invalid schemas, invalid names, and atomic-write cleanup on failure.

## Limitations

- JSON cannot hold comments. Users who edit the file by hand must keep valid JSON.
- No file locking. Two processes saving the same file at once will race, and the
  last writer wins.
