# Troubleshooting

## `error: manifest not found: sealfile.json`

Run `seal init` in the directory where you want to work, or pass `--manifest PATH`. `seal init` refuses to overwrite an existing file unless you add `--force`.

## `error: executable not in policy.allowed_commands: <name>`

The manifest allowlist is a set of executable basenames. Add the name to `policy.allowed_commands` and record the two runs again. Changing the manifest changes its digest, so older records no longer compare against new ones. Start a fresh pair.

## `error: bundle digest mismatch: content was modified`

Someone edited the bundle after it was written. Ask the producer for the original file. Do not add `--trust` to a bundle that fails this check.

## `error: verify executes commands from the bundle`

`seal verify` needs `--trust`. Read `bundle["manifest"]` first. Run verification in a container with no network interface. The allowlist, reserved environment keys, timeouts, and output caps still apply.

## `UNKNOWN` on every channel

Check `status` in the record. `timeout` means `policy.timeout_seconds` was too small. `output_capped` means `policy.max_output_bytes` was too small. A channel listed in `nondeterminism` stays `UNKNOWN` by design. Fix the probe, then record both versions again.

## `error: subject tree exceeds policy.max_subject_bytes`

The subject directory holds generated artifacts. Point `--subject` at a clean build output, or raise `policy.max_subject_bytes` inside its documented bound.

## `error: symlink in subject tree is refused` or `non-regular file ... is refused`

The runner copies the subject into a sandbox and refuses symlinks, FIFOs, sockets, and device nodes. Copy the needed files into a plain directory and record again.

## Two runs of the same program produce `UNEXPECTED`

Add `timestamps: true` to `manifest.normalization` only if the timestamps are cosmetic. Keep `PYTHONHASHSEED`, `TZ`, and `LC_ALL` fixed. A probe that reads a live service needs a mock. Do not hide the difference with a broad normalization rule.

## A probe example for a non-Python target

```json
{
  "schema": 1,
  "target": {"command": ["./build/app"]},
  "probes": [{"name": "help", "args": ["--help"], "stdin": "", "env": {}}],
  "normalization": {"crlf": true, "ansi": false, "timestamps": false},
  "nondeterminism": [],
  "intent": {"scope": ["stdout"], "description": "help text was updated"},
  "policy": {
    "timeout_seconds": 10,
    "max_output_bytes": 1048576,
    "max_subject_bytes": 67108864,
    "allowed_commands": ["python3"],
    "allow_network": false
  }
}
```

`./build/app` must be a regular executable file inside the subject directory. The runner remaps it into the copied workdir before execution.
