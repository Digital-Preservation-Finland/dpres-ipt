from file_scraper.utils import hexdigest


class BigFile(object):

    def __init__(self, algorithm='sha1'):
        # Accept MD5 and different SHA variations
        self.algorithm = algorithm.lower().replace('-', '').strip()

    def hexdigest(self, filename):
        return hexdigest(filename, self.algorithm)

    def checksums_match(self, checksum_expected, checksum_to_test):
        return ((len(checksum_expected) > 0) and
                (checksum_expected == checksum_to_test))

    def verify_file(self, filename, hexdigest):
        file_hexdigest = self.hexdigest(filename)
        return self.checksums_match(file_hexdigest, hexdigest)
