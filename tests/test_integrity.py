"""Defensive data-integrity gates, not source-data fixtures."""
from dataclasses import replace
import math

import pytest

from atlas.claims import Claim
from atlas.contract import check
from atlas.registry import Source


def source(**changes):
    s = Source(id='S', title='Test', publisher='Test', url='https://example.org',
               license='CC0', license_class='ship', license_read=True, kind='measurement',
               independence='independent', supports=('nutrition', 'season'), attribution='Test')
    return replace(s, **changes)


def claim(**changes):
    c = Claim(subject='food:apple', group='nutrition', field='vitamin', v=1.0,
              src='S', derivation='analytical', unit='mg', basis='fresh_weight', food_part='whole')
    return replace(c, **changes)


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -float('inf')])
def test_nonfinite_values_are_quarantined(value):
    gap = check(claim(v=value), {'S': source()})
    assert gap and gap.rule == 1


def test_cite_requires_specific_reference():
    c = claim(group='season', field='season:DE', v='Test', curated=True)
    assert check(c, {'S': source(license_class='cite')}).rule == 9
    assert check(replace(c, ref='Table 1, row Test'), {'S': source(license_class='cite')}) is None


def test_license_failure_does_not_redistribute_value_in_gap():
    gap = check(claim(v=12.0), {'S': source(license_read=False)})
    assert gap.rule == 9
    assert gap.carried_value is None
