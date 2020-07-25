from .. import quicklz
from .util import *
import numpy as np

table = '{:10} {:10} {:10} {:6}  {}'

def extract(cli, buffer):
  """Yield all members in a ZRES archive as (name: str, data: bytes|memoryview) tuples."""

  buffer = memoryview(buffer)

  try:
    payload, header = cut(buffer, -8)
    file_count, magic, _ = unpack('<I4s', header)
    assert magic == b'ZRES'
  except:
    raise ValueError('No ZRES header present.')

  cli.list(table.format('OFFSET', 'BYTES_USED', 'FILE_SIZE', 'RATIO', 'NAME'))

  _ = payload[-520 * file_count:]

  for i in range(file_count):

    name, offset, size, _ = unpack('<512s2I', _)
    name = padded_str(name)
    if not name: continue

    data = payload[offset:][:size]

    if data[:4] == b'QLZ\x01':
      data = quicklz.decompress(bytes(data[4:]))

    final_size = len(data)
    ratio = '%6.2f' % (final_size / size)

    cli.list(table.format(offset, size, final_size, ratio, name))
    yield name, data
