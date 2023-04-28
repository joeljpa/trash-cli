from trashcli.trash import print_version


class PrintVersion:
    def __init__(self, out, argv0, version):
        self.out = out
        self.argv0 = argv0
        self.version = version

    def execute(self, parsed):
        print_version(self.out, self.argv0, self.version)
