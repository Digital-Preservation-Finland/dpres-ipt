"""
Utility functions.
"""

import urllib
from collections import defaultdict
from copy import deepcopy
from fractions import Fraction

import six

import mimeparse
_SCRAPER_PARAM_ADDML_KEY_RELATION = (('fields', 'header_fields'),
                                     ('separator', 'separator'),
                                     ('delimiter', 'delimiter'))

_FFMPEG_FILE_SCRAPER_KEY_SYNONYMS = (('frame_rate', 'avg_frame_rate'),
                                     ('data_rate', 'bit_rate'),
                                     ('dar', 'display_aspect_ratio'),
                                     ('num_channels', 'channels'),
                                     ('sampling_frequency', 'sample_rate'))


class UnknownException(Exception):
    """Unknown error."""
    pass


class ValidationException(Exception):
    """Validator error."""
    pass


def merge_dicts(*dicts):
    """
    Merge N dictionaries. List and dict type elements with same key will be
    merged. Elements of other type cannot be merged. If value of an element is
    None, it will be overwritten by value from other dictionary with the same
    key.
    :dicts: a list of dicts.
    :returns: one merged dict
    """
    result = {}
    for dictionary in dicts:
        if not dictionary:
            continue
        for key in dictionary.keys():
            if key in result:
                if isinstance(result[key], dict) and \
                        isinstance(dictionary[key], dict):
                    result[key] = merge_dicts(result[key], dictionary[key])
                elif isinstance(result[key], list) and \
                        isinstance(dictionary[key], list):
                    result[key] = result[key] + dictionary[key]
                elif result[key] is None:
                    result[key] = dictionary[key]
                elif dictionary[key] is None:
                    continue
                else:
                    raise TypeError(
                        'Only lists and dictionaries can be merged.')
            else:
                result[key] = dictionary[key]
    return result


def compare_lists_of_dicts(expected, found):
    """
    :excpected: a list of dicts that should be in second 'found' parameter
    :found: a list of dicts that really exist
    :returns: a tuple describing missing and extraneus dicts
    """
    expected_count = dict(count_items_in_dict(expected))
    found_count = dict(count_items_in_dict(found))
    if found_count != expected_count:
        return False
    return True


def count_items_in_dict(expected):
    """
    :excpected: a list of dicts that should be in second 'found' paramater
    :returns: a dict that contains a count of each item
    """
    serialized_dicts = []
    if not expected:
        return {}
    for item in expected:
        serialized_dicts.append(serialize_dict(item))

    count = defaultdict(int)
    for item in serialized_dicts:
        count[item] += 1

    return count


def serialize_dict(data):
    """
    serialize dict to string
    :data: a dict.
    :returns: a list of strings containing dict values
    in format <key value>__<key value>
    """
    serialized_dict = ""
    if data:
        for key in sorted(list(data)):
            serialized_dict = serialized_dict + "%s=%s  " % (key, data[key])
    return serialized_dict.strip("  ")


def uri_to_path(uri):
    """Remove URI scheme from given `URI`:

    file://kuvat/PICT0081.JPG -> kuvat/PICT0081.JPG

    :uri: URI as string
    :returns: Relative path as string

    """
    uri = uri.encode("utf-8") if six.PY2 else uri
    path = urllib.unquote_plus(uri).replace('file://', '')
    return path.lstrip('./')


def parse_mimetype(mimetype):
    """Parse mimetype information from Content-type string.

    ..seealso:: https://www.ietf.org/rfc/rfc2045.txt
    """
    result = {"format": {}}
    # If the mime type can't be parsed, add the erroneous-mimetype item, which
    # can be checked when selecting validators. We need the original mimetype
    # for the error message printed by the UnknownFileformat validator.
    try:
        result_mimetype = mimeparse.parse_mime_type(mimetype)
    except mimeparse.MimeTypeParseException:
        result["format"]["erroneous-mimetype"] = True
        result["format"]["mimetype"] = mimetype
        return result

    params = result_mimetype[2]
    charset = params.get('charset')
    alt_format = params.get('alt-format')
    result["format"]["mimetype"] = (result_mimetype[0] + "/" +
                                    result_mimetype[1])
    if charset:
        result["format"]["charset"] = charset
    if alt_format:
        result["format"]["alt-format"] = alt_format

    return result


def handle_div(div, decimals=2):
    """
    Change a string containing a division or a decimal number to a
    string containing a decimal number with max <decimals> decimals.
    Returns original string if ValueError of ZeroDivisionError raised.
    :div: e.g. "16/9" or "1.7777778"
    :returns: e.g. "1.78"
    """
    try:
        div = float(Fraction(div))
        return ("%.2f" % round(div, decimals)).rstrip('0').rstrip('.')
    except (ValueError, ZeroDivisionError):
        return div


def find_max_complete(list1, list2, forcekeys=None):
    """
    Finds such version in two lists of dicts, where all the elements in all
    dicts exists. Handles also sublists inside dicts and subdicts inside dicts
    and sublists recursively. In other words, removes such elements that do not
    exist in one or more of the given dicts.
    :list1: List of dicts
    :list2: List of dicts
    :forcekeys: List of those keys which will not be changed or removed, if
                exists
    :returns: Filtered list1 and list2
    """
    included_keys = {}
    if list1 is None:
        list1 = []
    if list2 is None:
        list2 = []
    if list1:
        included_keys['root_key'] = set(list1[0])
    elif list2:
        included_keys['root_key'] = set(list2[0])
    else:
        return (list1, list2)
    included_keys = _find_keys(list1=list1, list2=list2,
                               included_keys=included_keys,
                               parent_key='root_key')
    return _filter_dicts(list1=deepcopy(list1), list2=deepcopy(list2),
                         included_keys=included_keys, parent_key='root_key',
                         forcekeys=forcekeys)


def _find_keys(list1, list2, included_keys, parent_key):
    """
    Recursive function for find_max_complete.
    Finds keys for each dicts and subdicts.
    """
    if parent_key not in included_keys:
        if list1:
            included_keys[parent_key] = set(list1[0].keys())
        elif list2:
            included_keys[parent_key] = set(list2[0].keys())
        else:
            included_keys[parent_key] = set([])

    for dictionary in list1 + list2:
        if not isinstance(dictionary, dict):
            continue
        included_keys[parent_key] = included_keys[parent_key]. \
            intersection(set(dictionary.keys()))

    for dict1 in list1:
        for dict2 in list2:
            for key in included_keys[parent_key]:
                if isinstance(dict1[key], list) and \
                        isinstance(dict2[key], list):
                    included_keys = _find_keys(
                        dict1[key], dict2[key], included_keys, key)
                elif isinstance(dict1[key], dict) and \
                        isinstance(dict2[key], dict):
                    included_keys = _find_keys(
                        [dict1[key]], [dict2[key]], included_keys, key)
    return included_keys


def _filter_dicts(list1, list2, included_keys, parent_key, forcekeys):
    """
    Recursive function for find_max_complete.
    Filters lists according to given keys.
    """
    for listx in [list1, list2]:
        for index, dictx in enumerate(listx):
            tmpdict = {key: dictx[key]
                       for key in included_keys[parent_key]}
            if forcekeys:
                for key in set(dictx.keys()). \
                        intersection(set(forcekeys)):
                    tmpdict[key] = dictx[key]
            listx[index] = tmpdict

    for dict1 in list1:
        for dict2 in list2:
            for key in included_keys[parent_key]:
                if isinstance(dict1[key], list) and \
                        isinstance(dict2[key], list):
                    (dict1[key], dict2[key]) = \
                        _filter_dicts(dict1[key], dict2[key],
                                      included_keys, key, forcekeys)
                elif isinstance(dict1[key], dict) and \
                        isinstance(dict2[key], dict):
                    (sublist1, sublist2) = \
                        _filter_dicts([dict1[key]], [dict2[key]],
                                      included_keys, key, forcekeys)
                    if sublist1 and sublist2:
                        dict1[key] = sublist1[0]
                        dict2[key] = sublist2[0]

    return (list1, list2)


def create_scraper_params(metadata_info):
    """Creates a suitable dictionary for keyword arguments for Scraper.

    :metadata_info: Discovered metadata information in dictionary.
    :returns: Dictionary of the parameters that can be passed to Scraper.
    """
    params = {}

    for scr_param_key, addml_key in _SCRAPER_PARAM_ADDML_KEY_RELATION:
        try:
            params[scr_param_key] = metadata_info['addml'][addml_key]
        except KeyError:
            # "addml_key"-key did not exist therefore no need to do anything.
            pass
    return params


def synonymize_stream_keys(stream):
    """Synonymizes the stream keys that is more appropriate for the mets
    validation.
    The stream keys are defined as is by file-scraper. Will throw
    RuntimeException if the key that is being named to already exists.
    """

    for first_key, second_key in _FFMPEG_FILE_SCRAPER_KEY_SYNONYMS:
        if hasattr(stream, second_key):
            raise RuntimeError('Stream [%s] key already exists' % second_key)
        try:
            stream[second_key] = stream[first_key]
        except KeyError:
            # "scrape_key"-key did not exist therefore no need to do anything.
            pass
    return stream


def concat(lines, prefix=''):
    """Join given list of strings to single string separated with newlines.

    :lines: List of string to join
    :prefix: Prefix to prepend each line with
    :returns: Joined lines as string

    """
    return '\n'.join(['%s%s' % (prefix, line) for line in lines])


def get_scraper_info(scraper):
    """
    Gather messages and errors from scraper.info dictionary, filtering empty
    errors. Prepend each message with the name of the scraper class which
    produced it.

    :scraper: The scraper object which has conducted scraping.
    :returns: (messages, errors) tuple, where
              - messages is a list of gathered messages
              - errors is a list of gathered errors
    """
    messages, errors = [], []
    for info in six.itervalues(scraper.info):
        scraper_class = info['class']
        # Keep empty messages to see which scrapers were used,
        # but filter empty errors
        messages.append(scraper_class + ': ' + info['messages'])
        if info['errors']:
            errors.append(scraper_class + ': ' + info['errors'])
    return messages, errors
