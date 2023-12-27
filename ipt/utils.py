"""
Utility functions.
"""
import os
from collections import defaultdict
from copy import deepcopy
from fractions import Fraction
import mimeparse

import lxml.etree as ET

from urllib.parse import unquote_plus, urlparse


_SCRAPER_PARAM_ADDML_KEY_RELATION = (('fields', 'header_fields'),
                                     ('separator', 'separator'),
                                     ('delimiter', 'delimiter'))

_FFMPEG_FILE_SCRAPER_KEY_SYNONYMS = {'frame_rate': 'avg_frame_rate',
                                     'data_rate': 'bit_rate',
                                     'dar': 'display_aspect_ratio',
                                     'num_channels': 'channels',
                                     'sampling_frequency': 'sample_rate'}


class UnknownException(Exception):
    """Unknown error."""


class ValidationException(Exception):
    """Validator error."""


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
            serialized_dict = f'{serialized_dict}{key}={data[key]}  '
    return serialized_dict.strip("  ")


def uri_to_path(uri):
    """Remove URI scheme from given `URI`:

    file://kuvat/PICT0081.JPG -> kuvat/PICT0081.JPG

    :uri: URI as string
    :returns: Relative path as string

    """
    path = unquote_plus(uri).replace('file://', '')
    return path.lstrip('./').encode("utf-8")


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
            included_keys[parent_key] = set()

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


def pair_compatible_list_elements(list_a, list_b, check_compatible):
    """
    Check if the elements of two lists can be matched perfectly so that every
    element in list_a has a pair in list_b and vice versa, and no element
    gets more than one pair. Elements p and q can be paired iff
    check_compatible(p, q) returns True.

    :list_a: List of elements to pair
    :list_b: List of elements to pair
    :check_compatible: Function to test if some element in list_a can be paired
                       with some element in list_b
    :returns: Set of (idx_a, idx_b) tuples, where idx_a is the index of element
              in list_a which was paired with list_b[idx_b], or empty set if
              pairing is not possible.
    """

    def _match(indices_a, indices_b):
        if not indices_a:
            # Nothing left to pair
            return set()
        idx_a = next(iter(indices_a))
        for idx_b in indices_b:
            if check_compatible(list_a[idx_a], list_b[idx_b]):
                # Found matching elements, remove matched indices and pair
                # the rest recursively
                matched_indices = _match(indices_a - {idx_a},
                                         indices_b - {idx_b})
                if matched_indices or len(indices_a) == 1:
                    # Pairing was successful, add indices of current matching
                    # elements into the set of matched indices
                    return matched_indices.union({(idx_a, idx_b)})
        # list_a[idx_a] could not be paired with any element in list_b
        return set()

    if len(list_a) != len(list_b):
        # If list lengths don't match, perfect pairing is impossible
        return set()
    return _match(set(range(len(list_a))), set(range(len(list_b))))


def create_scraper_params(metadata_info):
    """Creates a suitable dictionary for keyword arguments for Scraper.

    :metadata_info: Discovered metadata information in dictionary.
    :returns: Dictionary of the parameters that can be passed to Scraper.
    """
    params = {}

    if "format" in metadata_info and "charset" in metadata_info["format"]:
        params["charset"] = metadata_info["format"]["charset"]

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

    new_stream = {}
    for key, value in stream.items():
        # Get the equivalent METS key if one exists, otherwise use old key
        new_key = _FFMPEG_FILE_SCRAPER_KEY_SYNONYMS.get(key, key)
        if new_key in new_stream:
            raise RuntimeError(f'Stream {new_key} key already exists')
        new_stream[new_key] = value

    return new_stream


def concat(lines, prefix=''):
    """Join given list of strings to single string separated with newlines.

    :lines: List of string to join
    :prefix: Prefix to prepend each line with
    :returns: Joined lines as string

    """
    return '\n'.join(['{}{}'.format(prefix, line) for line in lines])


def get_scraper_info(scraper):
    """
    Gather messages and errors from scraper.info dictionary.
    Prepend each message with the name of the scraper class which
    produced it, and any plain text errors with 'ERROR: '. If a message
    or error can be parsed as XML, return it as lxml.etree element instead.

    :scraper: The scraper object which has conducted scraping.
    :returns: {'messages': ['[MyScraper] Message', ...],
               'errors': ['[MyScraper] ERROR: Failed', ...],
               'extensions': [ET._Element, ...]}
    """

    def _add_text_xml(scraper_info, info_key, prefix):
        strings = scraper_info[info_key]
        text, extensions = [], []
        parser = ET.XMLParser(remove_blank_text=True)
        for string in strings:
            try:
                extensions.append(ET.fromstring(ensure_binary(string), parser))
            except ET.XMLSyntaxError:
                text.append(prefix + string)
        if extensions:
            text.append(prefix + 'See eventOutcomeDetailExtension '
                                 'for details.')
        info[info_key].extend(text)
        info['extensions'].extend(extensions)

    info = {'messages': [],
            'errors': [],
            'extensions': []}
    for scraper_info in scraper.info.values():
        scraper_prefix = '[' + scraper_info['class'] + '] '
        _add_text_xml(scraper_info, 'messages', scraper_prefix)
        _add_text_xml(scraper_info, 'errors', scraper_prefix + 'ERROR: ')
    return info


def parse_uri_filepath(uri_path, accepted_schemes):
    """Parses and return the filepath from uri path by omitting the scheme and
    unquoting the path.

    :param uri_path: URI path that is being parsed.
    :param accepted_schemes: Iterable of accepted URI schemes.
    :return: Relative path of the given uri path in string.
    """
    # Schema_path as unquoted file path with leading slashes
    # removed since schema_path should always be a relative path
    elements = ', '.join(accepted_schemes)
    parsed_result = urlparse(uri_path)
    if parsed_result.scheme not in accepted_schemes:
        raise ValueError((f'Scheme [{parsed_result.scheme}] is not among the accepted schemes '
                          f'[{elements}]'))
    # Joining by netlock and stripping special characters from path is for the
    # cases with ambigious number of slashes... Like file-URI scheme where
    # usage can vary between one to even four slashes.
    return unquote_plus(os.path.join(parsed_result.netloc,
                                     parsed_result.path.lstrip('/')))


def ensure_binary(string, encoding='utf-8', errors='strict'):
    """Coerce string to binary.
    """
    if isinstance(string, str):
        return string.encode(encoding, errors)
    if isinstance(string, bytes):
        return string
    raise TypeError(f"not expecting type '{type(string)}'")


def ensure_text(string, encoding='utf-8', errors='strict'):
    """Coerce string to str.
    """
    if isinstance(string, bytes):
        return string.decode(encoding, errors)
    if isinstance(string, str):
        return string
    raise TypeError(f"not expecting type '{type(string)}'")
