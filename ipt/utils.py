"""
Utility functions.
"""
from __future__ import annotations

import os
from collections import defaultdict
from collections.abc import Callable, Iterable
from copy import deepcopy
from fractions import Fraction
from urllib.parse import unquote_plus, urlparse
from typing import Any
from file_scraper.scraper import Scraper

import mimeparse
import lxml.etree as ET


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


def matching_types(a: Any, b: Any, t: type) -> bool:
    """Determine whether both input objects are instances of a specified type.

    :param a: First object
    :param b: Second object
    :param t: The type to compare
    :returns: True if both a and b are instances of type t, otherwise False.
    """
    return isinstance(a, t) and isinstance(b, t)


def merge_dicts(*dicts: dict[str, dict | list | None]
                ) -> dict[str, dict | list | None]:
    """Merge multiple dictionaries. Lists and dicts with the same key are
    merged. None values are overwritten by non-None values.

    Other types cannot be merged.

    :param dicts: Dictionaries to merge.
    :returns: A single merged dictionary.
    """
    result = {}
    for dictionary in dicts:
        if not dictionary:
            continue
        for key, value in dictionary.items():
            if key not in result:
                result[key] = value
            elif result[key] is None:
                result[key] = value
            elif value is None:
                continue
            elif matching_types(result[key], value, dict):
                result[key] = merge_dicts(result[key], value)
            elif matching_types(result[key], value, list):
                result[key] = result[key] + value
            else:
                raise TypeError('Only lists and dictionaries can be merged.')

    return result


def compare_lists_of_dicts(expected: list[dict[str, Any]],
                           found: list[dict[str, Any]]) -> bool:
    """Compares two lists of dictionaries.

    :param expected: list of dicts that should be present
    :param found: list of dicts that are actually present
    :returns: True if both lists contain the same dicts with the same
    frequency, False otherwise
    """
    expected_count = count_items_in_dict(expected)
    found_count = count_items_in_dict(found)
    return expected_count == found_count


def count_items_in_dict(dicts: list[dict[str, Any]]) -> dict[str, int]:
    """Counts occurrences of serialized dictionaries in a list.

    :param dicts: list of dictionaries
    :returns: dict with serialized dicts as keys and their counts
    """
    if not dicts:
        return {}

    count = defaultdict(int)
    for item in dicts:
        serialized = serialize_dict(item)
        count[serialized] += 1

    return count


def serialize_dict(data: dict[str, Any]) -> str:
    """Serialize a dictionary to a string.

    :param data: A dictionary.
    :returns: A string in the format "<key=value>  <key=value>"
    """
    if not data:
        return ""

    parts = [f"{key}={data[key]}" for key in sorted(data)]
    return "  ".join(parts)


def uri_to_path(uri: str) -> bytes:
    """Remove URI scheme from given `URI`:

    file://kuvat/PICT0081.JPG -> kuvat/PICT0081.JPG

    :param uri: URI as string
    :returns: Relative path as UTF-8 encoded bytes
    """
    path = unquote_plus(uri).replace('file://', '')
    return path.lstrip('./').encode("utf-8")


def parse_mimetype(mimetype: str) -> dict[str, dict[str, Any]]:
    """Parse MIME type information from a Content-Type string.

    Attempts to extract the MIME type, charset, and alternative format
    from the given Content-Type string. If parsing fails, marks the
    mimetype as erroneous.

    See also: https://www.ietf.org/rfc/rfc2045.txt

    :param mimetype: The Content-Type string to parse.
    :returns: A dictionary with parsed format information.
    """
    result = {"format": {}}

    try:
        result_mimetype = mimeparse.parse_mime_type(mimetype)
    except mimeparse.MimeTypeParseException:
        result["format"]["erroneous-mimetype"] = True
        result["format"]["mimetype"] = mimetype
        return result

    params = result_mimetype[2]
    charset = params.get('charset')
    alt_format = params.get('alt-format')
    result["format"]["mimetype"] = f"{result_mimetype[0]}/{result_mimetype[1]}"
    if charset:
        result["format"]["charset"] = charset
    if alt_format:
        result["format"]["alt-format"] = alt_format

    return result


def handle_div(div: str, decimals: int = 2) -> str:
    """Converts a string representing a division or a decimal number into a
    formatted string with a maximum of <decimals> decimal places.

    Returns the original string if conversion fails due to ValueError or
    ZeroDivisionError.

    :param div: A string like "16/9" or "1.7777778"
    :param decimals: Number of decimal places to round to (default is 2)
    :returns: A string like "1.78"
    """
    try:
        value = float(Fraction(div))
        rounded = round(value, decimals)
        if decimals == 0:
            return str(int(rounded))
        return f"{rounded:.{decimals}f}".rstrip('0').rstrip('.')
    except (ValueError, ZeroDivisionError):
        return div


def find_max_complete(list1: list[dict] | None,
                      list2: list[dict] | None,
                      forcekeys: list[str] | None = None
                      ) -> tuple[list[dict], list[dict]]:
    """Filters two lists of dictionaries to retain only keys that are common
    across all dictionaries in both lists, recursively.

    Keys in `forcekeys` are preserved.

    :param list1: First list of dicts
    :param list2: Second list of dicts
    :param forcekeys: List of those keys which will not be changed or removed,
    if exists
    :returns: Filtered list1 and list2
    """
    list1 = list1 or []
    list2 = list2 or []
    forcekeys = forcekeys or []

    if not list1 and not list2:
        return [], []

    root_key_test = _get_first_dict(list1) or _get_first_dict(list2)
    if root_key_test is None:
        return list1, list2

    included_keys = _find_keys(list1, list2)

    return _filter_dicts(deepcopy(list1), deepcopy(list2), included_keys,
                         'root_key', forcekeys)


def _get_first_dict(lst: list[Any]) -> dict[str, Any] | None:
    """Returns the first dictionary in a list, or None if none exists.

    :param lst: A list potentially containing dictionaries
    :returns: The first dictionary found, or None
    """
    return next(item for item in lst if isinstance(item, dict)), None


def _find_keys(list1: list[dict],
               list2: list[dict],
               included_keys: dict[str, set[str]] | None = None,
               parent_key: str = 'root_key') -> dict[str, set[str]]:
    """Recursively finds keys common to all dictionaries in both lists.

    :param list1: First list of dictionaries
    :param list2: Second list of dictionaries
    :param included_keys: Dictionary tracking included keys by parent key.
    Optional, defaults to an empty dictionary
    :param parent_key: Current parent key in recursion. Optional, defaults to
    'root_key'
    :returns: Updated dictionary of included keys
    """
    if included_keys is None:
        included_keys = {}

    if parent_key not in included_keys:
        if list1:
            included_keys[parent_key] = set(list1[0].keys())
        elif list2:
            included_keys[parent_key] = set(list2[0].keys())
        else:
            included_keys[parent_key] = set()

    for d in list1 + list2:
        if isinstance(d, dict):
            included_keys[parent_key] &= set(d.keys())

    for d1 in list1:
        for d2 in list2:
            _find_keys_recurse_nested(d1, d2, included_keys, parent_key)

    return included_keys


def _find_keys_recurse_nested(dict1: dict[str, Any],
                              dict2: dict[str, Any],
                              included_keys: dict[str, set[str]],
                              parent_key: str) -> None:
    """Recursively finds keys common in both dictionaries

    :param dict1: First dictionary
    :param dict2: Second dictionary
    :param included_keys: Dictionary tracking included keys by parent key.
    :param parent_key: Current parent key is recursion
    """
    for key in included_keys[parent_key]:
        val1 = dict1[key]
        val2 = dict2[key]

        if matching_types(val1, val2, list):
            included_keys = _find_keys(val1, val2, included_keys, key)
        elif matching_types(val1, val2, dict):
            included_keys = _find_keys([val1], [val2], included_keys, key)


def _filter_dicts(list1: list[dict],
                  list2: list[dict],
                  included_keys: dict[str, set[str]],
                  parent_key: str,
                  forcekeys: list[str]) -> tuple[list[dict], list[dict]]:
    """Recursively filters dictionaries to retain only specified keys.

    :param list1: First list of dictionaries to filter
    :param list2: Second list of dictionaries to filter
    :param included_keys: Keys to retain, grouped by parent key
    :param parent_key: Current parent key in recursion
    :param forcekeys: Keys to preserve regardless of filtering
    :returns: Tuple of filtered list1 and list2
    """
    list1 = [_filter_single_dict(d, included_keys[parent_key], forcekeys)
             for d in list1]
    list2 = [_filter_single_dict(d, included_keys[parent_key], forcekeys)
             for d in list2]

    for d1 in list1:
        for d2 in list2:
            _filter_dicts_recurse_nested(d1, d2, included_keys, parent_key,
                                         forcekeys)

    return list1, list2


def _filter_dicts_recurse_nested(dict1: dict,
                                 dict2: dict,
                                 included_keys: dict[str, set[str]],
                                 parent_key: str,
                                 forcekeys: list[str]) -> None:
    """Recursively filters nested dictionaries and lists within two
    dictionaries.

    :param dict1: First dictionary to process
    :param dict2: Second dictionary to process
    :param included_keys: Dictionary of keys to retain, grouped by parent key
    :param parent_key: Current parent key in recursion
    :param forcekeys: Keys to preserve regardless of filtering
    """
    for key in included_keys[parent_key]:
        if key not in dict1 or key not in dict2:
            continue

        val1 = dict1[key]
        val2 = dict2[key]

        if matching_types(val1, val2, list):
            val1, val2 = _filter_dicts(val1, val2, included_keys,
                                       key, forcekeys)
        elif matching_types(val1, val2, dict):
            sublist1, sublist2 = _filter_dicts([val1], [val2], included_keys,
                                               key, forcekeys)
            if sublist1 and sublist2:
                dict1[key] = sublist1[0]
                dict2[key] = sublist2[0]


def _filter_single_dict(d: dict[str, Any],
                        keys_to_keep: set[str],
                        forcekeys: list[str]) -> dict[str, Any]:
    """Filters a single dictionary based on keys to keep and forcekeys.

    :param d: Dictionary to filter
    :param keys_to_keep: Set of keys to keep
    :param forcekeys: Keys to preserve regardless of filtering
    :returns: Filtered dictionary
    """
    filtered = {k: d[k] for k in keys_to_keep if k in d}
    if forcekeys:
        for k in set(d.keys()).intersection(forcekeys):
            filtered[k] = d[k]
    return filtered


def pair_compatible_list_elements(
        list_a: list[Any],
        list_b: list[Any],
        check_compatible: Callable[[list[Any], list[Any]], bool],
        **check_compatible_kwargs: Any) -> set[tuple[int, int]]:
    """Check if the elements of two lists can be matched perfectly so that
    every element in list_a has a pair in list_b and vice versa, and no element
    gets more than one pair. Elements p and q can be paired if
    check_compatible(p, q) returns True.

    :param list_a: First list of elements to pair
    :param list_b: Second list of elements to pair
    :param check_compatible: Function to test if some element in list_a can be
    paired with some element in list_b
    :param check_compatible_kwargs: Keyword arguments to pass into
    check_compatible

    :returns: Set of (idx_a, idx_b) tuples, where idx_a is the index of element
    in list_a which was paired with list_b[idx_b], or empty set if pairing is
    not possible.
    """

    def _match(indices_a: Any, indices_b: Any) -> set:
        if not indices_a:
            # Nothing left to pair
            return set()
        idx_a = next(iter(indices_a))
        for idx_b in indices_b:
            if check_compatible(list_a[idx_a], list_b[idx_b],
                                **check_compatible_kwargs):
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


def create_scraper_params(metadata_info: dict[str, Any]) -> dict[str, Any]:
    """Creates a suitable dictionary for keyword arguments for Scraper.

    :param metadata_info: Discovered metadata information in dictionary.
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


def synonymize_stream_keys(stream: dict[str, Any]) -> dict[str, Any]:
    """Synonymizes the stream keys to be more appropriate for METS validation.

    The stream keys are defined as is by file-scraper. Will throw
    RuntimeException if the key that is being named to already exists.

    :param stream: A dictionary representing the original stream with keys from
    file-scraper.
    :returns: A new dictionary with synonymized keys suitable for METS
    validation.
    """

    new_stream = {}
    for key, value in stream.items():
        # Get the equivalent METS key if one exists, otherwise use old key
        new_key = _FFMPEG_FILE_SCRAPER_KEY_SYNONYMS.get(key, key)
        if new_key in new_stream:
            raise RuntimeError(f'Stream [{new_key}] key already exists')
        new_stream[new_key] = value

    return new_stream


def concat(lines: list[str], prefix: str = '') -> str:
    """Join given list of strings to single string separated with newlines.

    :param lines: List of string to join
    :param prefix: Prefix to prepend each line with
    :returns: Joined lines as string

    """
    return '\n'.join(['{}{}'.format(prefix, line) for line in lines])


def get_scraper_info(scraper: Scraper
                     ) -> dict[str, list[str | ET._Element]]:
    """Gather messages and errors from scraper.info dictionary.
    Prepend each message with the name of the scraper class which
    produced it, and any plain text errors with 'ERROR: '. If a message
    or error can be parsed as XML, return it as lxml.etree element instead.

    :param scraper: The scraper object which has conducted scraping.
    :returns: {'messages': ['[MyScraper] Message', ...],
               'errors': ['[MyScraper] ERROR: Failed', ...],
               'extensions': [ET._Element, ...]}
    """

    def _add_text_xml(scraper_info: dict[str, Any],
                      info_key: str,
                      prefix: str) -> None:
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


def parse_uri_filepath(uri_path: str, accepted_schemes: Iterable[str]) -> str:
    """Parses and return the filepath from uri path by omitting the scheme and
    unquoting the path.

    :param uri_path: URI path that is being parsed.
    :param accepted_schemes: Iterable of accepted URI schemes.
    :returns: Relative path of the given uri path in string.
    """
    # Schema_path as unquoted file path with leading slashes
    # removed since schema_path should always be a relative path
    schemes = ', '.join(accepted_schemes)
    parsed_result = urlparse(uri_path)
    if parsed_result.scheme not in accepted_schemes:
        raise ValueError((f'Scheme [{parsed_result.scheme}]'
                          'is not among the accepted schemes '
                          f'[{schemes}]'))
    # Joining by netlock and stripping special characters from path is for the
    # cases with ambiguous number of slashes... Like file-URI scheme where
    # usage can vary between one to even four slashes.
    return unquote_plus(os.path.join(parsed_result.netloc,
                                     parsed_result.path.lstrip('/')))


def ensure_binary(string: str | bytes,
                  encoding: str = 'utf-8',
                  errors: str = 'strict') -> bytes:
    """Coerce a string or bytes object to a binary (bytes) object.

    :param string: Input string or bytes
    :param encoding: Encoding to use when converting to bytes, default is UTF-8
    :param errors: Error mode for encoding, default is 'strict'. Other values
    include 'ignore', 'replace', and other UnicodeEncodeErrors
    :returns: Input as bytes
    """
    if isinstance(string, str):
        return string.encode(encoding, errors)
    if isinstance(string, bytes):
        return string
    raise TypeError(f"Not expecting type '{type(string)}'")


def ensure_text(string: str | bytes,
                encoding: str = 'utf-8',
                errors: str = 'strict') -> str:
    """Coerce a string or bytes object to a text (str) object.

    :param string: Input string or bytes
    :param encoding: Decoding to use when converting to text, default is UTF-8
    :param errors: Error mode for decoding, default is 'strict'. Other values
    include 'ignore', 'replace', and other UnicodeDecodeErrors
    :returns: Input as string
    """
    if isinstance(string, bytes):
        return string.decode(encoding, errors)
    if isinstance(string, str):
        return string
    raise TypeError(f"Not expecting type '{type(string)}'")
