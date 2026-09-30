#!/usr/bin/env python3
"""Fail if a workflow defines the same job twice.

PyYAML keeps the last of two identical job keys without complaining, so a bad
edit to a workflow file is invisible to a plain load. It only shows up as an
Actions run that reports a workflow file error and starts no jobs.
"""
import collections
import pathlib
import sys

import yaml

fail = 0
for path in sorted(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".github/workflows").glob("*.y*ml")):
    doc = yaml.safe_load(path.read_text())
    if not isinstance(doc, dict) or "jobs" not in doc:
        continue
    # Keys are strings in the file, but YAML 1.1 turns some words like "on" into booleans.
    jobs = [k for k in doc["jobs"] if isinstance(k, str)]
    dupes = {k: v for k, v in collections.Counter(jobs).items() if v > 1}
    # Count every key line in the text too, since a duplicate is lost by the time
    # the document is loaded.
    import re
    text = path.read_text()
    declared = re.findall(r"^  ([A-Za-z][A-Za-z0-9_-]*):\s*$", text, re.M)
    text_dupes = {k: v for k, v in collections.Counter(declared).items() if v > 1}
    if dupes or text_dupes:
        fail = 1
        print(f"{path}: duplicate job definitions", file=sys.stderr)
        for k, v in {**dupes, **text_dupes}.items():
            print(f"  {k} appears {v} times", file=sys.stderr)
    else:
        print(f"{path}: {len(jobs)} jobs, no duplicates")
raise SystemExit(fail)
