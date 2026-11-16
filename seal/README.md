# seal

Show what a change actually changed, and hand the proof to somebody who was not there.

Git records edited lines. A test suite records assertions somebody remembered to write. An AI agent records a confident summary. When a patch arrives from an agent, a refactor, or a dependency bump, you still need an answer to one question: which observable behaviour moved, and which stayed put? `seal` runs a fixed set of probes against two versions of any executable, captures stdout, stderr, exit status and file effects, then classifies every difference against the intent you declared before the run. It writes one JSON file that a reviewer can re-execute on a clean machine.

## 30 seconds

```console
$ ./seal demo
seal demo: two programs, one hidden behaviour change

  stdout before : order total: 42
  stdout after  : order total: 42
  a stdout assertion passes on both

seal behaviour report
  before -> after
  manifest: 21ff77b04dea

probe: prints_total
  UNEXPECTED files_delta (difference outside declared intent scope)

verdict: UNEXPECTED
counts: UNEXPECTED=1, UNKNOWN=0, INTENDED=0, SAME=5

unexpected channels: prints_total/files_delta

seal caught: prints_total/files_delta
next: seal init, then seal record --subject DIR --tag NAME
```

The second version writes `audit.log` as a side effect. The printed output stays identical. `seal` records the file that appeared.

## Install

Python 3.9 or newer. The runtime uses the standard library only.

```console
$ git clone <your-fork-url> && cd seal
$ ./seal --version
seal 0.1.0
```

For a permanent install:

```console
$ python3 -m pip install .
$ seal demo
```

## How it works

1. `seal init` writes `sealfile.json`. You declare the target command, the probes, the intent scope, and the safety policy.
2. `seal record` copies one version of your program into a fresh temporary directory, runs every probe, and stores the observation surface.
3. `seal compare` classifies each channel as `SAME`, `INTENDED`, `UNEXPECTED`, or `UNKNOWN`.
4. `seal compare --bundle evidence.json` writes a self-contained evidence bundle.
5. `seal verify evidence.json --old DIR --new DIR --trust` re-executes the probes in a clean sandbox and checks that your machine reaches the same verdict.

## Commands

| Command | What it does | Exit codes |
|---|---|---|
| `seal init [--manifest PATH] [--force]` | Write a default manifest | 0 written, 2 error |
| `seal record --subject DIR --tag NAME [--manifest PATH] [--out PATH]` | Run probes and capture observations | 0 recorded, 2 error, 3 bad tag |
| `seal compare OLD NEW [--bundle PATH] [--json] [--strict-unknown]` | Classify differences | 0 clean, 1 unexpected, 2 error |
| `seal verify BUNDLE --old DIR --new DIR --trust [--json]` | Reproduce evidence in a clean sandbox | 0 reproduced, 1 mismatch, 2 error, 3 missing trust |
| `seal demo [--json] [--keep]` | Run the 30-second demonstration | 0 caught the change, 2 demo failed |

## Verdicts

| Verdict | Meaning |
|---|---|
| `SAME` | Canonical observation matches after declared normalization |
| `INTENDED` | The channel differs and sits inside `intent.scope` |
| `UNEXPECTED` | The channel differs outside `intent.scope` |
| `UNKNOWN` | A timeout, capped output, declared nondeterminism, or malformed evidence blocks a verdict |

`UNKNOWN` never turns into `SAME`. A run with any `UNEXPECTED` channel exits 1, so CI can gate a merge on it.

## A real workflow

```console
$ mkdir -p /tmp/review && cd /tmp/review
$ seal init
$ $EDITOR sealfile.json          # set target.command and intent.scope
$ seal record --subject ./before --tag before --out before.json
$ seal record --subject ./after  --tag after  --out after.json
$ seal compare before.json after.json --bundle evidence.json
$ seal verify evidence.json --old ./before --new ./after --trust
```

`verify` needs `--trust`. It executes commands stored inside the bundle. Read the manifest first and run it in a network-isolated sandbox.

## Safety

`seal` executes arbitrary programs. The runner refuses shells, rejects symlinks and non-regular files in the subject tree, bounds the subject size, caps output, kills the whole process group on timeout, remaps subject-relative executables into the copied workdir, blocks reserved environment keys such as `LD_PRELOAD`, and redacts secret values before writing a bundle. See [SECURITY.md](SECURITY.md) and [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) for the residual risks, including network access, which the tool declares but does not isolate.

Digests in a bundle detect modification. They do not prove who produced the bundle. You need a signing key for that, and this release has none.

## What this release does not do

- No cloud service, no dashboard, no agent plugin.
- No automatic discovery of probe inputs. You declare probes.
- No deterministic replay of networked programs.
- No cryptographic signing or nonrepudiation.
- No claim about GitHub star counts. Adoption sits outside the codebase. `docs/06_launch_scorecard.md` holds the checkable release criteria instead.

## Prior art

Golden snapshot tools store an expected value inside a project. API diff tools read symbols. Replay debuggers reconstruct an agent session. `docs/07_prior_art.md` names the nearest projects and states the conditional novelty claim with its search date. Read that file before you repeat the claim anywhere.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). The test suite runs with the standard library:

```console
$ PYTHONPATH=src:tests python3 -m unittest discover -s tests -v
$ python3 reviews/run_rounds.py after
$ python3 tests/behavior_lock.py --check
```

## License

MIT. See [LICENSE](LICENSE).
