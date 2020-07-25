from .codec import bxpk, zres, bimx
from argparse import ArgumentParser
from fnmatch import fnmatch
from pathlib import Path
import sys

class CLI():

  def __init__(self, description):

    self.usage = '\n    %(prog)s --help'
    self.description = description + """
      Any input file argument also accepts the string '-', denoting standard input."""
    self.create_callback = None
    self.extract_callback = None
    self.create_arguments = None
    self.extract_arguments = None

  def add_create_callback(self, callback, usage):

    self.create_callback = callback
    self.usage += usage

  def add_extract_callback(self, callback, usage):

    self.extract_callback = callback
    self.usage += usage

  def add_parser(self):

    self.parser = ArgumentParser(
      add_help=False, usage=self.usage, description=self.description)

    commands = self.parser.add_argument_group(title='commands')
    commands.add_argument('-h', '--help', action='help', help='display this help text')

    if self.create_callback:
      commands.add_argument('-c', '--create', metavar='file', nargs='+', default=[],
        help='create a new archive containing the given files')
      g = self.parser.add_argument_group(title='modifiers for -c')
      g.add_argument('-f', '--file', type=Path, metavar='file',
        help='write the archive to the specified file')
      self.create_arguments = g

    if self.extract_callback:
      commands.add_argument('-x', '--extract', metavar='file',
        help='extract archived files into the destination directory (or list them with -l)')
      g = self.parser.add_argument_group(title='modifiers for -x')
      g.add_argument('-d', '--destination', type=Path, metavar='dir',
        help="extract into 'dir' (default is named after the archive with '.d' appended, or "
        "the current directory if standard input is used)")
      g.add_argument('-e', '--exclude', metavar='name', nargs='+', action='extend', default=[],
        help='exclude members matching the provided names or globs (overrides -i)')
      g.add_argument('-i', '--include', metavar='name', nargs='+', action='extend', default=[],
        help='limit the operation to members matching the provided names or globs')
      g.add_argument('-l', '--list', action='store_true',
        help='list members instead of writing them to files')
      self.extract_arguments = g

    if g := (self.create_arguments or self.extract_arguments):
      if self.create_arguments and self.extract_arguments:
        g = self.parser.add_argument_group(title='modifiers for -c and -x')
      g.add_argument('-j', '--flatten', action='store_true',
        help='strip directories from member names')
      g.add_argument('-o', '--stdout', action='store_true',
        help='do not create files, write file contents to standard output')
      g.add_argument('-r', '--recursive', action='store_true',
        help='search directories for input files (directories are skipped by default)')
      self.create_and_extract_arguments = g

  def parse_args(self):

    a = self.args = self.parser.parse_args()

    if not a.include: # because 'default' does not work like this
      a.include = ['*']

    if self.create_callback:
      self.create_files = list(self.iter_input_files(self.args.create))

    if self.extract_callback and a.extract and not a.destination:
      if a.extract == '-':
        a.destination = Path.cwd()
      else:
        p = Path(a.extract)
        a.destination = p.with_name(p.name + '.d')

  def iter_path(self, p):

    if p.is_dir():
      if self.args.recursive:
        for p in p.iterdir():
          yield from self.iter_path(p)
      else:
        self.warn(f'skipping directory: {p}')
    elif p.is_file():
      yield p
    else:
      self.warn(f'skipping non-regular file: {p}')

  def maybe_flatten(self, path):

    return path.name if self.args.flatten else path

  def iter_input_files(self, names):

    for name in names:
      if name == '-':
        yield sys.stdin.buffer, '<stdin>'
      else:
        for p in self.iter_path(Path(name)):
          yield p.open('rb'), self.maybe_flatten(p)

  def open_input_file(self, name):

    if name == '-':
      return sys.stdin.buffer
    return Path(name).open('rb')

  def open_output_file(self, path):

    if self.args.stdout:
      return sys.stdout.buffer
    elif path:
      path.parent.mkdir(parents=True, exist_ok=True)
      return path.open('wb')

  def maybe_emit_file(self, name, data):

    if not any(fnmatch(name, p) for p in self.args.include): return
    if any(fnmatch(name, p) for p in self.args.exclude): return

    if not self.args.list:
      self.open_output_file(self.args.destination / self.maybe_flatten(Path(name))).write(data)

  def execute_command(self):

    if self.create_callback and self.args.create:
      self.create_callback(self, self.open_output_file(self.args.file), self.create_files)
    elif self.extract_callback and self.args.extract:
      self.extract_callback(self, self.open_input_file(self.args.extract))
    else:
      self.parser.error('no command specified')

  def list(self, line):

    if self.args.list:
      print(line)

  def warn(self, message):

    print(f'{self.parser.prog}: warning: {message}', file=sys.stderr)

def bxpk_main():

  def create(cli, output_file, files):

    members = [bxpk.Member(file.read(), name=name) for file, name in files]

    if output_file:
      bxpk.archive(members, output_file)
    else:
      cli.warn('no output mode specified, listing included files instead')
      for member in members:
        print(f'{len(member.data):10} {member.name}')

  def extract(cli, file):

    for member in bxpk.extract(cli, file.read()):
      cli.maybe_emit_file(member.name, member.data)

  cli = CLI("""
    This command creates and extracts BXPK archives, which are used to package some ARCHICAD \
    BIMx hyper-models. The design of the program is based on reverse-engineering of BIMx \
    model files.""")

  cli.add_create_callback(create, """
    %(prog)s -c file ... [-j] [-o | -f out.bimx] [-r]""")
  cli.add_extract_callback(extract, """
    %(prog)s -x in.bimx [-{i|e} name ...] ... [-j] [-l | -o | -d dir]""")

  cli.add_parser()

  cli.parse_args()
  cli.execute_command()

def zres_main():

  def extract(cli, file):

    if cli.args.gltf:
      files = dict(zres.extract(cli, file.read()))
      model = bimx.Model(cli, files['Offsets.bin'], files['Export.bin'])
    else:
      for name, data in zres.extract(cli, file.read()):
        cli.maybe_emit_file(name, data)

  cli = CLI("""
    This command extracts ZRES archives, which are used to package some ARCHICAD \
    BIMx hyper-models. The design of the program is based on reverse-engineering of BIMx \
    model files.""")

  cli.add_extract_callback(extract, """
    %(prog)s -x in.bimx [-{i|e} name ...] ... [-j] [--gltf] [-l | -o | -d dir]""")

  cli.add_parser()
  cli.extract_arguments.add_argument('--gltf', action='store_true',
    help='instead of extracting files, extract mesh and texture data as a glTF model')

  cli.parse_args()
  cli.execute_command()
