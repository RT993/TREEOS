# Specification: tree-logging

- **Component:** `framework/tree-logging`
- **Status:** Draft, implemented in Sprint 003
- **Language:** Python 3.12 (standard library only)

## Purpose

`tree-logging` gives every TREE OS component the same logger names, output
format and secret handling. CLAUDE.md section 11 requires that security-relevant
failures are logged without leaking secrets, so redaction lives here rather than
in each component.

It is a framework component, so it must not import application or service code
(CLAUDE.md section 4).

## Scope

In scope:

- Logger naming under the `treeos` namespace.
- One stream handler for the `treeos` logger, with a fixed format.
- Redaction of secret-looking values in log messages and `extra=` fields.

Out of scope (later components):

- Journald or syslog handlers. systemd captures standard error, so services
  need no extra handler for the first release.
- Log rotation, log files and remote log shipping.
- Structured (JSON) output.

## Logger names

- `get_logger(component)` returns `logging.getLogger("treeos.<component>")`.
- `component` must match `[a-z][a-z0-9-]*`. Any other value raises `ValueError`.

## Output

`configure(level, *, stream=None)` attaches a `StreamHandler` to the `treeos`
logger with this format:

```text
<asctime> <LEVELNAME> <logger name>: <message>
```

- `level` is a logging level name (`DEBUG`, `INFO`, `WARNING`, `ERROR`,
  `CRITICAL`, case-insensitive) or a non-negative integer. Anything else raises
  `ValueError`. Booleans are rejected.
- `stream` defaults to standard error.
- Calling `configure` again replaces the handler this module installed earlier.
  Handlers added by other code are kept.
- The `treeos` logger does not propagate to the global root logger, so a record
  is never printed twice and never printed without redaction.

## Redaction

Redaction is done by `SecretRedactionFilter`, which the installed handler uses.

- **Message text.** A `key=value` or `key: value` pair is masked when the key is
  one of `password`, `passwd`, `passphrase`, `secret`, `token`, `api_key`
  (also `api-key`, `apikey`) or `private_key`, matched case-insensitively. The
  key and separator are kept. The value is replaced with `<redacted>`. Quoted
  values are masked as a whole. The value ends at whitespace, `,`, `;` or `&`.
- **Format arguments.** The message is formatted first, then redacted, so `%s`
  arguments are covered.
- **`extra=` fields.** An extra attribute whose name matches a secret key is
  replaced with `<redacted>`. A string extra attribute is passed through the
  same text redaction.
- The filter never drops a record.

`redact_text(text)` exposes the text rule for other code.

## Errors

Invalid component names and invalid levels raise `ValueError`. Logging calls do
not raise for redaction problems; the filter only rewrites records.

## Security

- Redaction is best effort. It matches common secret names only. Code must not
  log secrets under other names, and must not log secret values at all.
- The module never reads files, runs commands or opens network connections.
- Configuration values and secrets are never stored by this module.

## Tests

Automated tests in `tests/unit/test_tree_logging.py` cover: logger naming,
invalid component names, level filtering, level validation, idempotent
`configure`, preservation of foreign handlers, the non-propagation setting,
message and argument redaction, `extra=` redaction and the non-dropping filter.

## Limitations

- Redaction does not detect secrets by their shape (for example a bare JWT or
  an unlabelled key). Such values must not be logged.
- Only one handler is installed by this module. Output is not written to a file.
