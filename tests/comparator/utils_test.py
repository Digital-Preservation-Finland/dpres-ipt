# coding=utf-8
"""Test for comparator/utils.py."""

import lxml.etree as ET
from ipt.comparator.utils import collect_supplementary_filepaths


def test_collect_supplementary_filepaths():
    """Tests the collect_supplementary_filepaths function."""
    xml = '<mets:mets xmlns:mets="http://www.loc.gov/METS/" ' \
          'xmlns:xlink="http://www.w3.org/1999/xlink"><mets:fileSec>' \
          '<mets:fileGrp><mets:file><mets:FLocat xlink:href="test1.xml"/>' \
          '</mets:file></mets:fileGrp>' \
          '<mets:fileGrp USE="fi-preservation-xml-schemas">' \
          '<mets:file><mets:FLocat xlink:href="test2.xml"/></mets:file>' \
          '<mets:file><mets:FLocat xlink:href="test3.xml"/></mets:file>' \
          '</mets:fileGrp></mets:fileSec></mets:mets>'

    expected_paths = ['test2.xml', 'test3.xml']
    collected_paths = collect_supplementary_filepaths(ET.fromstring(xml),
                                                      'xml_schemas')
    assert len(collected_paths) == len(expected_paths)
    for path in collected_paths:
        assert path in expected_paths
