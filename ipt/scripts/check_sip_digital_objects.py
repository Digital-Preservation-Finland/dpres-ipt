#!/usr/bin/python
"""Validate all digital objects in a given METS document"""

from __future__ import print_function

import argparse
import datetime
import os
import sys
import uuid

import lxml.etree

import premis
import xml_helpers.utils
from file_scraper.scraper import Scraper

from ipt.validator.utils import iter_metadata_info
from ipt.validator.comparator import MetadataComparator
from ipt.utils import (concat, create_scraper_params,
                       ensure_text, get_scraper_info)

_FILE_SCRAPER_DETECTOR_CLASSES = ('FidoDetector', 'MagicDetector')


def main(arguments=None):
    """ The main method for check-sip-digital-objects script"""

    args = parse_arguments(arguments)
    report = validation_report(
        validation(args.sip_path),
        args.linking_sip_type,
        args.linking_sip_id)

    print(ensure_text(xml_helpers.utils.serialize(report)))

    if contains_errors(report):
        return 117

    return 0


def parse_arguments(arguments):
    """ Create arguments parser and return parsed command line argumets"""
    parser = argparse.ArgumentParser()
    parser.add_argument('sip_path', help='Path to information package')
    parser.add_argument('linking_sip_type', default=' ')
    parser.add_argument('linking_sip_id', default=' ')

    return parser.parse_args(arguments)


def contains_errors(report):
    events = report.findall('.//' + premis.premis_ns('eventOutcome'))
    for event in events:
        if event.text == 'failure':
            return True
    return False


def make_result_dict(is_valid, messages=[], errors=[], prefix=''):
    """ Create a result dict from a validation component output.

    :is_valid: Boolean describing the validation result.
    :messages: List of message strings obtained from a validation component.
    :errors: List of error strings obtained from a validation component.
    :prefix: Prefix string to prepend messages and errors with.
    :returns: A result_dict created from the arguments.
    """
    return {
        'is_valid': is_valid,
        'messages': concat(messages, prefix),
        'errors': concat(errors, prefix),
    }


def check_metadata_info(metadata_info):
    """
    Check if metadata was parsed correctly from mets, and add possible notes
    to messages.

    :metadata_info: Dictionary containing metadata parsed from mets.
    :returns: result_dict dictionary.
    """
    if metadata_info['errors']:
        return make_result_dict(
            is_valid=False,
            messages=['Failed parsing metadata, skipping validation.'],
            errors=[metadata_info["errors"]]
        )
    messages = []
    try:
        alt_format = metadata_info['format']['alt-format']
        messages.append('Found alternative format "{}", '
                        'but validating as "{}".'.format(
                            alt_format, metadata_info['format']['mimetype']))
    except KeyError:
        pass
    return make_result_dict(True, messages)


def skip_validation(metadata_info):
    """ File format validation is not done for native file formats. """
    return metadata_info['use'] == 'no-file-format-validation'


def check_well_formed(scraper):
    """
    Create result_dict from scraper results.

    :scraper: File-scraper object which must have already called scrape().
    :returns: result_dict dictionary.
    """
    messages, errors = get_scraper_info(scraper, filter_detectors=True)
    return make_result_dict(scraper.well_formed, messages, errors)


def check_metadata_match(metadata_info, scraper):
    """
    Compare mets metadata to scraper metadata using the
    MetadataComparator class.

    :metadata_info: Dictionary containing metadata parsed from mets.
    :scraper: File-scraper object which must have already called scrape().
    :returns: result_dict dictionary.
    """
    comparator = MetadataComparator(metadata_info, scraper)
    result = comparator.result()
    return make_result_dict(prefix='MetadataComparator: ', **result)


def join_validation_results(metadata_info, results):
    """
    Join multiple result_dicts obtained from different validation components
    into a single dictionary, which is used to create the validation report.

    :metadata_info: Dictionary containing metadata parsed from mets.
    :results: List of result_dicts.
    :returns: Dictionary which contains metadata_info and the aggregated
              validation results.
    """
    valids, messages, errors = [], [], []
    for result_dict in results:
        valids.append(result_dict['is_valid'])
        messages.append(result_dict['messages'])
        errors.append(result_dict['errors'])
    # Filter empty messages and errors
    messages = [msg for msg in messages if msg]
    errors = [err for err in errors if err]
    return {
        'metadata_info': metadata_info,
        'is_valid': all(valids),
        'messages': '\n'.join(messages),
        'errors': '\n'.join(errors),
    }


def validation(mets_path):
    """
    Validate all files enumerated in mets.xml files.

    :mets_path: Path to the directory which contains the mets.xml file
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
        3. Scrape metadata using file-scraper and check well-formedness.
        4. Check that mets metadata matches scraper metadata.

        :returns: Dictionary containing joined results from the above steps.
        """
        results = []
        results.append(check_metadata_info(metadata_info))
        if not results[0]['is_valid'] or skip_validation(metadata_info):
            return join_validation_results(metadata_info, results)
        scraper = Scraper(metadata_info['filename'],
                          **create_scraper_params(metadata_info))
        scraper.scrape()
        results.append(check_well_formed(scraper))
        results.append(check_metadata_match(metadata_info, scraper))
        return join_validation_results(metadata_info, results)

    mets_tree = None
    if mets_path is not None:
        if os.path.isdir(mets_path):
            mets_path = os.path.join(mets_path, 'mets.xml')
        mets_tree = xml_helpers.utils.readfile(mets_path)

    for metadata_info in iter_metadata_info(mets_tree, mets_path):
        yield _validate(metadata_info)


def validation_report(results, linking_sip_type, linking_sip_id):
    """ Format validation results to Premis report"""

    if results is None:
        raise TypeError

    # Create PREMIS agent, only one agent is needed
    # TODO: Agent could be the used validator instead of script file
    agent_name = "check_sip_digital_objects.py-v0.0"
    agent_id_value = 'preservation-agent-' + agent_name + '-' + \
                     str(uuid.uuid4())
    agent_id = premis.identifier(
        identifier_type='preservation-agent-id',
        identifier_value=agent_id_value, prefix='agent')
    report_agent = premis.agent(agent_id=agent_id, agent_name=agent_name,
                                agent_type='software')

    childs = [report_agent]
    object_list = set()
    for result in results:

        metadata_info = result['metadata_info']

        # Create PREMIS object only if not already in the report
        if metadata_info['object_id']['value'] not in object_list:
            object_list.add(metadata_info['object_id']['value'])

            dep_id = premis.identifier(
                metadata_info['object_id']['type'],
                metadata_info['object_id']['value'])
            environ = premis.environment(dep_id)

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

            childs.append(report_object)

        # Create PREMIS event
        event_id = premis.identifier(
            identifier_type="preservation-event-id",
            identifier_value=str(uuid.uuid4()), prefix='event')
        outresult = 'success' if result["is_valid"] is True else 'failure'
        detail_extension = None
        try:
            detail_extension = lxml.etree.fromstring(result["messages"])
            detail_note = result["errors"] if result["errors"] else None

        except lxml.etree.XMLSyntaxError:
            if result["errors"]:
                detail_note = (result["messages"] + '\n' + result["errors"])
            else:
                detail_note = result["messages"]

        outcome = premis.outcome(outcome=outresult, detail_note=detail_note,
                                 detail_extension=detail_extension)

        report_event = premis.event(
            event_id=event_id, event_type="validation",
            event_date_time=datetime.datetime.now().isoformat(),
            event_detail="Digital object validation",
            child_elements=[outcome],
            linking_objects=[report_object], linking_agents=[report_agent])

        childs.append(report_event)

    return premis.premis(child_elements=childs)


if __name__ == '__main__':
    RETVAL = main()
    sys.exit(RETVAL)
