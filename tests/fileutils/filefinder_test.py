# Common boilerplate
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Module to test
import ipt.fileutils.filefinder


SIPDIR = os.path.abspath(os.path.dirname(__file__) + '../../data/sips')


class TestGetFilesInTree:

    def test_filelist_with_chdir(self):
        testset = set([
            'data/valid_1987a.gif',
            'data/valid_1.mp3',
            'data/valid_5.0.html',
            'data/valid__ascii.txt',
            'data/valid__utf8.txt',
            'mets.xml',
            'signature.sig'])
        cwd = os.getcwd()
        os.chdir(os.path.join(SIPDIR, 'valid_1.7.1_multiple_objects'))
        gotset = set(ipt.fileutils.filefinder.get_files_in_tree())
        os.chdir(cwd)
        assert gotset == testset

    def test_filelist_with_tree(self):
        testset = set([
            'data/valid_1987a.gif',
            'data/valid_1.mp3',
            'data/valid_5.0.html',
            'data/valid__ascii.txt',
            'data/valid__utf8.txt',
            'mets.xml',
            'signature.sig'])
        relpath = os.path.relpath(os.path.join(SIPDIR,
                                               'valid_1.7.1_multiple_objects'))
        assert set(
            ipt.fileutils.filefinder.get_files_in_tree(relpath)) == testset
