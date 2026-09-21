from atlas.claims import Claim
from atlas.registry import Source
from atlas.unified.identity import Edge
from atlas.unified.store import Store

SRC = Source(id="SRC-X", title="t", publisher="p", url="u", license="CC0", license_class="ship",
             license_read=True, kind="measurement", independence="independent",
             supports=("nutrition",), attribution="a")


def claim(subject, field="nutrient:bls:VITC", **kw):
    base = dict(subject=subject, group="nutrition", field=field, v=4.6, src="SRC-X", derivation="analytical",
                unit="mg", basis="as_described", food_part="product")
    return Claim(**(base | kw))


def test_store_is_idempotent_and_routes_rejects(tmp_path):
    s = Store(tmp_path / "u.duckdb")
    claims = [claim("prod:bls:B1"), claim("prod:bls:B2", basis=None), claim("prod:bls:B3", field="f2")]
    stats = s.replace_source("SRC-X", claims, {"SRC-X": SRC}, "b1")
    assert (stats.accepted, stats.rejected) == (2, 1)                 # B2 has no basis -> rule 6
    s.replace_source("SRC-X", claims, {"SRC-X": SRC}, "b2")           # re-run: same rows, no duplicates
    assert s.count("datapoints") == 2 and s.count("rejects") == 1
    # the rejected value is kept as a carried value, not as a claim (rule 6: no basis)
    assert s.con.execute("SELECT rule, carried FROM rejects").fetchall() == [(6, "4.6")]
    s.close()


def test_other_sources_are_untouched_by_a_replace(tmp_path):
    other = Source(**(SRC.__dict__ | {"id": "SRC-Y"}))
    s = Store(tmp_path / "u.duckdb")
    s.replace_source("SRC-Y", [claim("prod:fdc:1", src="SRC-Y")], {"SRC-Y": other}, "b1")
    s.replace_source("SRC-X", [claim("prod:bls:B1")], {"SRC-X": SRC}, "b1")
    s.replace_source("SRC-X", [], {"SRC-X": SRC}, "b2")               # SRC-X now empty
    assert s.count("datapoints") == 1
    s.close()


def test_species_attach_only_through_approved_edges(tmp_path):
    s = Store(tmp_path / "u.duckdb")
    s.replace_source("SRC-X", [claim("prod:bls:B1"), claim("prod:bls:B2", basis=None)], {"SRC-X": SRC}, "b1")
    assert s.species_with_claims("nutrition") == set()                # claims exist, identity does not
    s.load_edges([Edge("prod:bls:B1", "malus domestica", "manual", 1.0, "b", "a", "d"),
                  Edge("prod:bls:B2", "beta vulgaris", "manual", 1.0, "b", "a", "d"),
                  Edge("prod:bls:B3", "zea mays", "manual", 1.0, "b", "a", "d", status="rejected")])
    assert s.species_with_claims("nutrition") == {"malus domestica"}
    assert s.species_searched_empty("nutrition") == {"beta vulgaris"}  # read, but the claim was rejected
    s.close()
