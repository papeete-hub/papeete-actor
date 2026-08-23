"""Plain HTML/CSS rendering for an actor's identity page — reusable plumbing only.

papeete-actor owns HOW to render; it does not know WHAT a caller wants shown. Composition —
deciding which sections exist for a given actor — belongs to whichever package already
aggregates that actor's facets (papeete-actor-synchronous-messaging today). This module never
imports anything outside papeete-actor, and never touches a filesystem or a network — it turns
data in, HTML string out, and nothing else.
"""
from dataclasses import dataclass
from html import escape

from .manifest import Manifest

_STYLE = """
body { font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem;
       color: #1a1a1a; }
h1 { margin-bottom: 0.25rem; }
p.description { color: #555; margin-top: 0; }
h2 { margin-top: 2rem; }
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; padding: 0.4rem 0.6rem; border-bottom: 1px solid #ddd; }
th { background: #f5f5f5; }
"""


@dataclass(frozen=True)
class Section:
    title: str
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]   # each row's length matches headers — tabular, nothing fancier


def render(manifest: Manifest, sections: tuple[Section, ...] = ()) -> str:
    """One static HTML page: identity first, then each section as a table, in the order given."""
    parts = [
        "<!doctype html>",
        "<html><head><meta charset='utf-8'>",
        f"<title>{escape(manifest.name)}</title>",
        f"<style>{_STYLE}</style>",
        "</head><body>",
        f"<h1>{escape(manifest.name)}</h1>",
        f"<p class='description'>{escape(manifest.description)}</p>",
    ]
    for section in sections:
        parts.append(f"<h2>{escape(section.title)}</h2>")
        parts.append("<table>")
        parts.append("<tr>" + "".join(f"<th>{escape(h)}</th>" for h in section.headers) + "</tr>")
        for row in section.rows:
            parts.append("<tr>" + "".join(f"<td>{escape(c)}</td>" for c in row) + "</tr>")
        parts.append("</table>")
    parts.append("</body></html>")
    return "\n".join(parts)
