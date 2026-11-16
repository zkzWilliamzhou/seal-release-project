# seal release archive

This archive contains the complete `seal` project: source, tests, docs, eight review reports, CI, skills, evidence.

## Contents

| Path | Contents |
|---|---|
| `seal/` | The complete seal project: source, tests, docs, eight review reports, CI, skills, evidence |
| `research/` | `opensource_gap_research.md`, `adoption_playbook.md`, and the figure used by the latter |
| `architecture-review.html` | Self-contained HTML candidate report |
| `tools/` | The GitHub skills installer, the link-driven finisher, and its detached launcher |
| `skill_install_final.log` | Final skills-install log |
| `FINAL_VALIDATION.txt` | Commands, exit codes, and custom checks from the final validation run |
| `CHECKSUMS.sha256` | SHA-256 for every file in this archive except itself |
| `DELIVERY_MANIFEST.md` | This file |

## Quick start

```console
$ cd seal
$ ./seal demo
$ PYTHONPATH=src:tests python3 -m unittest discover -s tests -v
$ python3 tests/behavior_lock.py --check
```

See `seal/README.md` for project documentation.

## License

MIT License. See LICENSE file for details.