"""Offline image registry contract.

The 33 pilot nodes carry no photograph: the seven Wikimedia pictures were symbolic (a Swedish
apple tree is not the measured food) and were removed on 2026-09-21 by decision.
"""
from pathlib import Path

import yaml
from jinja2 import Environment, PackageLoader

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = {
    'url': 'images/example.jpg', 'alt': 'Example', 'credit': 'A. Author', 'license': 'CC0',
    'license_url': 'https://example.org/license', 'source_url': 'https://example.org/source',
    'reference_label': 'Reference photograph.',
}


def food_ids():
    foods = yaml.safe_load((ROOT / 'data/registry/foods.yaml').read_text())
    return {k for k in foods if k != 'excluded_foodatlas'}


def render_image(**kwargs):
    env = Environment(loader=PackageLoader('atlas.site', 'templates'), autoescape=True)
    return env.get_template('_plant_image.html.j2').render(**kwargs)


def test_no_pilot_node_resolves_to_an_image():
    from atlas.site.images import image_for
    ids = food_ids()
    assert len(ids) == 33
    assert all(image_for(fid) is None for fid in ids)


def test_registry_tombstones_every_food_so_the_research_queue_stays_quiet():
    images = yaml.safe_load((ROOT / 'data/registry/images.yaml').read_text())
    # research/queue.py enqueues an "image" task for every food id that is missing here
    assert set(images) == food_ids()
    for fid, entry in images.items():
        assert entry.get('removed') and 'url' not in entry, fid


def test_no_photograph_is_left_in_data_images():
    assert not list((ROOT / 'data' / 'images').glob('*.jpg'))


def test_non_mapped_ids_stay_imageless():
    from atlas.foods import FoodNode
    from atlas.site.images import image_for
    for bad in (None, {}, 'apple', 'org:malus-domestica', 'food:nonexistent'):
        assert image_for(bad) is None
    assert image_for(FoodNode('food:apple', 'taxon_food', 'Apple')) is None


def test_template_local_root_credit_and_reference():
    text = render_image(plant_image=FIXTURE, root='../')
    assert 'src="../images/example.jpg"' in text
    for field in ('reference_label', 'credit', 'license', 'source_url', 'license_url'):
        assert FIXTURE[field] in text
    assert 'loading="lazy"' in text


def test_template_absence_tombstone_and_minimal_external_image():
    assert '<img' not in render_image(plant_image=None, root='../')
    assert '<img' not in render_image(plant_image={'removed': 'symbolic image'}, root='../')
    text = render_image(plant_image={'url': 'https://example.org/photo.jpg', 'alt': '<plant>'}, root='../')
    assert 'src="https://example.org/photo.jpg"' in text
    assert '&lt;plant&gt;' in text
    assert 'None' not in text
