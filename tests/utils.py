"""Utilities

Couple of functions have been adapted from a MIT licensed open source solution:

Copyright (c) 2018 Benjamin Peterson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import six


class Directory(str):
    """Automatically create directory structures"""

    def __new__(cls, path):
        """Str immutable types call __new__() to instantiate new classes.

        Create directory when directory class is created"""

        if not os.path.isdir(path):
            os.makedirs(path)

        return str.__new__(cls, path)

    def subdir(self, directory):
        """Return Directory object to subdirectory `<self>/<directory>

        :directory: Subdirectory name
        :returns: Directory object to subdirectory

        """
        return Directory(os.path.join(self, directory))

    def __getattr__(self, attr):
        """Return original class attribute ethods or self.subdir(attr) if
        attribute does not exist.

        :attr: Attribute
        :returns: Attribute or Directory object

        """

        try:
            if attr in self.__dict__:
                return self.__dict__[attr]
            return self.subdir(attr)
        except Exception as exception:
            raise AttributeError(str(exception))


def ensure_binary(s, encoding='utf-8', errors='strict'):
    """Coerce **s** to six.binary_type.

    For Python 2:
      - `unicode` -> encoded to `str`
      - `str` -> `str`

    For Python 3:
      - `str` -> encoded to `bytes`
      - `bytes` -> `bytes`

    Direct copy from release 1.12::

        https://github.com/benjaminp/six/blob/master/six.py#L853
    """
    if isinstance(s, six.text_type):
        return s.encode(encoding, errors)
    elif isinstance(s, six.binary_type):
        return s
    else:
        raise TypeError("not expecting type '%s'" % type(s))


def ensure_text(s, encoding='utf-8', errors='strict'):
    """Coerce *s* to six.text_type.

    For Python 2:
      - `unicode` -> `unicode`
      - `str` -> `unicode`

    For Python 3:
      - `str` -> `str`
      - `bytes` -> decoded to `str`

    Direct copy from release 1.12::

        https://github.com/benjaminp/six/blob/master/six.py#892
    """
    if isinstance(s, six.binary_type):
        return s.decode(encoding, errors)
    elif isinstance(s, six.text_type):
        return s
    else:
        raise TypeError("not expecting type '%s'" % type(s))
