"""Generate or verify M17 final synthetic evaluation evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from careloop.final_evaluation import (
    load_final_evaluation_corpus,
    load_final_evaluation_gold,
    render_final_evaluation_markdown,
    run_final_evaluation,
)

ROOT = Path(__file__).parents[1]
CORPUS_PATH = ROOT / "benchmarks" / "final" / "m17.cases.v1.json"
GOLD_PATH = ROOT / "benchmarks" / "final" / "gold" / "m17.expectations.v1.json"
RAW_PATH = ROOT / "artifacts" / "raw" / "m17.final-evaluation.v1.json"
SUMMARY_PATH = ROOT / "artifacts" / "summary" / "m17.final-evaluation.v1.md"


def _expected_bytes() -> tuple[bytes, bytes]:
    corpus = load_final_evaluation_corpus(CORPUS_PATH)
    evidence = run_final_evaluation(
        corpus,
        repository_root=ROOT,
        gold_loader=lambda: load_final_evaluation_gold(GOLD_PATH, corpus),
    )
    return evidence.canonical_bytes(), render_final_evaluation_markdown(evidence)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raw, summary = _expected_bytes()
    if args.check:
        mismatches = [
            path
            for path, expected in ((RAW_PATH, raw), (SUMMARY_PATH, summary))
            if not path.exists() or path.read_bytes() != expected
        ]
        if mismatches:
            parser.error(
                "generated M17 evidence differs: "
                + ", ".join(str(path.relative_to(ROOT)) for path in mismatches)
            )
        return 0
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.write_bytes(raw)
    SUMMARY_PATH.write_bytes(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
