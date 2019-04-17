"""General interface for building a file validator plugin. """
import abc
import subprocess

from file_scraper.iterator import iter_scrapers
from six import iteritems, itervalues

from ipt.utils import run_command, handle_div, synonymize_stream_keys


class ValidatorError(Exception):
    """Unrecoverable error in validator"""
    pass


class Shell(object):
    """Docstring for ShellTarget. """

    def __init__(self, command, output_file=subprocess.PIPE, env=None):
        """Initialize instance.

        :command: Command to execute as list
        """
        self.command = command

        self._stdout = None
        self._stderr = None
        self._returncode = None
        self.output_file = output_file
        self.env = env

    @property
    def returncode(self):
        """Returncode from the command

        :returns: Returncode

        """
        return self.run()["returncode"]

    @property
    def stderr(self):
        """Standard error output from the command

        :returns: Stdout as string

        """
        return self.run()["stderr"]

    @property
    def stdout(self):
        """Command standard error output.

        :returns: Stderr as string

        """
        return self.run()["stdout"]

    def run(self):
        """Run the command and store results to class attributes for caching.

        :returns: Returncode, stdout, stderr as dictionary

        """
        if self._returncode is None:
            (self._returncode, self._stdout,
             self._stderr) = run_command(
                cmd=self.command, stdout=self.output_file,
                env=self.env)

        return {
            'returncode': self._returncode,
            'stderr': self._stderr,
            'stdout': self._stdout
        }


class BaseValidator(object):
    """This class introduces general interface for file validator plugin which
    every validator has to satisfy. This class is meant to be inherited and to
    use this class at least exec_cmd and filename variables has to be set.
    """

    __metaclass__ = abc.ABCMeta
    _supported_mimetypes = None

    validator_info = None

    def __init__(self, metadata_info, scraper_obj=None):
        """Setup the base validator object"""

        self.metadata_info = metadata_info
        self._messages = []
        self._errors = []
        self._scraper = scraper_obj
        self.validator_info = {'filename': metadata_info['filename'],
                               'format': {}}

    @classmethod
    def is_supported(cls, metadata_info):
        """Return True if this validator class supports digital object with
        given metadata_info record.

        Default implementation checks the mimetype and version. Other
        implementations may override this for other selection criteria"""

        mimetype = metadata_info['format']['mimetype']
        version = metadata_info['format']['version']

        return mimetype in cls._supported_mimetypes and \
               version in cls._supported_mimetypes[mimetype]

    def messages(self, message=None):
        """Return validation diagnostic messages"""
        if message is not None:
            self._messages.append(message)
        return concat(self._messages)

    def errors(self, error=None):
        """Return validation error messages"""
        if error is not None and error != "":
            self._errors.append(error)
        return concat(self._errors, 'ERROR: ')

    @property
    def filename(self):
        """Shorthand for returning given metadata's filename.
        :return: String
        """
        return self.metadata_info['filename']

    @property
    def mimetype(self):
        """Shorthand for returning given metadata's mimetype.
        :return: String
        """
        return self.metadata_info['format']['mimetype']

    @property
    def version(self):
        """Shorthand for returning given metadata's version.
        :return: String
        """
        return self.metadata_info['format']['version']

    @property
    def scraper(self):
        """Returns the data that would be used to validate against.

        :return: Stored dictionary data.
        """
        return self._scraper

    @scraper.setter
    def scraper(self, scraper_obj):
        """Object to be set and validated against. The objectis expected to be
        a file-scraper's Scraper-object that has conducted its scraping already.

        :param value: Scraper's data in dict.
        """
        self._scraper = scraper_obj

    @property
    def is_valid(self):
        """Validation result is valid when there are no error messages and
        scraped data is well formed.
        """
        return all((not self._errors,
                    self.scraper.well_formed))

    @property
    def is_valid_mimetype(self):
        """Validates the current defined mimetype and version to the scraper's
        discovered mimetype and version.
        """
        metadata_version = self.version if self.version else ''
        if any((self.mimetype != self.scraper.mimetype,
                metadata_version != self.scraper.version)):
            return False
        return True

    def iter_related_scrapers(self):
        """Iterates through all relevant scrapers based on the provided
        metadata.
        """
        for scraper_cls in iter_scrapers(self.mimetype, self.version):
            yield scraper_cls

    def result(self):
        """Return the validation result"""

        if len(self._messages) == 0:
            self.validate()

        return {
            'is_valid': self.is_valid,
            'messages': self.messages(),
            'errors': self.errors()
        }

    def validate_mimetype(self):
        """Validates the current defined mimetype and version to the scraper's
        discovered mimetype and version.
        :return: True if no mimetype matches,
            else False and then logs a message to errors.
        """
        if not self.is_valid_mimetype:
            metadata_version = self.version if self.version else ''
            self.errors(("Mimetype version mismatch. "
                         "Expected [%s: %s] in metadata, got [%s, %s]") % (
                            self.mimetype, metadata_version,
                            self.scraper.mimetype,
                            self.scraper.version))
            return False
        return True

    @abc.abstractmethod
    def validate(self):
        """All validator classes must implement the validate() method"""
        pass


class VideoAudioStreamValidatorMixin:
    """Mixin class to validate the video and audio stream """

    def validate_stream(self, stream_type):
        if stream_type in self.metadata_info:
            if stream_type == 'audio_streams':
                metadata_streams = self.metadata_info[stream_type]
                stream_type = 'audio'
            elif stream_type == 'video_streams':
                metadata_streams = self.metadata_info[stream_type]
                stream_type = 'video'
            else:
                metadata_streams = [self.metadata_info]
        else:
            metadata_streams = [self.metadata_info]

        scraper_streams = []
        for stream in itervalues(self.scraper.streams):
            _dummy_dict = {}
            stream = synonymize_stream_keys(stream)
            _dummy_dict['format'] = {
                'mimetype': stream.pop('mimetype', self.scraper.mimetype),
                'version': stream.pop('version', self.scraper.version)
            }
            _dummy_dict[stream_type] = stream
            scraper_streams.append(_dummy_dict)

        if _match_scraper_stream(metadata_streams, scraper_streams,
                                 stream_type):
            return True

        self.errors("Streams in %s are not what is "
                    "described in metadata. Found %s, expected %s" % (
                        self.metadata_info["filename"],
                        scraper_streams,
                        metadata_streams))
        return True


def concat(lines, prefix=""):
    """Join given list of strings to single string separated with newlines.

    :lines: List of string to join
    :prefix: Prefix to prepend each line with
    :returns: Joined lines as string

    """
    return "\n".join(["%s%s" % (prefix, line) for line in lines])


def _match_scraper_stream(metadata_streams, scraper_streams, s_type):
    """Helper function to help us determine that the stream data of metadata
    is found among scraper_streams.

    :param metadata_streams: The stream that we'll compare to scraper stream.
    :param scraper_streams: The stream to be compared at.
    :param s_type: Which stream type are we handling.
    :return: True if metadata stream information can be found in scraper stream.
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
