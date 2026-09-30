#!/usr/bin/env python3
"""Fail the build when the staged web page references a file that is not there.

The staging step copies the build output, and a file that never made it to the
site returns 404 in the browser rather than failing anything. This walks the
deployed page and reports every local reference it cannot find.

Usage: check-web-assets.py <site-dir>
"""
import html.parser
import pathlib
import re
import sys

# Matches url(...) in CSS with single quotes, double quotes, or no quotes.
CSS_URL = re.compile(r"""url\(\s*(?:"([^"]*)"|'([^']*)'|([^)'"\s]*))\s*\)""", re.I)
# Local means not remote, not inline, not a fragment, not a data URI.
REMOTE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:)?//|^data:|^#|^mailto:", re.I)


def local_path(raw: str) -> str | None:
    """The site-relative file a reference points at, or None if it is not local.

    A root-absolute path returns None as well, because it resolves against the
    domain root rather than the site directory, but it is reported separately.
    """
    ref = html.unescape(raw.strip())
    if not ref or REMOTE.match(ref):
        return None
    # Drop a query string or fragment, so app.js?v=2 resolves to app.js.
    ref = ref.split("?", 1)[0].split("#", 1)[0]
    if not ref or ref.startswith("/"):
        return None
    return ref


class Refs(html.parser.HTMLParser):
    """Collects src, href and srcset values, and the text of any style element."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.refs: list[str] = []
        self.css: list[str] = []
        self._in_style = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "style":
            self._in_style = True
        for name, value in attrs:
            if not value:
                continue
            if name in ("src", "href", "poster", "data"):
                self.refs.append(value)
            elif name == "srcset":
                for part in value.split(","):
                    candidate = part.strip().split(" ", 1)[0]
                    if candidate:
                        self.refs.append(candidate)

    def handle_endtag(self, tag: str) -> None:
        if tag == "style":
            self._in_style = False

    def handle_data(self, data: str) -> None:
        # Only inside style elements. Scanning the whole file would match url() calls
        # in the script, such as URL.createObjectURL(blob).
        if self._in_style:
            self.css.append(data)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    site = pathlib.Path(argv[1])
    index = site / "index.html"
    if not index.is_file():
        print(f"no index.html in {site}", file=sys.stderr)
        return 1
    if not index.stat().st_size:
        print(f"{index} is empty", file=sys.stderr)
        return 1

    # Every page and stylesheet that shipped, not just index.html.
    sources = sorted(p for p in site.rglob("*") if p.suffix in (".html", ".css") and p.is_file())
    if not sources:
        print(f"no html or css in {site}", file=sys.stderr)
        return 1

    parser = Refs()
    for source in sources:
        text = source.read_text(encoding="utf-8", errors="replace")
        parser.feed(text)
        # A standalone stylesheet is scanned directly, with no style element around it.
        if source.suffix == ".css":
            parser.css.append(text)

    refs = [r for r in (local_path(v) for v in parser.refs) if r]
    css = "".join(parser.css)
    refs += [r for r in (local_path(m) for m in (a or b or c for a, b, c in CSS_URL.findall(css))) if r]
    refs = sorted(set(refs))

    root_absolute = sorted({
        html.unescape(v.strip()).split("?", 1)[0].split("#", 1)[0]
        for v in parser.refs
        if v.strip().startswith("/") and not REMOTE.match(v.strip())
    })
    nested = [p for p in sources if p.parent != site]

    if not refs and not root_absolute:
        print("found no local references, so the check proved nothing", file=sys.stderr)
        return 1

    missing = []
    for ref in refs:
        # A relative reference in a nested file resolves against that file's directory
        # first, then against the site root.
        found = False
        for base in [p.parent for p in nested] + [site]:
            target = base / ref
            if target.is_file() or (target.is_dir() and (target / "index.html").is_file()):
                found = True
                break
        if not found:
            missing.append(ref)

    # A warning, not a failure. A root-absolute path breaks under a Pages subpath but is
    # correct when the site is served from a domain root, and the check cannot tell which.
    for ref in root_absolute:
        print(f"warning: root-absolute reference, which 404s under a Pages subpath: {ref}", file=sys.stderr)

    for ref in missing:
        print(f"missing from the staged site: {ref}", file=sys.stderr)

    if missing:
        return 1
    print(f"all {len(refs)} local references are present in {site}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
