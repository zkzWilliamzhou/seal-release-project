# Contributing

## Setup

```console
$ git clone <your-fork-url> && cd seal
$ ./seal demo
$ PYTHONPATH=src:tests python3 -m unittest discover -s tests -v
```

No virtual environment is required. The runtime depends on the Python standard library only. `pyproject.toml` uses setuptools at build time so `pip install .` works.

## Rules for a patch

1. Write the failing test first. `tests/` uses `unittest`, not pytest.
2. Keep one responsibility per module in `src/seal/`.
3. Never change a verdict string, an exit code, or a bundle field without an ADR in `docs/adr/`.
4. Run `python3 reviews/run_rounds.py after` and `python3 tests/behavior_lock.py --check`. Both must pass.
5. Any change to `runner.py` needs a threat-model update in `docs/THREAT_MODEL.md` and a test that fails without the fix.

## Review gates

`docs/02_workflow.md` lists G0 through G7. `reviews/` contains eight round reports with the checks that ran and the fixes that followed. A pull request that reports "looks fine" without a command gets sent back.

## Good first issues

Look for issues labelled `good first issue`. Each one states the file, the acceptance criterion, and the test that proves it. Small scopes win:

- add a declared normalization rule with a test
- add a probe example for a language other than Python
- improve an error message with a reproduction command
- extend the launch scorecard with a checkable artifact

## Reporting a vulnerability

Use [SECURITY.md](SECURITY.md). Do not open a public issue for command execution, sandbox escape, or secret leakage.
