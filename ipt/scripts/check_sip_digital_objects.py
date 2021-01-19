#!/usr/bin/python
"""Validate all digital objects in a given METS document"""

from __future__ import print_function, unicode_literals

import argparse
import datetime
import os
import sys
import uuid

import premis
import xml_helpers.utils
from file_scraper.scraper import Scraper

from ipt.comparator.utils import iter_metadata_info
from ipt.comparator.comparator import MetadataComparator
from ipt.utils import merge_dicts, create_scraper_params, get_scraper_info
from ipt.six_utils import ensure_text

_UNAVAILABLE_VERSION_VALUES = ('', '(:unav)', '(:unap)')


def main(arguments=None):
    """The main method for check-sip-digital-objects script"""

    args = parse_arguments(arguments)
    report = validation_report(
        sip_path=args.sip_path,
        catalog_path=args.catalog_path,
        linking_sip_type=args.linking_sip_type,
        linking_sip_id=args.linking_sip_id)

    print(ensure_text(xml_helpers.utils.serialize(report)))

    if contains_errors(report):
        return 117

    return 0


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    default_path = (
        '/etc/xml/dpres-xml-schemas/schema_catalogs/catalog_main.xml')

    parser = argparse.ArgumentParser()
    parser.add_argument('sip_path', help='Path to information package')
    parser.add_argument('linking_sip_type', default=' ')
    parser.add_argument('linking_sip_id', default=' ')
    parser.add_argument('-c', '--catalog_path', dest='catalog_path',
                        default=default_path,
                        help='Full path to XML catalog file',
                        metavar='FILE')

    return parser.parse_args(arguments)


def contains_errors(report):
    """
    Check if premis report contains any events with 'failure' as the outcome.
    """
    events = report.findall('.//' + premis.premis_ns('eventOutcome'))
    for event in events:
        if event.text == 'failure':
            return True
    return False


def make_result_dict(is_valid, messages=None, errors=None,
                     extensions=None, valid_only_messages=None):
    """ Create a result dict from a validation component output.

    :is_valid: Boolean describing the validation result.
    :messages: List of message strings obtained from a validation component.
    :errors: List of error strings obtained from a validation component.
    :extensions: List of lxml.etree elements which are added to
                 eventOutcomeDetailExtension element in the report
    :valid_only_messages: List of messages that should only be appended to
                          the end of the report if the final result is valid.
    :returns: A result_dict created from the arguments.
    """
    if is_valid not in (True, False, None):
        raise TypeError('is_valid must be boolean or None, got {}'
                        .format(type(is_valid)))
    # Ensure all values are lists so that merge_dicts can be used
    # to join the results
    return {
        'is_valid': [is_valid],
        'messages': messages if messages else [],
        'errors': errors if errors else [],
        'extensions': extensions if extensions else [],
        'valid_only_messages': (valid_only_messages
                                if valid_only_messages else [])
    }


def check_mets_errors(metadata_info):
    """
    Check if metadata was parsed correctly from mets.

    :metadata_info: Dictionary containing metadata parsed from mets.
    :returns: result_dict dictionary.
    """
    if metadata_info['errors']:
        return make_result_dict(
            is_valid=False,
            messages=['Failed parsing METS, skipping validation.'],
            errors=[metadata_info['errors']]
        )
    return make_result_dict(is_valid=True)


def skip_validation(metadata_info):
    """ File format validation is not done for native file formats. """
    return metadata_info['use'] == 'no-file-format-validation'


def append_format_info(message, mimetype, version=''):
    """
    Append file format information to the message.

    :returns: <prefix>mimetype: <mimetype>[, version: <version>]
    """
    message += 'mimetype: {}'.format(mimetype)
    if version not in _UNAVAILABLE_VERSION_VALUES:
        message += ', version: {}'.format(version)
    return message


def check_well_formed(metadata_info, catalog_path):
    """
    Check if file is well formed. If mets specifies an alternative format or
    scraper identifies the file as something else than what is given in mets,
    add a message specifying the alternative mimetype and version. Validate
    file as the mimetype given in mets.

    :param metadata_info: Dictionary containing metadata parsed from mets.
    :param catalog_path: Schema XML catalog path to pass to file-scraper.
    :returns: Tuple with 2 dicts: (result_dict, scraper.streams)
    """
    messages = []
    valid_only_messages = []
    md_mimetype = metadata_info['format']['mimetype']
    md_version = metadata_info['format']['version']
    force_mimetype = False

    if 'alt-format' in metadata_info['format']:
        messages.append(
            append_format_info('METS alternative ',
                               metadata_info['format']['alt-format']))
        force_mimetype = True
    else:
        scraper = Scraper(metadata_info['filename'])
        (mime, version) = scraper.detect_filetype()
        if mime != md_mimetype or version != md_version:
            messages.append(
                append_format_info('Detected ', mime, version))
            force_mimetype = True

    scraper_mimetype = None
    scraper_version = None
    if force_mimetype:
        scraper_mimetype = md_mimetype
        scraper_version = md_version
        messages.append(append_format_info('METS ', md_mimetype, md_version))
        messages.append(append_format_info('Validating as ', md_mimetype,
                                           md_version))
        valid_only_messages.append(
            append_format_info('The digital object will be preserved as ',
                               md_mimetype, md_version))

    scraper = Scraper(metadata_info['filename'],
                      mimetype=scraper_mimetype,
                      version=scraper_version,
                      catalog_path=catalog_path,
                      **create_scraper_params(metadata_info))
    scraper.scrape()

    scraper_info = get_scraper_info(scraper)
    messages.extend(scraper_info['messages'])
    return (make_result_dict(is_valid=scraper.well_formed,
                             messages=messages,
                             errors=scraper_info['errors'],
                             extensions=scraper_info['extensions'],
                             valid_only_messages=valid_only_messages),
            scraper.streams)


def check_metadata_match(metadata_info, scraper_streams):
    """
    Compare mets metadata to scraper metadata using the
    MetadataComparator class.

    :metadata_info: Dictionary containing metadata parsed from mets.
    :scraper: File-scraper object which must have already called scrape().
    :returns: result_dict dictionary.
    """
    comparator = MetadataComparator(metadata_info, scraper_streams)
    result = comparator.result()
    messages = ['[MetadataComparator] ' + msg for msg in result['messages']]
    errors = ['[MetadataComparator] ' + err for err in result['errors']]
    return make_result_dict(result['is_valid'], messages, errors)


def join_validation_results(metadata_info, results):
    """
    Join multiple result_dicts obtained from different validation components
    into a single dictionary, which is used to create the validation report.

    :metadata_info: Dictionary containing metadata parsed from mets.
    :results: List of result_dicts.
    :returns: Dictionary which contains metadata_info and the aggregated
              validation results.
    """
    joined_result = merge_dicts(*results)
    messages = joined_result['messages']
    is_valid = all(joined_result['is_valid'])
    if is_valid:
        messages.extend(joined_result['valid_only_messages'])
    return {
        'metadata_info': metadata_info,
        'is_valid': is_valid,
        'messages': '\n'.join(messages),
        'errors': '\n'.join(joined_result['errors']),
        'extensions': joined_result['extensions']
    }


def validation(mets_path, catalog_path):
    """
    Validate all files enumerated in mets.xml files.

    :mets_path: Path to the directory which contains the mets.xml file
                or the full path to mets.xml file itself
    :catalog_path: Path to a XML catalog file
    :yields: {
                'metadata_info': metadata_info,
                'is_valid': Boolean which is True iff all validation components
                            report valid results.
                'messages': String containing joined messages from all
                            validation components.
                'errors': String containing joined errors from all validation
                          components.
            }
    """

    def _validate(metadata_info):
        """
        Perform validation operations in the following order:
        1. Check metadata_info for errors and notes; if there are errors,
           skip other steps.
        2. Check if file needs to be validated; if not, skip other steps.
        3. Check if file is well formed using scraper; if not, skip comparison.
        4. Check that mets metadata matches scraper metadata.

        :returns: Dictionary containing joined results from the above steps.
        """
        results = []

        mets_result = check_mets_errors(metadata_info)
        results.append(mets_result)
        if not mets_result['is_valid'][0] or skip_validation(metadata_info):
            return join_validation_results(metadata_info, results)
        scraper_result, streams = check_well_formed(metadata_info,
                                                    catalog_path=catalog_path)
        results.append(scraper_result)
        if scraper_result['is_valid'][0]:
            results.append(check_metadata_match(metadata_info, streams))
        return join_validation_results(metadata_info, results)

    mets_tree = None

    if mets_path is not None:
        # If the mets_path is a directory path, add mets.xml to mets_path
        if os.path.isdir(mets_path):
            mets_path = os.path.join(mets_path, 'mets.xml')
        mets_tree = xml_helpers.utils.readfile(mets_path)

    for metadata_info in iter_metadata_info(mets_tree=mets_tree,
                                            mets_path=mets_path):
        yield _validate(metadata_info)


def create_report_agent():
    """Create premis agent describing who/what performed validation."""
    # TODO: Agent could be the used validator instead of script file
    agent_name = "check_sip_digital_objects.py-v0.0"
    agent_id_value = 'preservation-agent-' + agent_name + '-' + \
                     str(uuid.uuid4())
    agent_id = premis.identifier(
        identifier_type='preservation-agent-id',
        identifier_value=agent_id_value, prefix='agent')
    report_agent = premis.agent(agent_id=agent_id, agent_name=agent_name,
                                agent_type='software')

    return report_agent


def create_report_object(metadata_info, linking_sip_type, linking_sip_id):
    """Create premis element for digital object."""
    dep_id = premis.identifier(
        metadata_info['object_id']['type'],
        metadata_info['object_id']['value'],
        prefix='dependency')
    dependency = premis.dependency(identifiers=[dep_id])
    environ = premis.environment(child_elements=[dependency])

    related_id = premis.identifier(
        identifier_type=linking_sip_type,
        identifier_value=linking_sip_id,
        prefix='object')
    related = premis.relationship(
        relationship_type='structural',
        relationship_subtype='is included in',
        related_object=related_id)

    object_id = premis.identifier('preservation-object-id',
                                  str(uuid.uuid4()))

    report_object = premis.object(
        object_id=object_id, original_name=metadata_info['filename'],
        child_elements=[environ, related],
        representation=True)

    return report_object


def create_report_event(result, report_object, report_agent):
    """Create premis element for digital object validation event."""
    event_id = premis.identifier(
        identifier_type="preservation-event-id",
        identifier_value=str(uuid.uuid4()), prefix='event')
    outresult = 'success' if result["is_valid"] is True else 'failure'

    if result["errors"]:
        detail_note = (result["messages"] + '\n' + result["errors"])
    else:
        detail_note = result["messages"]

    extensions = result.get('extensions', None)
    outcome = premis.outcome(outcome=outresult, detail_note=detail_note,
                             detail_extension=extensions)

    report_event = premis.event(
        event_id=event_id, event_type="validation",
        event_date_time=datetime.datetime.now().isoformat(),
        event_detail="Digital object validation",
        child_elements=[outcome],
        linking_objects=[report_object], linking_agents=[report_agent])

    return report_event


def validation_report(sip_path,
                      catalog_path,
                      linking_sip_type,
                      linking_sip_id):
    """Format validation results to Premis report"""

    # Create PREMIS agent, only one agent is needed
    report_agent = create_report_agent()
    child_elements = [report_agent]
    object_list = set()
    for result in validation(mets_path=sip_path, catalog_path=catalog_path):
        metadata_info = result['metadata_info']
        # Create PREMIS object only if not already in the report
        if metadata_info['object_id']['value'] not in object_list:
            object_list.add(metadata_info['object_id']['value'])
            report_object = create_report_object(metadata_info,
                                                 linking_sip_type,
                                                 linking_sip_id)
            child_elements.append(report_object)
        report_event = create_report_event(result, report_object, report_agent)
        child_elements.append(report_event)

    return premis.premis(child_elements=child_elements)


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
