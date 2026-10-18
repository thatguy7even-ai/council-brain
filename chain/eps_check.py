#!/usr/bin/env python3
"""EPS checker — validates encoding-provenance blocks against lesson vectors.

Usage: python3 eps_check.py <lesson_json_path> [input_names_json]
Checks:
  1. every non-zero in[i] has an encoding entry (else UNJUSTIFIED)
  2. every encoding entry's v == in[i] (else SCHEMA VIOLATION)
  3. every entry has src and why (else WEAK)
"""
import json
import sys

INPUT_NAMES = ["prov_completeness", "measurement_coverage", "seat_consensus",
               "operator_ordered", "stakes", "reversibility", "break_triggered",
               "confab_risk", "record_impact", "novel_claim", "instrument_ready",
               "time_sensitivity", "autonomy_granted", "cross_seat",
               "outward_facing", "data_vs_reading"]


def check(lesson, input_names=INPUT_NAMES):
    findings = []
    enc = lesson.get("encoding", {})
    for i, (name, v) in enumerate(zip(input_names, lesson["in"])):
        if abs(v) < 1e-12:
            continue  # zero needs no justification
        e = enc.get(name)
        if e is None:
            findings.append((name, "UNJUSTIFIED",
                             f"in[{i}]={v} has no encoding entry"))
            continue
        if abs(e.get("v", float("nan")) - v) > 1e-9:
            findings.append((name, "SCHEMA VIOLATION",
                             f"encoding v={e.get('v')} != in[{i}]={v}"))
            continue
        if not e.get("src") or not e.get("why"):
            findings.append((name, "WEAK", "missing src or why"))
    return findings


def main():
    path = sys.argv[1]
    lesson = json.load(open(path))
    findings = check(lesson)
    if not findings:
        print(f"{path}: EPS CLEAN "
              f"({sum(1 for v in lesson['in'] if abs(v) > 1e-12)} justified non-zero values)")
    else:
        print(f"{path}: {len(findings)} findings")
        for name, kind, msg in findings:
            print(f"  [{kind}] {name}: {msg}")


if __name__ == "__main__":
    main()
