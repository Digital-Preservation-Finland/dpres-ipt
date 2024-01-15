"""Create a schema catalog from given parameters."""


import argparse
import os
import sys
from urllib.parse import urlparse

import mets
import premis
import xml_helpers.utils
from xml_helpers.schema_catalog import construct_catalog_xml
from ipt.utils import parse_uri_filepath, ensure_text


def main(arguments=None):
    """ The main method for create-schema-catalog script"""
    args = parse_arguments(arguments)
    result = _create_schema_catalog(mets_path=args.mets,
                                    sip=args.sip,
                                    output_path=args.output_path,
                                    catalog=args.catalog)
    return result


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line arguments
    :param arguments: Arguments given to the argparser.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('mets',
                        metavar='METS',
                        help=('File path to METS document containing local '
                              'schema linkings.'))
    parser.add_argument('sip',
                        metavar='SIP',
                        help='Path to information package directory')
    parser.add_argument('output_path',
                        metavar='OUTPUT',
                        help='Write the catalog to given file path')
    parser.add_argument(
        '-c', '--catalog',
        dest='catalog',
        default='/etc/xml/dpres-xml-schemas/schema_catalogs/catalog_main.xml',
        help=('File path to another existing (main) schema catalog to be '
              'added to the schema catalog that is constructed.'))

    return parser.parse_args(arguments)


def _create_schema_catalog(mets_path, sip, output_path, catalog):
    """Create schema catalog based on given METS XML, and possibly catalog
    file.

    :param mets_path: METS XML file to fetch the schema URIs.
    :param sip: SIP path where all package content is located under.
    :param output_path: File to create the schema catalog to.
    :param catalog: Catalog file to be added as nextCatalog entry.
    :return: Integer 0 when no issue arises. 117 if METS file is missing.
    """
    try:
        mets_tree = xml_helpers.utils.readfile(mets_path)
    except OSError as err:
        print(ensure_text(str(err)), file=sys.stderr)
        return 117

    try:
        schemas = _collect_xml_schemas(sip_path=sip,
                                       mets_tree=mets_tree)
    except ValueError as err:
        print(ensure_text(str(err)), file=sys.stderr)
        return 117

    catalog_xml = construct_catalog_xml(
        base_path=sip,
        rewrite_rules=schemas,
        next_catalogs=[catalog])
    with open(output_path, 'wb') as out_file:
        out_file.write(xml_helpers.utils.serialize(catalog_xml))
    return 0


def _collect_xml_schemas(sip_path, mets_tree):
    """Collect all XML schemas from the METS. The schemas are ordered as
    a dictionary with the schemaLocations as keys and the schema paths
    as values. The schemaLocations can either be URIs or paths to
    files.

    The XML schema catalog mainly understands URIs when mapping
    locations to paths. If a local file path is used without an URI
    syntax, the catalog needs to read the file paths as relative
    locations from the catalog file itself in order to rewrite the
    URI prefixes properly.

    :param sip_path: The path to the SIP contents
    :param mets_tree: METS XML tree
    :returns: a dictionary of schema locations and paths
    """
    schemas = {}
    environments = None
    for techmd in mets.iter_techmd(mets_tree):
        environments = premis.iter_environments(techmd)
    if environments is not None:
        for environment in premis.environments_with_purpose(
                environments,
                purpose='xml-schemas'):
            for dependency in premis.parse_dependency(environment):
                parsed_name = next(premis.iter_elements(dependency,
                                                        'dependencyName')).text

                schema_path = parse_uri_filepath(
                    uri_path=parsed_name,
                    accepted_schemes=('file', ''))
                # Check that illegal paths pointing outside the SIP don't
                # exist. Raise error if such case happens as it is
                # considered malformed mets.xml content.
                abs_schema_path = os.path.abspath(os.path.join(sip_path,
                                                               schema_path))
                abs_sip_path = os.path.abspath(sip_path)
                if not abs_schema_path.startswith(abs_sip_path):
                    raise ValueError((f'Schema [{schema_path}]'
                                      'must not point outside '
                                      'of SIP directory'))
                (_, id_value) = premis.parse_identifier_type_value(
                    dependency, prefix='dependency')
                # Add absolute path to catalog file if the value is a simple
                # file path and not an URI
                if not urlparse(id_value).scheme:
                    schema_path = os.path.join(sip_path, schema_path)
                schemas[id_value] = schema_path

    return schemas


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
