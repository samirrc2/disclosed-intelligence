# Environment (Code Ocean–compatible)

## Code Ocean

`Dockerfile` pins the exact analysis stack (Python 3.11 + `numpy==2.2.6`,
`pandas==2.2.3`, `scipy==1.14.1`, `statsmodels==0.14.4`, `matplotlib==3.9.2`).
Reproduction needs **no API keys and no network**.

Capsule mounts:

| Mount | Contents |
|-------|----------|
| `/code` | `src/`, `scripts/`, `tests/`, `requirements.txt`, `run` |
| `/data` | frozen pseudonymized inputs (see `data/README.md`) |
| `/results` | analysis outputs (tables, figures, `metrics_summary.md`) |

Default Reproducible Run: `/code/run` → `bash code/scripts/reproduce.sh`
(analyze the frozen data, then a byte-identical replication check).

## Local development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r code/requirements.txt
bash reproduce.sh            # analyze + determinism check → results/latest/
bash reproduce.sh --test     # unit tests only
```

`reproduce.sh` sets `PYTHONPATH=code/src` and resolves `data/` and `results/`
automatically for both a local checkout and the Code Ocean mounts.
