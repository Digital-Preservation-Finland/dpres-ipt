from setuptools import setup, find_packages
from version import get_version
import os


def scripts_list():
    """Return list of command line tools from package pas.scripts"""
    scripts = []
    for modulename in os.listdir('ipt/scripts'):
        if modulename == '__init__.py':
            continue
        if not modulename.endswith('.py'):
            continue
        modulename = modulename.replace('.py', '')
        scriptname = modulename.replace('_', '-')
        scripts.append('%s = ipt.scripts.%s:main' % (scriptname, modulename))
    print(scripts)
    return scripts


def main():
    """Install dpres-ipt Python libraries"""
    setup(
        name='ipt',
        packages=find_packages(exclude=['tests', 'tests.*']),
        version=get_version(),
        entry_points={'console_scripts': scripts_list()},
        install_requires=[
            'python-mimeparse',
            'scandir; python_version == "2.7"',
            'six',
            'xml_helpers@git+https://gitlab.ci.csc.fi/dpres/xml-helpers.git'
            '@develop#egg=xml_helpers',
            'mets@git+https://gitlab.ci.csc.fi/dpres/mets.git'
            '@develop#egg=mets',
            'premis@git+https://gitlab.ci.csc.fi/dpres/premis.git'
            '@develop#egg=premis',
            'file_scraper@git+https://gitlab.ci.csc.fi/dpres/file-scraper.git'
            '@develop#egg=file_scraper'
        ]
    )


if __name__ == '__main__':
    main()
