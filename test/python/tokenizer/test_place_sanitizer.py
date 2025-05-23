# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of Nominatim. (https://nominatim.org)
#
# Copyright (C) 2025 by the Nominatim developer community.
# For a full list of authors see the git log.
"""
Tests for execution of the sanitztion step.
"""
import pytest

from nominatim_db.errors import UsageError
import nominatim_db.tokenizer.place_sanitizer as sanitizer
from nominatim_db.data.place_info import PlaceInfo


def test_placeinfo_clone_new_name():
    place = sanitizer.PlaceName('foo', 'ki', 'su')

    newplace = place.clone(name='bar')

    assert place.name == 'foo'
    assert newplace.name == 'bar'
    assert newplace.kind == 'ki'
    assert newplace.suffix == 'su'


def test_placeinfo_clone_merge_attr():
    place = sanitizer.PlaceName('foo', 'ki', 'su')
    place.set_attr('a1', 'v1')
    place.set_attr('a2', 'v2')

    newplace = place.clone(attr={'a2': 'new', 'b2': 'foo'})

    assert place.get_attr('a2') == 'v2'
    assert place.get_attr('b2') is None
    assert newplace.get_attr('a1') == 'v1'
    assert newplace.get_attr('a2') == 'new'
    assert newplace.get_attr('b2') == 'foo'


def test_placeinfo_has_attr():
    place = sanitizer.PlaceName('foo', 'ki', 'su')
    place.set_attr('a1', 'v1')

    assert place.has_attr('a1')
    assert not place.has_attr('whatever')


def test_sanitizer_default(def_config):
    san = sanitizer.PlaceSanitizer([{'step': 'split-name-list'}], def_config)

    name, address = san.process_names(PlaceInfo({'name': {'name:de:de': '1;2;3'},
                                                 'address': {'street': 'Bald'}}))

    assert len(name) == 3
    assert all(isinstance(n, sanitizer.PlaceName) for n in name)
    assert all(n.kind == 'name' for n in name)
    assert all(n.suffix == 'de:de' for n in name)

    assert len(address) == 1
    assert all(isinstance(n, sanitizer.PlaceName) for n in address)


@pytest.mark.parametrize('rules', [None, []])
def test_sanitizer_empty_list(def_config, rules):
    san = sanitizer.PlaceSanitizer(rules, def_config)

    name, address = san.process_names(PlaceInfo({'name': {'name:de:de': '1;2;3'}}))

    assert len(name) == 1
    assert all(isinstance(n, sanitizer.PlaceName) for n in name)


def test_sanitizer_missing_step_definition(def_config):
    with pytest.raises(UsageError):
        sanitizer.PlaceSanitizer([{'id': 'split-name-list'}], def_config)
