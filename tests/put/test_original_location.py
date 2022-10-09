import unittest

from trashcli.put.original_location import OriginalLocation, parent_realpath
from trashcli.put.path_maker import PathMaker, PathMakerType
from parameterized import parameterized

rel = PathMakerType.relative_paths
abs = PathMakerType.absolute_paths


class TestOriginalLocation(unittest.TestCase):

    def setUp(self):
        self.original_location = OriginalLocation(parent_realpath, PathMaker())

    @parameterized.expand([
        ('/volume', '/file', abs, '/file',),
        ('/volume', '/file/././', abs, '/file',),
        ('/volume', '/dir/../file', abs, '/file'),
        ('/volume', '/dir/../././file', abs, '/file'),
        ('/volume', '/outside/file', abs, '/outside/file'),
        ('/volume', '/volume/file', abs, '/volume/file',),
        ('/volume', '/volume/dir/file', abs, '/volume/dir/file'),
        ('/volume', '/file', rel, '/file'),
        ('/volume', '/dir/../file', rel, '/file'),
        ('/volume', '/outside/file', rel, '/outside/file'),
        ('/volume', '/volume/file', rel, 'file'),
        ('/volume', '/volume/dir/file', rel, 'dir/file'),
    ])
    def test_original_location(self, volume, file_to_be_trashed, path_type,
                               expected_result):
        result = self.original_location.for_file(file_to_be_trashed, path_type,
                                                 volume)
        assert expected_result == result
