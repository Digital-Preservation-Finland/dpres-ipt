"""
Module to compare metadata found in mets to metadata scraped by file-scraper.
"""

import itertools
from six import iteritems, itervalues
from file_scraper.scraper import Scraper
from ipt.utils import handle_div, synonymize_stream_keys


_ETAL_ALLOWED_KEYS = ('display_aspect_ratio')
_INTEGER_VALUE_KEYS = ('data_rate')
_UNAVAILABLE_VALUES = ('(:unav)', '0')


class MetadataComparator(object):
    """
    This class checks that mets metadata matches scraper metadata.
    First call to the result() method calls the _perform_checks() method,
    which goes through all relevant sections of the metadata_info dictionary.
    The checks for individual metadata_info sections are performed in methods
    starting with '_check', which may call other _check methods or helper
    functions.

    1. _check_format (always): compare mimetype and version
           _check_charset (text files only): compare character set
    2. _check_addml (if 'addml' key exists in metadata_info)
    3. _check_audio_or_video_streams (called for each of the following keys
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
            self._perform_checks()
            if self.is_valid:
                self._messages.append('Mets metadata matches '
                                      'scraper metadata.')
        return {
            'is_valid': self.is_valid,
            'messages': self.messages(),
            'errors': self.errors(),
        }

    def _add_error(self, info, mets_value, scraper_value):
        """
        Add an error describing what failed and which values were
        compared.
        """
        self._errors.append(info + ' Mets: {}, Scraper: {}'.format(
            mets_value, scraper_value))

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

    def _perform_checks(self):
        self._check_format()
        metadata_stream_types = set(self._metadata_info.keys()).intersection(
            {'addml', 'audio', 'audio_streams', 'video', 'video_streams'})
        for stream_type in metadata_stream_types:
            if stream_type == 'addml':
                self._check_addml(self._metadata_info['addml'])
            else:
                self._check_audio_or_video_streams(stream_type)

    def _check_format(self):
        """
        Check that mimetype and version (and charset if textfile)
        in mets metadata matches metadata found by scraper.
        """
        mets_format = self._metadata_info['format']
        scraper_format = self._get_stream_format(0)
        is_textfile = Scraper(self._metadata_info['filename']).is_textfile()

        if is_textfile:
            self._check_charset()
        if not _compare_mimetype_version(
                mets_format, scraper_format, is_textfile):
            self._add_error('Missing or incorrect mimetype/version.',
                            mets_format, scraper_format)

    def _check_charset(self):
        """Check that character set in mets matches what scraper found."""
        scraper_charset = self._scraper_streams[0].get('charset', None)
        mets_charset = self._metadata_info['format'].get('charset', None)
        if mets_charset != scraper_charset:
            self._add_error('Character set mismatch.',
                            mets_charset, scraper_charset)

    def _check_addml(self, metadata_stream):
        # TODO implement addml comparison
        pass

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
        Modify scraper streams to resemble the metadata_info dictionary.
        Keep only streams of given type, handle divisions in values
        and convert key names to match corresponding metadata_info keys.

        :scraper_streams: Streams scraped by a file-scraper object.
        :stream_type: Either 'audio' or 'video'.
        :returns: List of metadata dictionaries prepared for comparison.
        """
        if stream_type not in ('audio', 'video'):
            raise ValueError('Invalid stream type {}'.format(stream_type))
        prepared_dicts = []
        for stream in itervalues(self._scraper_streams):
            if stream['stream_type'] != stream_type:
                continue
            _dummy_dict = {}
            _dummy_dict['format'] = self._get_stream_format(stream['index'])
            _stream = {}
            for key, value in iteritems(stream):
                decimals = 2  # Round values to two decimals by default
                if key in _INTEGER_VALUE_KEYS:
                    decimals = 0
                _stream[key] = handle_div(value, decimals)
            _stream = synonymize_stream_keys(_stream)
            _dummy_dict[stream_type] = _stream
            prepared_dicts.append(_dummy_dict)
        return prepared_dicts

    def _prepare_mets_av_streams(self, stream_type):
        """
        Get stream dicts of type stream_type from metadata_info into a list.

        :stream_type: One of the following strings:
                      'audio', 'audio_streams', 'video', 'video_streams'.
        :returns: List of metadata dictionaries.
        """
        if stream_type in ('audio_streams', 'video_streams'):
            return self._metadata_info[stream_type]
        if stream_type in ('audio', 'video'):
            return [self._metadata_info]
        raise ValueError('Invalid stream type {}'.format(stream_type))


def _compare_mimetype_version(mets_format, scraper_format, is_textfile=False):
    """
    Helper to check if mimetype and version in mets match scraper.

    :mets_format: Dict with keys 'mimetype' and 'version' (from mets).
    :scraper_format: Dict with keys 'mimetype' and 'version' (from scraper).
    :is_textfile: True if checking a text file.
    :returns: True iff mets mimetype and version match what scraper found.
    """
    ok_mimetypes = [scraper_format['mimetype']]
    ok_versions = [scraper_format['version']]
    # Subsets of text/plain (e.g., text/html) can be submitted as plaintext
    if is_textfile:
        ok_mimetypes.append('text/plain')
    # If scraper does not find a version, empty string in mets is ok
    if scraper_format['version'] in ('(:unav)', '(:unap)', '', None):
        ok_versions.extend(['(:unap)', ''])
    return all((mets_format['mimetype'] in ok_mimetypes,
                mets_format['version'] in ok_versions))


def _match_streams(mets_streams, scraper_streams, stream_type):
    """
    Check that mets contains as many streams as scraper found, and that every
    stream in mets matches some scraper stream.

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
        if not _compare_mimetype_version(mets_stream['format'],
                                         scraper_stream['format']):
            return False

        for key, mets_value in iteritems(mets_stream[stream_type]):
            try:
                scraper_value = scraper_stream[stream_type][key]
                if mets_value == scraper_value:
                    continue
                # Check special cases where value mismatch is allowed
                if mets_value in _UNAVAILABLE_VALUES:
                    notes.append('Found value for {} -- {}.'.format(
                        {key: mets_value}, {key: scraper_value}))
                    continue
                if scraper_value in _UNAVAILABLE_VALUES:
                    continue
                if mets_value == '(:etal)' and key in _ETAL_ALLOWED_KEYS:
                    continue
                return False
            except KeyError:
                # Mets may contain keys that scraper does not find, this is ok
                pass
        return True

    # Number of streams must match
    if len(mets_streams) != len(scraper_streams):
        return (False, [])

    # Try to pair each mets stream with one scraper stream.
    # NOTE This is a brute-force algorithm which tries every possible
    # pairing combination (O(n!) time complexity). Typically the number of
    # streams is small, so this should not be a problem.
    # TODO Special handling for cases when there are too many streams,
    # or implement a completely different smarter algorithm?
    for mets_perm in itertools.permutations(mets_streams):
        notes = []
        if all([_compare_stream_dicts(mets_stream, scraper_stream)
                for mets_stream, scraper_stream in
                zip(mets_perm, scraper_streams)]):
            return (True, notes)
    # All combinations tried, could not match the streams. Notes are only
    # useful if the streams were matched successfully, so return empty list.
    return (False, [])
