"""Plain HTML/CSS rendering — content-agnostic plumbing, no I/O, no other papeete-* package."""
from papeete_actor.manifest import Manifest
from papeete_actor.portal import Section, render

WAITER = Manifest(name="waiter", description="Takes orders and answers when asked who they're from.")


def test_render_with_no_sections_shows_identity_only():
    html = render(WAITER)
    assert "<h1>waiter</h1>" in html
    assert "Takes orders and answers when asked who they" in html
    assert "re from." in html
    assert "<table>" not in html


def test_render_lays_out_each_section_as_a_table():
    section = Section("Data", ("name", "type"), (("order_id", "string"), ("total", "number")))
    html = render(WAITER, (section,))
    assert "<h2>Data</h2>" in html
    assert "<th>name</th><th>type</th>" in html
    assert "<td>order_id</td><td>string</td>" in html
    assert "<td>total</td><td>number</td>" in html


def test_render_escapes_untrusted_content():
    hostile = Manifest(name="<script>alert(1)</script>", description="ok")
    html = render(hostile)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
