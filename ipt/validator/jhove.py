"""Module for vallidating files with JHove 1 Validator"""
import os
import lxml.etree

from ipt.validator.basevalidator import BaseValidator
from ipt.utils import UnknownException, ValidationException, run_command

JHOVE_MODULES = {
    'application/pdf': 'PDF-hul',
    'image/tiff': 'TIFF-hul',
    'image/jpeg': 'JPEG-hul',
    'image/jp2': 'JPEG2000-hul',
    'image/gif': 'GIF-hul',
    'text/html': 'HTML-hul'
}

NAMESPACES = {'j': 'http://hul.harvard.edu/ois/xml/ns/jhove'}


class Jhove(BaseValidator):
    """ Initializes JHove 1 validator and set ups everything so that
        methods from base class (BaseValidator) can be called, such as
        validate() for file validation.

        .. note:: The following mimetypes and JHove modules are supported:
                  'application/pdf': 'PDF-hul', 'image/tiff': 'TIFF-hul',
                  'image/jpeg': 'JPEG-hul', 'image/jp2': 'JPEG2000-hul',
                  'image/gif': 'GIF-hul'

        .. seealso:: http://jhove.sourceforge.net/documentation.html
    """

    _supported_mimetypes = {
        'application/pdf': ['1.3', '1.4', 'A-1a', 'A-1b'],
        'image/tiff': ['6.0'],
        'image/jpeg': ['', '1.0', '1.01'],
        'image/jp2': [],
        'image/gif': ['1987a', '1989a'],
        'text/html': []
    }

    def __init__(self, fileinfo):
        """init"""
        super(Jhove, self).__init__(fileinfo)

        self.filename = fileinfo['filename']
        self.fileversion = fileinfo['format']['version']
        self.mimetype = fileinfo['format']['mimetype']

        self.exec_cmd = ['jhove', '-h', 'XML']
        self.statuscode = 1
        self.stderr = ""
        self.stdout = ""

        # only names with whitespace are quoted. this might break the
        # filename otherwise ::
        if self.filename.find(" ") != -1:
            if not (self.filename[0] == '"' and self.filename[-1] == '"'):
                self.filename = '%s%s%s' % ('"', self.filename, '"')

        if self.mimetype in JHOVE_MODULES.keys():
            validator_module = JHOVE_MODULES[self.mimetype]
            command = ['-m', validator_module]
            self.exec_cmd += command
        else:
            raise ValidationException(
                "jhove.py does not seem to support mimetype: %s" %
                self.mimetype)

    def validate(self):
        """Validate file with command given in variable self.exec_cmd and with
        options set in self.exec_options. Also check that validated file
        version and profile matches with validator.

        :returns: Tuple (status, report, errors) where
            status -- 0 is success, 117 validation failure,
                      anything else system error.
            report -- generated report
            errors -- errors if encountered, else None
        """

        filename_in_list = [self.filename]
        self.exec_cmd += filename_in_list
        (self.statuscode,
         self.stdout,
         self.stderr) = run_command(cmd=self.exec_cmd)

        if self.statuscode != 0:
            return (self.statuscode, self.stdout,
                    "Validator returned error: %s\n%s" % (
                        self.statuscode, self.stderr))

        errors = []

        # Check file validity
        (validity_exitcode, validity_stderr) = self.check_validity()
        if validity_exitcode != 0:
            errors.append(validity_stderr)

        # Check file version
        (version_exitcode, version_errors) = self.check_version(
            self.fileversion)
        if version_exitcode != 0:
            errors.append(version_errors)

        # Check file profile
        (profile_exitcode, profile_errors) = self.check_profile(
            self.fileversion)
        if profile_exitcode != 0:
            errors.append(profile_errors)

        if len(errors) == 0:
            return (0, self.stdout, '')
        else:
            return (117, self.stdout, '\n'.join(errors))

    def check_validity(self):
        """ Check if file is valid according to JHove output.
        :returns: a tuple (0/117, errormessage)
        """
        if self.statuscode == 254 or self.statuscode == 255:
            raise UnknownException("Jhove returned returncode: \
                %s %s %s" % (self.statuscode, self.stdout, self.stderr))
        status = self.get_report_field("status")
        filename = os.path.basename(self.filename)

        if status != 'Well-Formed and valid':
            return (117, "ERROR: File '%s' does not validate: %s" % (
                filename, status))
        return (0, "")

    def check_version(self, version):
        """ Check if version string matches JHove output.
        :version: version string
        :returns: a tuple (0/117, errormessage)
        """

        report_version = self.get_report_field("version")
        report_version = report_version.replace(" ", ".")

        if version is None:
            return (0, "")

        if self.mimetype == "application/pdf" and "A-1" in version:
            version = "1.4"

        # There is no version tag in TIFF images.
        # TIFF 4.0 and 5.0 is also valid TIFF 6.0.
        if self.mimetype == "image/tiff" and report_version in ["4.0", "5.0"]:
            report_version = "6.0"

        if report_version != version:
            return (117, (
                "ERROR: File version is '%s', expected '%s'"
                % (report_version, version)))
        return (0, "")

    def check_profile(self, version):
        """ Check if profile string matches JHove output.
        :version: version number
        :returns: a tuple (0/117, errormessage)
        """
        profile = None
        if self.mimetype == "application/pdf" and "A-1" in version:
            profile = "ISO PDF/A-1"

        report_profile = self.get_report_field("profile")
        if profile is None:
            return (0, "")

        if profile not in report_profile:
            return (117, "ERROR: File profile is '%s', expected '%s'" % (
                report_profile, profile))
        return (0, "")

    def get_report_field(self, field):
        """
        Return field value from JHoves XML output. This method assumes that
        JHove's XML output handler is used: jhove -h XML. Method uses XPath
        for querying JHoves output. This method is mainly used by validator
        class itself. Example usage:

        .. code-block:: python

            get_report_field("Version", report)
            1.2

            get_report_field("Status", report)
            "Well formed"

        :field: Field name which content we are looking for. In practise
            field is an element in XML document.
        :returns:
            Concatenated string where each result is on own line. An empty
            string is returned if there's no results.
        """

        root = lxml.etree.fromstring(self.stdout)
        query = '//j:%s/text()' % field
        results = root.xpath(query, namespaces=NAMESPACES)

        return '\n'.join(results)