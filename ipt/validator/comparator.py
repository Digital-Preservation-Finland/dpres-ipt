"""Module to compara metadata found in mets to metadata scraped by
file-scraper.
"""

from six import iteritems, itervalues
from ipt.utils import handle_div, synonymize_stream_keys, concat


class MetadataComparator(object):
    """This class performs the metadata comparison between mets and scraper
    output."""

    def __init__(self, metadata_info, scraper):
        """Setup the metadata comparator object

        :metadata_info: A dictionary containing metadata info parsed from mets.
        :scraper: A scraper object which has conducted file scraping.
        """
        self.metadata_info = metadata_info
        self._messages = []
        self._errors = []
        self._scraper = scraper

    @property
    def is_valid(self):
        """Comparison result is valid when there are no error messages and
        scraped data is well formed.
        """
        return all((not self._errors,
                    self._scraper.well_formed))

    def messages(self):
        """Return comparison diagnostic messages"""
        return concat(self._messages)

    def errors(self):
        """Return comparison error messages"""
        return concat(self._errors, 'ERROR: ')

    def result(self):
        """Return the comparison result."""
        if not any((self._messages, self._errors)):
            self._check_format()
            self._check_streams()

        return {
            'is_valid': self.is_valid,
            'messages': self.messages(),
            'errors': self.errors(),
        }

    def _check_format(self):
        """Check that the mimetype and version number found by
        scraper match mets metadata.
        """
        metadata_mimetype = self.metadata_info['format']['mimetype']
        metadata_version = self.metadata_info['format']['version']

        if not metadata_mimetype:
            self._errors.append('Mimetype not found in metadata.')
        elif metadata_mimetype == self._scraper.mimetype and \
                metadata_version in ('', self._scraper.version):
            self._messages.append('Mimetype and version ok.')
        else:
            self._errors.append(
                'Mimetype and version mismatch. '
                'Expected ["{}", "{}"], found ["{}", "{}"]'
                .format(metadata_mimetype, metadata_version,
                        self._scraper.mimetype, self._scraper.version))

    def _check_streams(self):
        found_stream_types = set(self.metadata_info.keys()).intersection(
            set(['audio', 'video', 'audio_streams', 'video_streams']))
        for stream_type in found_stream_types:
            self._check_audio_or_video_stream(stream_type)

    def _check_audio_or_video_stream(self, stream_type):
        """Modifies scraper output streams into a scraper_streams dict, which
        follows the same formatting as the metadata_info dict. Then
        checks that matching value for each metadata_info entry is also found
        in scraper_streams.
        """
        if stream_type == 'audio_streams':
            metadata_streams = self.metadata_info[stream_type]
            stream_type = 'audio'
        elif stream_type == 'video_streams':
            metadata_streams = self.metadata_info[stream_type]
            stream_type = 'video'
        else:
            metadata_streams = [self.metadata_info]

        scraper_streams = []
        for stream in itervalues(self._scraper.streams):
            _dummy_dict = {}
            stream = synonymize_stream_keys(stream)
            _dummy_dict['format'] = {
                'mimetype': stream.pop('mimetype', self._scraper.mimetype),
                'version': stream.pop('version', self._scraper.version)
            }
            _dummy_dict[stream_type] = stream
            scraper_streams.append(_dummy_dict)

        if not _match_scraper_stream(metadata_streams, scraper_streams,
                                     stream_type):
            # TODO Add clearer error message specifying exactly which values
            # did not match?
            self._errors.append(
                'Streams in {} are not what is '
                'described in metadata. Found {}, expected {}'.format(
                    self.metadata_info['filename'],
                    scraper_streams,
                    metadata_streams))


def _match_scraper_stream(metadata_streams, scraper_streams, s_type):
    """Helper function to help us determine that the stream data of metadata
    is found among scraper_streams.

    :param metadata_streams: The stream that we'll compare to scraper stream.
    :param scraper_streams: The stream to be compared at.
    :param s_type: Which stream type are we handling.
    :return: True if metadata stream information can be found in scraper streams.
    """

    def _match_to(metadata_collection, scraper_collection):
        """Helper to make the if-condition readable.

        :param metadata_collection: Collection to use to compare to.
        :param scraper_collection: Collection to compare against.
        :return: True if metadata_collection information can be found in
            scraper_collection.
        """
        try:
            return all((
                value == handle_div(scraper_collection[key]) for key, value in
                iteritems(metadata_collection)
            ))
        except KeyError:
            return False

    matched_indexes = set()  # To keep tabs which items were matched.
    for metadata_stream in metadata_streams:
        for i, stream in enumerate(scraper_streams):
            if _match_to(metadata_stream[s_type],
                         stream[s_type]) and i not in matched_indexes:
                # All values are a match, we break out from the stream loop.
                matched_indexes.add(i)
                break
        else:
            # The whole stream has been traversed and none of them matched.
            break
    else:
        # We'll reach here only if scraper stream loop didn't break
        # therefore signifying success of matching and for final check.
        # The number of unique matches must match with length of metadata.
        return len(matched_indexes) == len(metadata_streams)
    return False
