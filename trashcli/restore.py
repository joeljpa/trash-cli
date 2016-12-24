import os
import sys

from .trash import version
from .fstab import Fstab
from .trash import TrashDirectory
from .trash import TrashDirectories
from .fs import contents_of
from .trash import backup_file_path_from
import fs

def getcwd_as_realpath(): return os.path.realpath(os.curdir)

class RestoreCmd(object):
    def __init__(self, stdout, stderr, environ, exit, input,
                 curdir = getcwd_as_realpath, version = version):
        self.out      = stdout
        self.err      = stderr
        self.exit     = exit
        self.input    = input
        self.environ  = environ
        self.curdir   = curdir
        self.version = version
        self.fs = fs
        self.path_exists = os.path.exists
        self.contents_of = contents_of
    def run(self, args = sys.argv):
        if '--version' in args[1:]:
            command = os.path.basename(args[0])
            self.println('%s %s' %(command, self.version))
            return

        trashed_files = self.all_trashed_files_in_dir()

        if not trashed_files:
            self.report_no_files_found()
        else :
            for i, trashedfile in enumerate(trashed_files):
                self.println("%4d %s %s" % (i, trashedfile.deletion_date, trashedfile.path))
            self.restore_asking_the_user(trashed_files)
    def restore_asking_the_user(self, trashed_files):
        index=self.input("What file to restore [0..%d]: " % (len(trashed_files)-1))
        if index == "" :
            self.println("Exiting")
        else :
            try:
                index = int(index)
                if (index < 0 or index >= len(trashed_files)):
                    raise IndexError("Out of range")
                trashed_file = trashed_files[index]
                self.restore(trashed_file)
            except (ValueError, IndexError) as e:
                self.printerr("Invalid entry")
                self.exit(1)
            except IOError as e:
                self.printerr(e)
                self.exit(1)
    def restore(self, trashed_file):
        restore(trashed_file, self.path_exists, self.fs)
    def all_trashed_files_in_dir(self):
        trashed_files = []
        self.for_all_trashed_file_in_dir(trashed_files.append, self.curdir())
        return trashed_files
    def for_all_trashed_file_in_dir(self, action, dir):
        def is_trashed_from_curdir(trashedfile):
            return trashedfile.path.startswith(dir + os.path.sep)
        for trashedfile in filter(is_trashed_from_curdir,
                                  self.all_trashed_files()) :
            action(trashedfile)
    def all_trashed_files(self):
        for trash_dir in self.all_trash_directories2():
            for trashedfile in self.trashed_files(trash_dir):
                yield trashedfile
    def all_trash_directories2(self):
        fstab = Fstab()
        mount_points = fstab.mount_points()
        all_trash_directories = AllTrashDirectories(
                volume_of    = fstab.volume_of,
                getuid       = os.getuid,
                environ      = self.environ,
                mount_points = mount_points
                )
        return all_trash_directories.all_trash_directories()

    def trashed_files(self, trash_dir) :
        for info_file in trash_dir.all_info_files():
            try:
                yield self.make_trashed_file(info_file, trash_dir.volume)
            except ValueError:
                trash_dir.logger.warning("Non parsable trashinfo file: %s" % info_file)
            except IOError as e:
                trash_dir.logger.warning(str(e))
    def make_trashed_file(self,
                          trashinfo_file_path,
                          trash_dir_volume):

        trash_info = TrashInfoParser(self.contents_of(trashinfo_file_path),
                                     trash_dir_volume)

        original_location = trash_info.original_location()
        deletion_date     = trash_info.deletion_date()
        backup_file_path  = backup_file_path_from(trashinfo_file_path)

        return TrashedFile(original_location, deletion_date,
                trashinfo_file_path, backup_file_path)
    def report_no_files_found(self):
        self.println("No files trashed from current dir ('%s')" % self.curdir())
    def println(self, line):
        self.out.write(line + '\n')
    def printerr(self, msg):
        self.err.write('%s\n' % msg)

from .trash import parse_path
from .trash import parse_deletion_date
class TrashInfoParser:
    def __init__(self, contents, volume_path):
        self.contents    = contents
        self.volume_path = volume_path
    def deletion_date(self):
        return parse_deletion_date(self.contents)
    def original_location(self):
        path = parse_path(self.contents)
        return os.path.join(self.volume_path, path)

class AllTrashDirectories:
    def __init__(self, volume_of, getuid, environ, mount_points):
        self.volume_of    = volume_of
        self.getuid       = getuid
        self.environ      = environ
        self.mount_points = mount_points
    def all_trash_directories(self):
        trash_directories = TrashDirectories(volume_of = self.volume_of,
                                             getuid    = self.getuid,
                                             environ   = self.environ)
        collected = []
        def add_trash_dir(path, volume):
            collected.append(TrashDirectory(path, volume))

        trash_directories.home_trash_dir(add_trash_dir)
        for volume in self.mount_points:
            trash_directories.volume_trash_dir1(volume, add_trash_dir)
            trash_directories.volume_trash_dir2(volume, add_trash_dir)

        return collected

class TrashedFile:
    """
    Represent a trashed file.
    Each trashed file is persisted in two files:
     - $trash_dir/info/$id.trashinfo
     - $trash_dir/files/$id

    Properties:
     - path : the original path from where the file has been trashed
     - deletion_date : the time when the file has been trashed (instance of
                       datetime)
     - info_file : the file that contains information (instance of Path)
     - actual_path : the path where the trashed file has been placed after the
                     trash opeartion (instance of Path)
     - trash_directory :
    """
    def __init__(self, path, deletion_date, info_file, actual_path):
        self.path = path
        self.deletion_date = deletion_date
        self.info_file = info_file
        self.actual_path = actual_path
        self.original_file = actual_path

def restore(trashed_file, path_exists, fs):
    if path_exists(trashed_file.path):
        raise IOError('Refusing to overwrite existing file "%s".' % os.path.basename(trashed_file.path))
    else:
        parent = os.path.dirname(trashed_file.path)
        fs.mkdirs(parent)

    fs.move(trashed_file.original_file, trashed_file.path)
    fs.remove_file(trashed_file.info_file)

