"""
MetadataComparator tests. This module checks that the comparison results
are as expected, using mocked metadata_info and scraper streams dicts.
Only valid scraper streams are used, since the comparison will be skipped
for non-well-formed objects in the check-sip-digital-objects script.

The tests check the dictionary returned by the result() method to ensure that:
    - When metadata_info contains all required values and they match the
      scraper streams, the comparison result should be valid.
    - If scraper finds a value for a key which is listed as unavailable in mets
      ('0' or '(:unav)'), the found value must be included in a message.
    - If mets has the value '(:etal)' in some of the keys for which this is
      allowed, the scraper value should be ignored (and result still be valid).
    - If mets and scraper values do not match for some key and it is not one of
      the special cases listed above, the result should be invalid.
"""


from copy import deepcopy
import pytest
from file_scraper.scraper import Scraper
from ipt.comparator.comparator import MetadataComparator
from ipt.utils import concat

METADATA_INFO = {
    'valid_text': {
        'filename': 'textfile',
        'format': {'charset': 'UTF-8',
                   'mimetype': 'text/plain',
                   'version': ''}},
    'valid_office': {
        'filename': 'officefile',
        'format': {'mimetype': 'application/vnd.oasis.opendocument.text',
                   'version': '1.0'}},
    'valid_image': {
        'filename': 'imagefile',
        'format': {'mimetype': 'image/jpeg',
                    'version': '1.02'}},
    'valid_audio': {
        'filename': 'audiofile',
        'format': {'mimetype': 'audio/x-wav',
                    'version': ''},
        'audio': {'bit_rate': '706',
                  'bits_per_sample': '8',
                  'channels': '2',
                  'sample_rate': '44.1'}},
    'valid_video': {
        'filename': 'videocontainer',
        'format': {'mimetype': 'video/mp4', 'version': ''},
        'audio_streams': [{'format': {'mimetype': 'audio/aac',
                                      'version': ''},
                           'audio': {'bit_rate': '135',
                                     'channels': '2',
                                     'sample_rate': '44.1'}},
                          {'format': {'mimetype': 'audio/aac',
                                      'version': ''},
                           'audio': {'bit_rate': '135',
                                     'channels': '4',
                                     'sample_rate': '48'}}],
        'video_streams': [{'format': {'mimetype': 'video/h264',
                                      'version': ''},
                           'video': {'avg_frame_rate': '30',
                                     'bit_rate': '0.05',
                                     'display_aspect_ratio': '1.78',
                                     'height': '180',
                                     'width': '320'}}]},
}


SCRAPER_STREAMS = {
    'valid_text': {
        0: {'charset': 'UTF-8',
            'index': 0,
            'mimetype': 'text/plain',
            'stream_type': 'text',
            'version': '(:unap)'}},
    'valid_office': {
        0: {'index': 0,
            'mimetype': 'application/vnd.oasis.opendocument.text',
            'stream_type': 'binary',
            'version': '(:unav)'}},
    'valid_image': {
        0: {'bps_unit': 'integer',
            'bps_value': '8',
            'colorspace': 'srgb',
            'compression': 'jpeg',
            'height': '300',
            'index': 0,
            'mimetype': 'image/jpeg',
            'samples_per_pixel': '3',
            'stream_type': 'image',
            'version': '1.02',
            'width': '400'}},
    'valid_audio': {
        0: {'audio_data_encoding': 'PCM',
            'bits_per_sample': '8',
            'codec_creator_app': 'Lavf56.40.101',
            'codec_creator_app_version': '56.40.101',
            'codec_name': 'PCM',
            'codec_quality': 'lossless',
            'data_rate': '705.6',
            'data_rate_mode': 'Fixed',
            'duration': 'PT0.86S',
            'index': 0,
            'mimetype': 'audio/x-wav',
            'num_channels': '2',
            'sampling_frequency': '44.1',
            'stream_type': 'audio',
            'version': '(:unap)'}},
    'valid_video': {
        0: {'codec_creator_app': 'Lavf56.40.101',
            'codec_creator_app_version': '56.40.101',
            'codec_name': 'MPEG-4',
            'index': 0,
            'mimetype': 'video/mp4',
            'stream_type': 'videocontainer',
            'version': '(:unap)'},
        1: {'bits_per_sample': '8',
            'codec_creator_app': 'Lavf56.40.101',
            'codec_creator_app_version': '56.40.101',
            'codec_name': 'AVC',
            'codec_quality': 'lossy',
            'color': 'Color',
            'dar': '1.778',
            'data_rate': '0.048704',
            'data_rate_mode': 'Variable',
            'duration': 'PT1S',
            'frame_rate': '30',
            'height': '180',
            'index': 1,
            'mimetype': 'video/h264',
            'par': '1',
            'sampling': '4:2:0',
            'signal_format': '(:unap)',
            'sound': 'Yes',
            'stream_type': 'video',
            'version': '(:unap)',
            'width': '320'},
        2: {'audio_data_encoding': 'AAC',
            'bits_per_sample': '(:unav)',
            'codec_creator_app': 'Lavf56.40.101',
            'codec_creator_app_version': '56.40.101',
            'codec_name': 'AAC',
            'codec_quality': 'lossy',
            'data_rate': '135.233',
            'data_rate_mode': 'Fixed',
            'duration': 'PT0.86S',
            'index': 2,
            'mimetype': 'audio/aac',
            'num_channels': '4',
            'sampling_frequency': '48',
            'stream_type': 'audio',
            'version': '(:unap)'},
        3: {'audio_data_encoding': 'AAC',
            'bits_per_sample': '(:unav)',
            'codec_creator_app': 'Lavf56.40.101',
            'codec_creator_app_version': '56.40.101',
            'codec_name': 'AAC',
            'codec_quality': 'lossy',
            'data_rate': '135.233',
            'data_rate_mode': 'Fixed',
            'duration': 'PT0.86S',
            'index': 3,
            'mimetype': 'audio/aac',
            'num_channels': '2',
            'sampling_frequency': '44.1',
            'stream_type': 'audio',
            'version': '(:unap)'}},
}

# The default result message if comparison does not find any errors.
DEFAULT_VALID_MESSAGE = 'METS metadata matches scraper metadata.'

VALID_TEST_CASES = [
    {'reason': 'Valid plaintext must pass.',
     'base': 'valid_text'},
    {'reason': 'Valid office must pass even with scraper (:unav) version.',
     'base': 'valid_office'},
    {'reason': 'Valid non-plaintext must pass.',
     'base': 'valid_image'},
    {'reason': 'Valid single-stream file must pass.',
     'base': 'valid_audio'},
    {'reason': 'Valid video container with multiple streams must pass.',
     'base': 'valid_video'},
    {'reason': 'Check that (:etal) value in allowed key is accepted.',
     'base': 'valid_video',
     'md_patch': [
         ['video_streams', 0, 'video', 'display_aspect_ratio', '(:etal)']]},
    {'reason': 'If scraper finds value for mets (:unav), it must be reported.',
     'base': 'valid_audio',
     'md_patch': [['audio', 'channels', '(:unav)']],
     'expected_message': "Found value for {'channels': '(:unav)'} "
                         "-- {'channels': '2'}."},
    {'reason': 'Check that mismatching character sets are reported.',
     'base': 'valid_text',
     'md_patch': [['format', 'charset', 'UTF-16']],
     'expected_message': 'METS and Scraper character sets do not match.'},
]

INVALID_TEST_CASES = [
    {'reason': 'Mimetype is always required in mets.',
     'base': 'valid_text',
     'md_patch': [['format', {'mimetype': None, 'version': None}]],
     'expected_error': 'Missing or incorrect mimetype/version.'},
    {'reason': 'Version is required except when scraper results (:unap).',
     'base': 'valid_image',
     'md_patch': [['format', 'version', '']],
     'expected_error': 'Missing or incorrect mimetype/version.'},
    {'reason': 'Check that mismatching stream value is caught.',
     'base': 'valid_video',
     'md_patch': [['audio_streams', 0, 'audio', 'bit_rate', 200]],
     'expected_error': ('audio streams in {} are not what is described '
                        'in metadata'.format(
                            METADATA_INFO['valid_video']['filename']))},
    {'reason': 'File format version is not allowed to be (:unav) in METS',
     'base': 'valid_office',
     'md_patch': [['format', 'version', '(:unav)']],
     'expected_error': 'Missing or incorrect mimetype/version'}
]


def patch_dict(original, patches):
    """Create a copy of a dictionary and replace values according to patches.

    :original: The dictionary to be copied and modified.
    :patches: A list of patches. Each patch is a list of keys to follow,
              and the last value is the new value.

    For example:
    original = {'format': {'mimetype': 'audio/x-wav',
                           'version': ''},
                'audio': {'bit_rate': '706',
                          'bits_per_sample': '8',
                          'channels': '2',
                          'sample_rate': '44.1'}}
    patches = [['format', 'mimetype', 'text/plain'],
               ['audio', 'channels', 1337]]
    patch_dict(original, patches) retuns:
               {'format': {'mimetype': 'text/plain',
                           'version': ''},
                'audio': {'bit_rate': '706',
                         'bits_per_sample': '8',
                         'channels': '1337',
                         'sample_rate': '44.1'}}
    :returns: The patched dictionary.
    """
    patched_dict = deepcopy(original)
    for patch in patches:
        value = patch[-1]
        current = patched_dict
        for key in patch[:-2]:
            current = current[key]
        current[patch[-2]] = value
    return patched_dict


def _is_textfile(self):
    return self.filename == 'textfile'


@pytest.mark.parametrize('test_params', VALID_TEST_CASES,
                         ids=[case['reason'] for case in VALID_TEST_CASES])
def test_valid_result(test_params, monkeypatch):
    """Test valid input for the comparator function"""
    monkeypatch.setattr(Scraper, 'is_textfile', _is_textfile)
    base = test_params['base']
    scraper_streams = SCRAPER_STREAMS[base]
    metadata_info = METADATA_INFO[base]
    try:
        metadata_info = patch_dict(metadata_info, test_params['md_patch'])
    except KeyError:
        pass

    comparator = MetadataComparator(metadata_info, scraper_streams)
    result = comparator.result()

    expected_message = test_params.get('expected_message',
                                       DEFAULT_VALID_MESSAGE)
    assert not result['errors']
    assert expected_message in concat(result['messages'])
    assert result['is_valid']


@pytest.mark.parametrize('test_params', INVALID_TEST_CASES,
                         ids=[case['reason'] for case in INVALID_TEST_CASES])
def test_invalid_result(test_params, monkeypatch):
    """Test invalid input for the comparator function"""

    monkeypatch.setattr(Scraper, 'is_textfile', _is_textfile)
    base = test_params['base']
    scraper = SCRAPER_STREAMS[base]
    metadata_info = METADATA_INFO[base]
    try:
        metadata_info = patch_dict(metadata_info, test_params['md_patch'])
    except KeyError:
        pass

    comparator = MetadataComparator(metadata_info, scraper)
    result = comparator.result()

    expected_error = test_params['expected_error']
    assert expected_error in concat(result['errors'])
    assert not result['is_valid']
