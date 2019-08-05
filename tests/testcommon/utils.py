"""Utilities"""

import os


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


def create_test_bagit(bagit_path):
    """Create test bagit."""
    sip_path = os.path.join(bagit_path, 'data', 'transfers', 'sippi')

    os.makedirs(sip_path)

    mets_path = os.path.join(sip_path, 'mets.xml')
    with open(mets_path, 'w') as mets:
        mets.write('asfasdfasdfsda')

    image_path = os.path.join(sip_path, 'kuvat')
    os.makedirs(image_path)

    file_1_path = os.path.join(sip_path, 'file_1.txt')
    file_2_path = os.path.join(image_path, 'image1.jpg')
    with open(file_1_path, 'w') as infile:
        infile.write('abcd')
    with open(file_2_path, 'w') as infile:
        infile.write('abcdef')

    with open(os.path.join(bagit_path, 'manifest-md5.txt'), 'w') as outfile:
        outfile.write('e2fc714c4727ee9395f324cd2e7f331f ' + os.path.join(
            'data', 'file.txt') + '\n')
        outfile.write('e80b5017098950fc58aad83c8c14978e ' + os.path.join(
            'data', 'kuvat', 'file2.txt') + '\n')
    with open(os.path.join(bagit_path, 'bagit.txt'), 'w') as outfile:
        outfile.write('foo\n')
