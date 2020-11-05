# coding=utf-8
"""Test for comparator/utils.py."""

import lxml.etree as ET
from ipt.comparator.utils import (collect_supplementary_filepaths,
                                  collect_xml_schemas)


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


def test_collect_xml_schemas():
    """Tests the collect_xml_schemas function."""
    xml = '<mets:mets xmlns:mets="http://www.loc.gov/METS/" ' \
          'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' \
          '<mets:amdSec><mets:techMD><mets:mdWrap><mets:xmlData>' \
          '<premis:object xmlns:premis="info:lc/xmlns/premis-v2" '\
          'xsi:type="premis:representation"><premis:environment>' \
          '<premis:environmentPurpose>xml-schemas' \
          '</premis:environmentPurpose><premis:dependency>' \
          '<premis:dependencyName>schemas/my_schema.xsd' \
          '</premis:dependencyName><premis:dependencyIdentifier>' \
          '<premis:dependencyIdentifierType>URI' \
          '</premis:dependencyIdentifierType>' \
          '<premis:dependencyIdentifierValue>http://localhost/my_schema.xsd' \
          '</premis:dependencyIdentifierValue></premis:dependencyIdentifier>' \
          '</premis:dependency></premis:environment></premis:object>' \
          '</mets:xmlData></mets:mdWrap></mets:techMD>' \
          '</mets:amdSec></mets:mets>'

    schemas = collect_xml_schemas(ET.fromstring(xml))
    assert len(schemas) == 1
    assert schemas['http://localhost/my_schema.xsd'] == 'schemas/my_schema.xsd'
