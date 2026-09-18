"""Offline image registry contract; no network access during builds/tests."""
from pathlib import Path
import hashlib

import pytest
import yaml
from jinja2 import Environment, PackageLoader

ROOT = Path(__file__).resolve().parents[1]
PILOTS = ('apple', 'cabbage', 'broccoli', 'cauliflower', 'kohlrabi', 'brussels-sprout', 'kale')


@pytest.mark.parametrize('slug', PILOTS)
def test_pilot_image_has_local_asset_and_provenance(slug):
    from atlas.site.images import image_for
    image = image_for({'id': f'food:{slug}', 'level': 'taxon_food'})
    assert image is not None
    assert image['url'].startswith('images/')
    asset = ROOT / 'data' / image['url']
    assert asset.is_file()
    assert 1000 < asset.stat().st_size < 500_000
    assert hashlib.sha256(asset.read_bytes()).hexdigest() == image['sha256']
    assert image['width'] > 0 and image['height'] > 0
    for field in ('alt', 'credit', 'license', 'license_url', 'source_url', 'original_url', 'retrieved', 'changes'):
        assert image[field]
    assert image['source_url'].startswith('https://commons.wikimedia.org/')
    assert image['reference_label']


def test_non_mapped_ids_stay_imageless():
    from atlas.site.images import image_for
    # Unknown IDs, organisms and garbage inputs still resolve to None;
    # there is no code-level fallback.
    for bad in (None, {}, 'apple', 'org:malus-domestica', 'food:nonexistent'):
        assert image_for(bad) is None


def test_object_and_string_ids_and_copy():
    from atlas.foods import FoodNode
    from atlas.site.images import image_for
    assert image_for(FoodNode('food:apple', 'taxon_food', 'Apple')) == image_for('food:apple')
    changed = image_for('food:apple')
    changed['alt'] = 'bad'
    assert image_for('food:apple')['alt'] != 'bad'


def render_image(**kwargs):
    env = Environment(loader=PackageLoader('atlas.site', 'templates'), autoescape=True)
    return env.get_template('_plant_image.html.j2').render(**kwargs)


def test_template_local_root_credit_and_reference():
    from atlas.site.images import image_for
    image = image_for('food:apple')
    text = render_image(plant_image=image, root='../')
    assert 'src="../images/apple.jpg"' in text
    assert image['reference_label'] in text
    assert image['credit'] in text
    assert image['license'] in text
    assert image['source_url'] in text
    assert image['license_url'] in text
    assert 'loading="lazy"' in text


def test_template_absence_and_minimal_external_image():
    assert '<img' not in render_image(plant_image=None, root='../')
    text = render_image(plant_image={'url': 'https://example.org/photo.jpg', 'alt': '<plant>'}, root='../')
    assert 'src="https://example.org/photo.jpg"' in text
    assert '&lt;plant&gt;' in text
    assert 'None' not in text


def test_registry_covers_every_food_and_labels_references():
    images = yaml.safe_load((ROOT / 'data/registry/images.yaml').read_text())
    foods = yaml.safe_load((ROOT / 'data/registry/foods.yaml').read_text())
    food_ids = {k for k in foods if k != 'excluded_foodatlas'}
    # Every food entry has an explicit image mapping; mapping stays explicit-only.
    assert set(images) == food_ids
    # Only the seven taxon-level foods carry an original photograph; every other
    # entry must visibly label its image as a taxon reference, not the thing itself.
    taxa = {f'food:{slug}' for slug in PILOTS}
    for fid, img in images.items():
        assert img['reference_label']
        if fid not in taxa:
            assert 'reference' in img['reference_label'].lower(), fid
