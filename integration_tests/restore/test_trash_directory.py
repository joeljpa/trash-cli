import unittest

import six

from trashcli.restore import TrashDirectory

from integration_tests.files import require_empty_dir
from unit_tests.support import MyPath
from integration_tests.files import make_file
from mock import Mock


class TestTrashDirectory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = MyPath.make_temp_dir()
        require_empty_dir(self.temp_dir / 'trash-dir')
        self.trash_dir = TrashDirectory()
        self.logger = Mock()
        self.trash_dir.logger = self.logger

    def test_should_list_a_trashinfo(self):
        make_file(self.temp_dir / 'trash-dir/info/foo.trashinfo')

        result = self.list_trashinfos()

        assert [('trashinfo', self.temp_dir / 'trash-dir/info/foo.trashinfo')] == result

    def test_should_list_multiple_trashinfo(self):
        make_file(self.temp_dir / 'trash-dir/info/foo.trashinfo')
        make_file(self.temp_dir / 'trash-dir/info/bar.trashinfo')
        make_file(self.temp_dir / 'trash-dir/info/baz.trashinfo')

        result = self.list_trashinfos()

        six.assertCountEqual(self,
                             [('trashinfo', self.temp_dir / 'trash-dir/info/foo.trashinfo'),
                              ('trashinfo', self.temp_dir / 'trash-dir/info/baz.trashinfo'),
                              ('trashinfo', self.temp_dir / 'trash-dir/info/bar.trashinfo')],
                             result)

    def test_non_trashinfo_should_reported_as_a_warn(self):
        make_file(self.temp_dir / 'trash-dir/info/not-a-trashinfo')

        result = self.list_trashinfos()

        six.assertCountEqual(self,
                             [('non_trashinfo',
                               self.temp_dir / 'trash-dir/info/not-a-trashinfo')],
                             result)

    def list_trashinfos(self):
        return list(self.trash_dir.all_info_files(self.temp_dir / 'trash-dir'))


