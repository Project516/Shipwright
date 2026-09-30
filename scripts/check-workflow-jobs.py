#!/usr/bin/env python3
"""Fail if a workflow defines the same job twice.

A duplicated job key is invisible to a plain load, because the loader keeps the
last one without complaint. The only symptom is an Actions run that reports a
workflow file error and starts no jobs at all.

Usage: check-workflow-jobs.py [workflow-dir]
"""
import pathlib
import sys

import yaml


class DupLoader(yaml.SafeLoader):
    """A loader that refuses a mapping key it has already seen.

    Duplicate keys are legal in YAML, and every plain loader silently keeps the
    last one. That is exactly the case worth failing on here.
    """


def _no_duplicates(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        # Take the key as the text written in the file. PyYAML resolves an unquoted on or
        # yes to a boolean, so a job named on and a job named yes would otherwise share one
        # key and a job would vanish, and on: with "on": would look like two distinct keys.
        if isinstance(key_node, yaml.ScalarNode):
            key = key_node.value
        else:
            key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r} at line {key_node.start_mark.line + 1}", key_node.start_mark
            )
        seen.add(key)


def _mapping(loader, node, deep=False):
    _no_duplicates(loader, node, deep=deep)
    # Hand the already-validated pairs to the standard constructor, keyed by the raw text.
    result = {}
    for key_node, value_node in node.value:
        key = key_node.value if isinstance(key_node, yaml.ScalarNode) else key_node
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


DupLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)

def main(argv: list[str]) -> int:
    root = pathlib.Path(argv[1] if len(argv) > 1 else ".github/workflows")
    if not root.is_dir():
        print(f"{root} is not a directory", file=sys.stderr)
        return 2

    fail = 0
    for path in sorted(list(root.glob("*.yml")) + list(root.glob("*.yaml"))):
        try:
            doc = yaml.load(path.read_text(), Loader=DupLoader)
        except yaml.constructor.ConstructorError as e:
            fail = 1
            print(f"{path}: {e.problem}", file=sys.stderr)
            continue
        if not isinstance(doc, dict):
            continue
        jobs = doc.get("jobs")
        if not isinstance(jobs, dict):
            continue
        # Report the keys the loader would have dropped, so the message is useful.
        print(f"{path}: {len(jobs)} jobs, no duplicate keys")
    return fail


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
