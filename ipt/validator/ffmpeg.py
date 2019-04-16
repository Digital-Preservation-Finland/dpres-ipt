""" This is a module that integrates ffmpeg and ffprobe tools with
information-package-tools for file validation purposes. Validation is
achieved by doing a conversion. If conversion is succesful, file is
interpred as a valid file. Container type is also validated with ffprobe.
"""

from six import itervalues, iteritems

from ipt.validator.basevalidator import BaseValidator
from ipt.utils import (handle_div, synonymize_stream_keys)

MPEG1 = {"version": None, "mimetype": "video/MP1S"}
MPEG2_TS = {"version": None, "mimetype": "video/MP2T"}
MPEG2_PS = {"version": None, "mimetype": "video/MP2P"}
MP3 = {"version": None, "mimetype": "audio/mpeg"}
MP4 = {"version": None, "mimetype": "video/mp4"}
RAW_AAC = {"version": None, "mimetype": "audio/mp4"}
RAW_MPEG = {"version": None, "mimetype": "video/mpeg"}
RAW_MPEG1 = {"version": "1", "mimetype": "video/mpeg"}
RAW_MPEG2 = {"version": "2", "mimetype": "video/mpeg"}

MPEG1_STRINGS = ["MPEG-1 video",
                 "MPEG-1 Systems / MPEG program stream",
                 "MPEG-1 Systems / MPEG program stream (VCD)"]
RAW_MPEG_STRINGS = ["raw MPEG video"]
RAW_MPEG1_STRINGS = ["raw MPEG-1 video"]
RAW_MPEG2_STRINGS = ["raw MPEG-2 video"]
MPEG2_TS_STRINGS = ["MPEG-2 transport stream format",
                    "MPEG-TS (MPEG-2 Transport Stream)",
                    "raw MPEG-TS (MPEG-2 Transport Stream)"]
MPEG2_PS_STRINGS = ["MPEG-PS format",
                    "MPEG-2 PS (DVD VOB)",
                    "MPEG-2 PS (VOB)",
                    "MPEG-PS (MPEG-2 Program Stream)",
                    "MPEG-2 PS (SVCD)"]
MP3_STRINGS = [
    "MPEG audio layer 2/3",
    "MP3 (MPEG audio layer 3)",
    "MP2/3 (MPEG audio layer 2/3)",
    "ADU (Application Data Unit) MP3 (MPEG audio layer 3)",
    "MP3onMP4",
    "libmp3lame MP3 (MPEG audio layer 3)",
    "libshine MP3 (MPEG audio layer 3)"]
MPEG4_STRINGS = ["M4A",
                 "MP4 (MPEG-4 Part 14)",
                 "QuickTime/MPEG-4/Motion JPEG 2000 format",
                 "QuickTime / MOV",
                 "raw H.264 video"]
RAW_AAC_STRINGS = ["raw ADTS AAC",
                   "raw ADTS AAC (Advanced Audio Coding)"]

CONTAINER_MIMETYPES = [
    {"data": MPEG1, "strings": MPEG1_STRINGS},
    {"data": MPEG2_TS, "strings": MPEG2_TS_STRINGS},
    {"data": MPEG2_PS, "strings": MPEG2_PS_STRINGS},
    {"data": MP3, "strings": MP3_STRINGS},
    {"data": MP4, "strings": MPEG4_STRINGS},
    {"data": RAW_AAC, "strings": RAW_AAC_STRINGS},
    {"data": RAW_MPEG, "strings": RAW_MPEG_STRINGS},
    {"data": RAW_MPEG1, "strings": RAW_MPEG1_STRINGS},
    {"data": RAW_MPEG2, "strings": RAW_MPEG2_STRINGS}
]

NOT_CONTAINERS = ['audio/mpeg', 'video/mpeg', 'audio/mp4']

STREAM_MIMETYPES = {
    "mpegvideo": "video/mpeg",
    "mpeg1video": "video/mpeg",
    "mpeg2video": "video/mpeg",
    "h264": "video/mp4",
    "libmp3lame": "audio/mpeg",
    "libshine": "audio/mpeg",
    "mp3": "audio/mpeg",
    "mp3adu": "audio/mpeg",
    "mp3adufloat": "audio/mpeg",
    "mp3float": "audio/mpeg",
    "mp3on4": "audio/mpeg",
    "mp3on4float": "audio/mpeg",
    "aac": "audio/mp4"
}


class FFMpeg(BaseValidator):
    """FFMpeg validator class."""

    # TODO: video/mp4 accepts various other formats too, such as 3gp
    _supported_mimetypes = {
        'video/mpeg': ['1', '2'],
        'audio/mpeg': ['1', '2'],
        'video/MP1S': [''],
        'video/MP2T': [''],
        'video/MP2P': [''],
        'audio/mp4': [''],
        'video/mp4': [''],
    }

    def validate(self):
        """validate file."""
        if not set(self.metadata_info.keys()).intersection(
                set(['audio', 'video', 'audio_streams', 'video_streams'])):
            self.errors('Stream metadata was not found.')
            return
        if 'audio' in self.metadata_info:
            self.check_streams('audio')
        if 'video' in self.metadata_info:
            self.check_streams('video')
        if 'audio_streams' in self.metadata_info:
            self.check_streams('audio_streams')
        if 'video_streams' in self.metadata_info:
            self.check_streams('video_streams')

    def check_streams(self, stream_type):
        """Check that streams inside container are what they are described in
        audioMD and videoMD. Ffprobe command gives a json output in the
        following format:

            "streams": [
            {
                "index": 0,
                "codec_name": "mpeg1video",
                "codec_long_name": "MPEG-1 video",
                "codec_type": "video",
                "codec_time_base": "1001/30000",
                "codec_tag_string": "[0][0][0][0]",
                "codec_tag": "0x0000",
                "width": 320,
                "height": 240,
                "has_b_frames": 1,
                "sample_aspect_ratio": "1:1",
                "display_aspect_ratio": "4:3",
                "pix_fmt": "yuv420p",
                "level": -99,
                "timecode": "00:00:00:00",
                "r_frame_rate": "30000/1001",
                "avg_frame_rate": "30000/1001",
                "time_base": "1/1200000",
                "duration": "19.025400"
            }

        :stream_type: "audio" or "video"
        """

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

        metadata_version = self.version if self.version else ''
        validation_failures = False
        if any((self.mimetype != self.scraper.mimetype,
                metadata_version != self.scraper.version)):
            self.errors(("Mimetype version mismatch. "
                         "Expected [%s: %s] in metadata, got [%s, %s]") % (
                            self.mimetype, metadata_version,
                            self.scraper.mimetype,
                            self.scraper.version))
            validation_failures = True
        if not _match_scraper_stream(metadata_streams, scraper_streams,
                                     stream_type):
            self.errors("Streams in %s are not what is "
                        "described in metadata. Found %s, expected %s" % (
                            self.metadata_info["filename"],
                            scraper_streams,
                            metadata_streams))
            validation_failures = True

        if not validation_failures:
            self.messages(
                "Streams %s are according to metadata description" %
                metadata_streams)


def get_version(mimetype, stream_data):
    """
    Solve version of file format.
    """
    if mimetype == 'audio/mpeg':
        if stream_data in ['32', '44.1', '48']:
            return '1'
        elif stream_data in ['16', '22.05', '24']:
            return '2'
    if mimetype == 'video/mpeg':
        if stream_data in ['mpegvideo', 'mpeg1video']:
            return '1'
        elif stream_data in ['mpeg2video']:
            return '2'
    return None


def parse_video_streams(stream):
    """Parse video streams from Scraper's stream output.

    :stream: Stream data in dict.
    :returns: parsed dict of video stream data.
    """
    new_stream = {"format": {'mimetype': stream.get('mimetype'),
                             'version': stream.get('version')},
                  "video": {}}

    if "bit_rate" in stream:
        new_stream["video"]["bit_rate"] = handle_div(stream.get("bit_rate"))
    if "avg_frame_rate" in stream:
        new_stream["video"]["avg_frame_rate"] = \
            handle_div(stream.get("avg_frame_rate"))
    if "display_aspect_ratio" in stream:
        new_stream["display_aspect_ratio"] = \
            handle_div(stream.get("display_aspect_ratio").replace(':', '/'))
    new_stream["video"]["width"] = str(stream.get("width"))
    new_stream["video"]["height"] = str(stream.get("height"))

    return new_stream


def parse_audio_streams(stream):
    """Parse audio streams from Scraper's stream output.

    :stream: Stream data in dict.
    :returns: parsed dict of audio stream data.
    """
    new_stream = {"format": {'mimetype': stream.get('mimetype'),
                             'version': stream.get('version')},
                  "audio": {}}

    new_stream["audio"]["bits_per_sample"] = stream.get("bits_per_sample")
    if "bit_rate" in stream:
        new_stream["audio"]["bit_rate"] = \
            str(int(stream.get("bit_rate")) / 1000)
    if "sample_rate" in stream:
        new_stream["audio"]["sample_rate"] = \
            handle_div(stream.get("sample_rate") + "/1000")
    new_stream["audio"]["channels"] = str(stream.get("channels"))

    return new_stream


STREAM_PARSERS = {
    "video": parse_video_streams,
    "audio": parse_audio_streams
}


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
