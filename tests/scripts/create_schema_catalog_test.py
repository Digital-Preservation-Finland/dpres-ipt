"""Test that schema creation catalog script behaves correctly."""
import os
import pytest
import xml_helpers.utils as xml_utils

from ipt.scripts.create_schema_catalog import main
from tests.testcommon import shell
from tests.testcommon.settings import TESTDATADIR


@pytest.mark.parametrize(
    ('sip', 'mets', 'catalog', 'expected_rewrite_uri', 'expected_return_code'),
    [('valid_1.7.1_xml_local_schemas', 'mets.xml', None, 1, 0),
     ('valid_1.7.1_xml_local_schemas', 'mets.xml', '/other/catalog.xml', 1, 0),
     ('valid_1.7.1_video_container', 'mets.xml', None, 0, 0),
     ('valid_1.7.1_xml_local_schemas', 'no_mets.xml', None, None, 117)],
    ids=['METS contain local schemas',
         'Different main catalog given from the default',
         'METS does not contain local schemas',
         'METS missing'])
def test_create_schema_catalog(tmpdir,
                               sip,
                               mets,
                               catalog,
                               expected_rewrite_uri,
                               expected_return_code):
    """Test that the script will generate a schema catalog if mets.xml file
    can be read. Other than output parameter, other parameters given should
    be reflected within the schema catalog file.
    """
    output = tmpdir.join('my_catalog_schema.xml').strpath
    sip = os.path.join(TESTDATADIR, 'sips', sip)
    mets = os.path.join(sip, mets)
    args = [mets, sip, output]
    if catalog:
        args.append('-c')
        args.append(catalog)

    (returncode, _, _) = shell.run_main(main, args)
    assert expected_return_code == returncode
    if expected_return_code == 0:
        root_element = xml_utils.readfile(output).getroot()
        assert root_element.attrib[xml_utils.xml_ns('base')].rstrip('/') == sip

        rewrite_uri_count = 0
        next_catalog_count = 0
        for child in root_element:
            if child.tag.endswith('rewriteURI'):
                rewrite_uri_count += 1
            if child.tag.endswith('nextCatalog'):
                next_catalog_count += 1
                if catalog:
                    assert child.attrib['catalog'] == catalog

        # There should always be one catalog.
        assert next_catalog_count == 1
        assert rewrite_uri_count == expected_rewrite_uri
    else:
        assert os.path.isfile(output) is False
