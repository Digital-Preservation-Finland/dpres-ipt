# coding=utf-8
"""Test for utils.py."""

import random
import pytest

from ipt.utils import (compare_lists_of_dicts, find_max_complete, merge_dicts,
                       serialize_dict, uri_to_path,
                       pair_compatible_list_elements, parse_uri_filepath)

CODEC1 = {"codec": "foo"}
CODEC2 = {"codec": "bar"}
AUDIOMD1 = {"audiomd": [CODEC1]}
AUDIOMD2 = {"audiomd": [CODEC2]}
VIDEOMD = {"codec": "foo", "duration": "bar"}
AUDIOVIDEOMD = {"audiomd": [CODEC1], "videomd": [VIDEOMD]}
FORMAT1 = {'format': {'mimetype': None, 'version': '1.0'}}
FORMAT2 = {'format': {'mimetype': 'image/ipeg', 'version': None}}
FORMAT3 = {'format': {'mimetype': 'image/ipeg', 'version': None}}


def test_merge_dicts():
    """Tests for merge dict."""
    metadata_info = {'filename': "sippi"}
    addml = {"addml": {"charset": "UTF-8"}}

    # Simple merge
    metadata_info = merge_dicts(metadata_info, AUDIOMD1)
    assert metadata_info == {"audiomd": [{"codec": "foo"}],
                             "filename": "sippi"}

    # Merge dicts that contain list-elements with same key
    metadata_info = merge_dicts(metadata_info, AUDIOMD2)
    assert metadata_info == {"audiomd": [
        {"codec": "foo"}, {"codec": "bar"}], "filename": "sippi"}

    # Merge dicts that contain multiple list-elements
    metadata_info = merge_dicts(metadata_info, AUDIOVIDEOMD)
    assert metadata_info == {
        "audiomd": [{"codec": "foo"}, {"codec": "bar"}, {"codec": "foo"}],
        "filename": "sippi",
        "videomd": [{"codec": "foo", "duration": "bar"}]}

    metadata_info = merge_dicts(metadata_info, addml)
    assert metadata_info == {
        "audiomd": [{"codec": "foo"}, {"codec": "bar"}, {"codec": "foo"}],
        "filename": "sippi",
        "videomd": [{"codec": "foo", "duration": "bar"}],
        "addml": {"charset": "UTF-8"}}

    # Merge dict in dict. Merge NoneType elements.
    metadata_info = merge_dicts(FORMAT1, FORMAT2)
    assert metadata_info == {'format': {'mimetype': 'image/ipeg',
                                        'version': '1.0'}}

    # Try to merge dicts that contain duplicate values
    with pytest.raises(TypeError):
        merge_dicts(FORMAT2, FORMAT3)


def test_compare_lists_of_dicts():
    """Test list comparison of dicts."""
    assert compare_lists_of_dicts(None, None)
    assert compare_lists_of_dicts([CODEC1, CODEC2], [CODEC1, CODEC2])
    assert not compare_lists_of_dicts([CODEC1], None)
    assert not compare_lists_of_dicts(None, [CODEC1])
    assert not compare_lists_of_dicts([CODEC1, CODEC2], [CODEC1])
    assert not compare_lists_of_dicts([CODEC1], [CODEC1, CODEC2])
    assert not compare_lists_of_dicts([CODEC1], [CODEC1, CODEC1])
    assert not compare_lists_of_dicts([CODEC1, CODEC1], [CODEC1])


def test_serialize_dict():
    """Test list serialization"""
    assert serialize_dict(CODEC1) == "codec=foo"
    assert serialize_dict({"a": "b", "c": "d"}) == "a=b  c=d"
    assert serialize_dict({"c": "d", "a": "b"}) == "a=b  c=d"


def test_uri_to_path():
    result = uri_to_path(u"file://files/f%C3%B5le.txt")
    assert result == b"files/f\xc3\xb5le.txt"
    assert result.decode("utf-8") == u"files/fõle.txt"


def test_find_max_complete():
    assert find_max_complete(None, None) == ([], [])
    assert find_max_complete([], []) == ([], [])

    list1 = [{"format": {"mimetype": "video/mp4",
                         "version": None},
              "video": {"width": '1920',
                        "height": '1080',
                        "avg_frame_rate": "25"}},
             {"format": {"mimetype": "video/mpeg",
                         "version": "1"},
              "video": {"width": '320',
                        "height": '240',
                        "bit_rate": '0.32',
                        "avg_frame_rate": "29.97"}}]
    list2 = [{"format": {"mimetype": "video/mp4",
                         "version": None},
              "video": {"width": '1920',
                        "height": '1080',
                        "bit_rate": '0.32',
                        "avg_frame_rate": "25"}},
             {"format": {"mimetype": "video/mpeg",
                         "version": "1"},
              "video": {"width": '320',
                        "bit_rate": '0.32',
                        "avg_frame_rate": "29.97"}}]
    expect = [{"format": {"mimetype": "video/mp4",
                          "version": None},
               "video": {"width": '1920',
                         "avg_frame_rate": "25"}},
              {"format": {"mimetype": "video/mpeg",
                          "version": "1"},
               "video": {"width": '320',
                         "avg_frame_rate": "29.97"}}]

    (res1, res2) = find_max_complete(list1, list2)
    assert res1 == expect
    assert res2 == expect

    (res1, res2) = find_max_complete(list1, list2, ['height'])
    expect[0]['video']['height'] = '1080'
    assert res2 == expect

    expect[1]['video']['height'] = '240'
    assert res1 == expect

    (res1, res2) = find_max_complete(
        list1, [{'format': {'foo': 'bar'}}], ['mimetype'])
    assert res1 == [{"format": {"mimetype": "video/mp4"}},
                    {"format": {"mimetype": "video/mpeg"}}]
    assert res2 == [{'format': {}}]
    (res1, res2) = find_max_complete(
        [{'format': {'foo': 'bar'}}], None, ['format', 'mimetype'])
    assert res1 == [{'format': {'foo': 'bar'}}]
    assert res2 == []


def test_pair_compatible_list_elements():
    """ Test that pair_compatible_list_elements returns:
        - empty set when pairing empty lists
        - empty set when elements cannot be paired
        - correct set of index tuples when pairing is possible
    """

    def integer_compare(a, b):
        """Helper function to compare equality of integers"""
        return a == b

    random.seed(1)

    assert pair_compatible_list_elements([], [], integer_compare) == set()

    index_pairs = pair_compatible_list_elements(
        [1, 2, 3], [2, 3, 1], integer_compare)
    assert index_pairs == {(0, 2), (1, 0), (2, 1)}

    assert not pair_compatible_list_elements(
        [1, 2, 3], [1, 4, 2], integer_compare)
    assert not pair_compatible_list_elements(
        [2, 3, 3], [2, 3, 3, 1], integer_compare)

    list_a = [1] * 5 + [2] * 5
    list_b = [1] * 5 + [2] * 5
    random.shuffle(list_b)
    index_pairs = pair_compatible_list_elements(
        list_a, list_b, integer_compare)
    assert all(list_a[idx_a] == list_b[idx_b] for idx_a, idx_b in index_pairs)

    list_a = [1] * 5 + [2] * 5
    list_b = [1] * 4 + [2] * 6
    random.shuffle(list_b)
    assert not pair_compatible_list_elements(list_a, list_b, integer_compare)

    list_a = list(range(100))
    list_b = list(range(100))
    random.shuffle(list_b)
    index_pairs = pair_compatible_list_elements(
        list_a, list_b, integer_compare)
    assert all(list_a[idx_a] == list_b[idx_b] for idx_a, idx_b in index_pairs)

    list_a = list(range(100))
    list_b = list(range(1, 101))
    random.shuffle(list_b)
    assert not pair_compatible_list_elements(list_a, list_b, integer_compare)


@pytest.mark.parametrize('case', [
    'file:/data/local.xsd',
    'file://data/local.xsd',
    'file:///data/local.xsd',
    'data/local.xsd',
    '/data/local.xsd',
    './data/local.xsd',
    '/./data/local.xsd',
    'http:/data/local.xsd',
    'http://data/local.xsd',
    'http:///data/local.xsd',
])
def test_parse_uri_filepath(case):
    path = parse_uri_filepath(uri_path=case,
                              accepeted_schemes=('http', 'file', ''))
    assert path == 'data/local.xsd'


def test_parse_uri_filepath_error():
    with pytest.raises(ValueError):
        parse_uri_filepath(uri_path='file:///does-not-exist.txt',
                           accepeted_schemes=('http',))
