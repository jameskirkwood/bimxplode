from .codec import bxpk, zres
from argparse import ArgumentParser
from fnmatch import fnmatch
from pathlib import Path
import logging
import sys

def main(description, create=None, extract=None):

  usage = """
    %(prog)s --help"""
  if create: usage += """
    %(prog)s -c file ... [-j] [-o | -f out.bimx] [-r]"""
  if extract: usage += """
    %(prog)s -x in.bimx [-{i|e} name ...] ... [-j] [-l | -o | -d dir]"""

  description += """
    Any input file argument also accepts the string '-', denoting standard input."""

  ap = ArgumentParser(add_help=False, usage=usage, description=description)

  g_commands = ap.add_argument_group(title='commands')
  g_commands.add_argument('-h', '--help', action='help', help='display this help text')

  if create:
    g_commands.add_argument('-c', '--create', metavar='file', nargs='+', default=[],
      help='create a new archive containing the given files')

    g_create = ap.add_argument_group(title='modifiers for -c')
    g_create.add_argument('-f', '--file', type=Path, metavar='file',
      help='write the archive to the specified file')

  if extract:
    g_commands.add_argument('-x', '--extract', metavar='file',
      help='extract members of each file into the destination directory (or list them with -l)')

    g_extract = ap.add_argument_group(title='modifiers for -x')
    g_extract.add_argument('-d', '--destination', type=Path, metavar='dir',
      help="extract into 'dir' (default is named after the archive with '.d' appended, or the "
      "current directory if standard input is used)")
    g_extract.add_argument('-e', '--exclude', metavar='name', nargs='+', action='extend',
      default=[],
      help='exclude members matching the provided names or globs (overrides -i)')
    g_extract.add_argument('-i', '--include', metavar='name', nargs='+', action='extend',
      default=[],
      help='limit the operation to members matching the provided names or globs')
    g_extract.add_argument('-l', '--list', action='store_true',
      help='list members instead of writing them to files')

  if create and extract:
    g_both = ap.add_argument_group(title='modifiers for -c and -x')
  elif create:
    g_both = g_create
  elif extract:
    g_both = g_extract

  if create or extract:
    g_both.add_argument('-j', '--flatten', action='store_true',
      help='strip directories from member names')
    g_both.add_argument('-o', '--stdout', action='store_true',
      help='do not create files, write file contents to standard output')
    g_both.add_argument('-r', '--recursive', action='store_true',
      help='search directories for input files (directories are skipped by default)')

  g_dev = ap.add_argument_group(title='developer options')
  g_dev.add_argument('--debug', action='store_true',
    help='print a stack trace and exit immediately on error')
  g_dev.add_argument('--log-level', type=lambda a: getattr(logging, a), metavar='level',
    help='set the minimum priority logs to print (DEBUG | INFO | WARNING | ERROR | CRITICAL)')

  args = ap.parse_args()

  if not args.include:
    args.include = ['*']

  def iter_path(p):

    if p.is_dir():
      if args.recursive:
        for p in p.iterdir():
          for p in iter_path(p):
            yield p
      else:
        logging.warning(f'skipping directory: {p}')
    elif p.is_file():
      yield p
    else:
      logging.warning(f'skipping non-regular file: {p}')

  def maybe_flatten(path):

    return path.name if args.flatten else path

  def iter_input_files(names):

    for name in names:
      if name == '-':
        yield sys.stdin.buffer, '<stdin>'
      else:
        for p in iter_path(Path(name)):
          yield p.open('rb'), maybe_flatten(p)

  def open_input_file(name):

    if name == '-':
      return sys.stdin.buffer
    return Path(name).open('rb')

  if create: create_files = list(iter_input_files(args.create))

  logging.basicConfig(level=args.log_level, format='%(levelname)s: %(message)s')

  def open_output_file(path):

    if args.stdout:
      return sys.stdout.buffer
    elif path:
      path.parent.mkdir(parents=True, exist_ok=True)
      return path.open('wb')

  if extract and args.extract and not args.destination:
    if args.extract == '-':
      args.destination = Path.cwd()
    else:
      p = Path(args.extract)
      args.destination = p.with_name(p.name + '.d')

  def handle_member(name, data, summary):

    if not any(fnmatch(name, p) for p in args.include): return
    if any(fnmatch(name, p) for p in args.exclude): return

    if args.list:
      print(summary)
    else:
      open_output_file(args.destination / maybe_flatten(Path(name))).write(data)

  if create and args.create:
    create(open_output_file(args.file), create_files)
  elif extract and args.extract:
    extract(open_input_file(args.extract), handle_member)
  else:
    ap.error('no command specified')

def bxpk_main():

  def create(output_file, files):

    members = [bxpk.Member(file.read(), name=name) for file, name in files]

    if output_file:
      bxpk.archive(members, output_file)
    else:
      logging.warning('no output mode specified, listing included files instead...')
      for member in members:
        print(f'{len(member.data):10} {member.name}')

  def extract(file, handler):

    for member in bxpk.extract(file.read()):
      summary = f'{member.offset:10} {len(member.data):10} {member.name}'
      handler(member.name, member.data, summary)

  main("""
    This command creates and extracts BXPK archives, which are used to package some ARCHICAD \
    BIMx hyper-models. The design of the program is based on reverse-engineering of some BIMx \
    model files.""",
    create=create,
    extract=extract)

def zres_main():

  def extract(file, handler):

    for data, name, offset, size, decompressed_size in zres.extract(file.read()):
      if decompressed_size:
        ratio = '%.2f' % (decompressed_size / size)
      else:
        decompressed_size = ratio = ''
      summary = f'{offset:10} {size:10} {decompressed_size:10} {ratio:10} {name}'
      handler(name, data, summary)

  main("""
    This command extracts ZRES archives, which are used to package some ARCHICAD \
    BIMx hyper-models. The design of the program is based on reverse-engineering of some BIMx \
    model files.""",
    extract=extract)
