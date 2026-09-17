import textwrap

from atlas.curated import load_curated


def test_load_curated_marks_claims(tmp_path):
    (tmp_path / "apple.yaml").write_text(textwrap.dedent("""
        subject: food:apple
        claims:
          - {group: sensory, field: texture, v: "Crisp to mealy", src: SRC-EDITORIAL, derivation: editorial}
          - {group: season, field: season:DE, v: "Aug–Oct", src: SRC-BZFE-SAISONKALENDER, derivation: registry, ref: "Saisonkalender, Äpfel"}
    """), encoding="utf-8")
    claims = load_curated(tmp_path)
    assert len(claims) == 2 and all(c.curated and c.subject == "food:apple" for c in claims)
    assert claims[1].ref == "Saisonkalender, Äpfel"
