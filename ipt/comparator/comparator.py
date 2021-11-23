"""
Module to compare metadata found in mets to metadata scraped by file-scraper.
"""

from __future__ import unicode_literals
import json

import six

from ipt.utils import (handle_div, synonymize_stream_keys,
                       pair_compatible_list_elements)


_ETAL_ALLOWED_KEYS = ('display_aspect_ratio',)
_AUDIOMD_INTEGER_VALUE_KEYS = ('data_rate',)
_METS_UNAVAILABLE_VALUES = ('(:unav)', '0')
_PDF_VERSION_SUBSETS = {'1.4': ('A-1a', 'A-1b'),
                        '1.7': ('A-2a', 'A-2b', 'A-2u',
                                'A-3a', 'A-3b', 'A-3u')}
_KNOWN_UNAV_VERSIONS = {
    "application/vnd.oasis.opendocument.text": ["1.0", "1.1", "1.2"],
    "application/vnd.oasis.opendocument.spreadsheet": [
        "1.0", "1.1", "1.2"],
    "application/vnd.oasis.opendocument.presentation": [
        "1.0", "1.1", "1.2"],
    "application/vnd.oasis.opendocument.graphics": ["1.0", "1.1", "1.2"],
    "application/vnd.oasis.opendocument.formula": ["1.0", "1.2"],
}


class MetadataComparator(object):
    """
    This class checks that mets metadata matches scraper metadata.
    First call to the result() method calls the _check_mets_matches_scraper()
    method, which goes through all relevant sections of the metadata_info
    dictionary. The checks for individual metadata_info sections are performed
    in methods starting with '_check', which may call other _check methods or
    helper functions.

    1. _check_format (always): compare mimetype and version
           _check_charset (text files only): compare character set
    2. _check_audio_or_video_streams (called for each of the following keys
           present in metadata_info:
           'audio', 'audio_streams', 'video', 'video_streams')
    """

    def __init__(self, metadata_info, scraper_streams):
        """Setup the metadata comparator object

        :metadata_info: A dictionary containing metadata info parsed from mets.
        :scraper: A scraper object which has conducted file scraping.
        """
        self._metadata_info = metadata_info
        self._scraper_streams = scraper_streams
        self._messages = []
        self._errors = []

    @property
    def is_valid(self):
        """
        Comparison result is valid when checks don't result in any error
        messages.
        """
        return not self._errors

    def messages(self):
        """Return comparison diagnostic messages"""
        return self._messages

    def errors(self):
        """Return comparison error messages"""
        return ['ERROR: ' + err for err in self._errors]

    def result(self):
        """Perform comparison if not already done and return the result."""
        if not any((self._messages, self._errors)):
            self._check_mets_matches_scraper()
            if self.is_valid:
                self._messages.append('METS metadata matches '
                                      'scraper metadata.')
        return {
            'is_valid': self.is_valid,
            'messages': self.messages(),
            'errors': self.errors(),
        }

    def _is_textfile(self):
        """Helper to check if the file is a text file according to scraper."""
        return self._scraper_streams[0]["stream_type"] == "text"

    def _add_error(self, info, mets_value, scraper_value):
        """
        Add an error describing what failed and which values were
        compared.
        """
        self._errors.append(info + '\nMETS: {},\nScraper: {}\n'.format(
                            json.dumps(mets_value, indent=4),
                            json.dumps(scraper_value, indent=4)))

    def _get_stream_format(self, stream_index):
        """
        Helper to get the part of a scraper stream which corresponds with the
        metadata_info['format'] dictionary.

        :stream_index: Index of the scraper stream.
        """
        stream = self._scraper_streams[stream_index]
        return {
            'mimetype': stream['mimetype'],
            'version': stream['version'],
        }

    def _check_mets_matches_scraper(self):
        """
        Check that the 'format' dictionary values in metadata_info match
        the values of the first scraper stream. If metadata_info contains
        a single audio or video stream ('audio' or 'video' key) or a
        video container with one or more streams ('audio_streams' and/or
        'video_streams' keys) check that they can be matched with scraper
        streams.
        """
        self._check_format()
        metadata_stream_types = set(self._metadata_info.keys()).intersection(
            {'audio', 'audio_streams', 'video', 'video_streams'})
        for stream_type in metadata_stream_types:
            self._check_audio_or_video_streams(stream_type)

    def _check_format(self):
        """
        Check that mimetype and version (and charset if textfile)
        in mets metadata matches metadata found by scraper.
        """
        mets_format = self._metadata_info['format']
        scraper_format = self._get_stream_format(0)
        is_textfile = self._is_textfile()

        if is_textfile:
            self._check_charset()
        if not _compare_mimetype_version(
                mets_format, scraper_format, is_textfile):
            self._add_error('Missing or incorrect mimetype/version.',
                            mets_format, scraper_format)

    def _check_charset(self):
        """
        Check that character set in mets matches what scraper found. If
        they do not match, add message (not an error, because scraper may
        guess wrong).
        """
        scraper_charset = self._scraper_streams[0].get('charset', None)
        mets_charset = self._metadata_info['format'].get('charset', None)
        if mets_charset != scraper_charset:
            self._messages.append(
                'METS and Scraper character sets do not match. METS: {} '
                'Scraper: {}'.format(mets_charset, scraper_charset))

    def _check_audio_or_video_streams(self, stream_type):
        """
        Prepare mets and scraper streams for comparison and try to match them.

        :stream_type: One of the following strings:
                      'audio', 'audio_streams', 'video', 'video_streams'
        """
        mets_streams = self._prepare_mets_av_streams(stream_type)
        stream_type = stream_type.split('_')[0]  # remove '_streams' part
        scraper_streams = self._prepare_scraper_av_streams(stream_type)

        is_match, notes = _match_streams(mets_streams, scraper_streams,
                                         stream_type)
        if is_match:
            self._messages += notes
        else:
            self._add_error(
                '{} streams in {} are not what is described in metadata.'
                .format(stream_type, self._metadata_info['filename']),
                mets_streams, scraper_streams)

    def _prepare_scraper_av_streams(self, stream_type):
        """
        Prepare a list of metadata_info-like dictionaries from scraper
        streams. Keep only streams of given type, handle divisions
        in values and convert scraper key names to match corresponding
        metadata_info keys.

        :stream_type: Either 'audio' or 'video'.
        :returns: List of metadata dictionaries prepared for comparison.
        """
        if stream_type not in ('audio', 'video'):
            raise ValueError('Invalid stream type {}'.format(stream_type))
        prepared_dicts = []
        for stream in six.itervalues(self._scraper_streams):
            if stream['stream_type'] != stream_type:
                continue
            md_info_style_dict = {}
            md_info_style_dict['format'] = \
                self._get_stream_format(stream['index'])
            _stream = {}
            for key, value in six.iteritems(stream):
                decimals = 2  # Round values to two decimals by default
                if stream_type == 'audio' and \
                        key in _AUDIOMD_INTEGER_VALUE_KEYS:
                    decimals = 0
                _stream[key] = handle_div(value, decimals)
            _stream = synonymize_stream_keys(_stream)
            md_info_style_dict[stream_type] = _stream
            prepared_dicts.append(md_info_style_dict)
        return prepared_dicts

    def _prepare_mets_av_streams(self, stream_type):
        """
        Get stream dicts of type stream_type from metadata_info into a list.
        See https://wiki.csc.fi/KDK/MetadataInfoInWorkflow

        :stream_type: One of the following strings:
                      'audio' or 'video' (single stream, not a video container)
                      'audio_streams' or 'video_streams' (one or more streams
                                                          in a video container)
        :returns: List of metadata dictionaries.
        """
        if stream_type in ('audio_streams', 'video_streams'):
            return self._metadata_info[stream_type]
        if stream_type in ('audio', 'video'):
            return [self._metadata_info]
        raise ValueError('Invalid stream type {}'.format(stream_type))


def _harmonized_versions(scraper_format):
    """
    Harmonize the set of file format versions found by file-scraper according
    to the specifications of the preservation service, i.e., the values that
    can be found in the METS document.

    :scraper_format: Dict with keys 'mimetype' and 'version' (from scraper).
    :returns: Set of harmonized versions.
    """
    harmonized_versions = set()
    # If scraper denotes version as unapplicable, empty string in METS is
    # expected.
    if scraper_format['version'] == '(:unap)':
        harmonized_versions.add('')
    # If scraper is unable to resolve version, we expect only values from
    # some file formats in a list.
    elif scraper_format['version'] in ['(:unav)', None]:
        # We handle (:unav) version result from Scraper only in known cases.
        # For other cases we leave harmonized_versions empty, which results
        # error.
        if _KNOWN_UNAV_VERSIONS.get(scraper_format['mimetype'], None):
            harmonized_versions.update(
                _KNOWN_UNAV_VERSIONS[scraper_format['mimetype']])
    # In the normal case the version in METS should be the same as the
    # version scraper found.
    else:
        harmonized_versions.add(scraper_format['version'])
    # PDF file special case:
    # If scraper finds a version which is a subset of the version given METS,
    # the more general METS value is allowed (e.g, METS: 1.4, scraper: A-1b)
    if scraper_format['mimetype'] == 'application/pdf':
        for super_version, sub_versions in six.iteritems(_PDF_VERSION_SUBSETS):
            if scraper_format['version'] in sub_versions:
                harmonized_versions.add(super_version)
    return harmonized_versions


def _compare_mimetype_version(mets_format, scraper_format, is_textfile=False):
    """
    Helper to check if mimetype and version in mets match scraper.

    :mets_format: Dict with keys 'mimetype' and 'version' (from mets).
    :scraper_format: Dict with keys 'mimetype' and 'version' (from scraper).
    :is_textfile: True if checking a text file.
    :returns: True iff mets mimetype and version match what scraper found.
    """
    matching_mimetypes = {scraper_format['mimetype']}
    # Subsets of text/plain (e.g., text/html) can be submitted as plaintext
    if is_textfile:
        matching_mimetypes.add('text/plain')
    return all((mets_format['mimetype'] in matching_mimetypes,
                mets_format['version'] in
                _harmonized_versions(scraper_format)))


def _match_streams(mets_streams, scraper_streams, stream_type):
    """
    Check that mets_streams can be paired perfectly with scraper_streams,
    so that each mets_stream and scraper_stream has a pair, and no stream
    is paired more than once.

    :mets_streams: List of prepared audio or video streams parsed from mets.
    :scraper_streams: List of prepared audio or video streams from scraper.
    :stream_type: Either 'audio' or 'video'.
    :returns: (is_match, notes); is_match = True iff all streams were paired
              successfully. Notes is a list of info about values listed as
              (:unav) or 0 in mets but for which scraper found actual values.
    """
    if stream_type not in ('audio', 'video'):
        raise ValueError('Invalid stream type {}'.format(stream_type))

    def _compare_stream_dicts(mets_stream, scraper_stream):
        """
        Helper to check if all key-value pairs in mets_stream can be found in
        scraper_stream, excluding some special cases.

        mets_stream: A prepared mets stream dictionary.
        scraper_stream: A prepared scraper stream dictionary.
        :returns: True iff mets_stream matches scraper_stream.
        """
        if not _compare_mimetype_version(
                mets_stream['format'], scraper_stream['format']):
            return False

        for key, mets_value in six.iteritems(mets_stream[stream_type]):
            try:
                scraper_value = scraper_stream[stream_type][key]
                if mets_value == scraper_value:
                    continue
                # Check special cases where value mismatch is allowed
                if mets_value in _METS_UNAVAILABLE_VALUES:
                    continue
                if scraper_value == '(:unav)':
                    continue
                if mets_value == '(:etal)' and key in _ETAL_ALLOWED_KEYS:
                    continue
                return False
            except KeyError:
                # Mets may contain keys that scraper does not find, this is ok
                pass
        return True

    index_pairs = pair_compatible_list_elements(mets_streams, scraper_streams,
                                                _compare_stream_dicts)

    if index_pairs:
        # Streams were matched successfully; add message for all cases where
        # mets had an unavailable value, but scraper found an actual value
        notes = []
        for mets_idx, scraper_idx in index_pairs:
            scraper_stream = scraper_streams[scraper_idx][stream_type]
            for key, mets_value in \
                    six.iteritems(mets_streams[mets_idx][stream_type]):
                try:
                    scraper_value = scraper_stream[key]
                    if mets_value != scraper_value and \
                            mets_value in _METS_UNAVAILABLE_VALUES:
                        notes.append('Found value for {} -- {}.'.format(
                            {key: mets_value}, {key: scraper_value}))
                except KeyError:
                    pass
        return (True, notes)
    # Streams could not be matched (or there were no streams, in which case
    # this function should not have been called at all)
    return (False, [])
