from . import ofs
from .. import quicklz
from .util import cut, unpack
from pathlib import Path
import json

def extract(buffer):
  """Yield all members in a ZRES archive as (data, name, offset, size, decompressed_size) \
tuples."""

  buffer = memoryview(buffer)

  try:
    payload, header = cut(buffer, -8)
    file_count, magic, _ = unpack('<I4s', header)
    assert magic == b'ZRES'
  except:
    raise ValueError('No ZRES header present.')

  p = payload[-520 * file_count:]

  files = {}
  for i in range(file_count):
    name, offset, size, p = unpack('<512s2I', p)
    name = name[:name.index(0)].decode()
    if not name: continue

    data = payload[offset:][:size]

    if data[:4] == b'QLZ\x01':
      data = quicklz.decompress(bytes(data[4:]))
      decompressed_size = len(data)
    else:
      decompressed_size = None

    files[name] = (data, offset, size, decompressed_size)

    yield data, name, offset, size, decompressed_size

  export_bin = files['Export.bin'][0]
  offsets_bin = files['Offsets.bin'][0]
  assert offsets_bin[:4] == b'OFS\x01'

  export_map = []
  for key, offsets in ofs.extract(offsets_bin).items():
    export_map.extend([(offset, key, id) for id, offset in offsets])
  export_map.sort()

  for i, v in enumerate(export_map):
    offset, key, id = v
    if i + 1 < len(export_map):
      size = export_map[i + 1][0] - offset
    else:
      size = len(export_bin) - offset
    
    if key == 'TEX' and id != -1:
      data = export_bin[offset:][:size]
      name, a, b, c, d, e, f, sbz, data = unpack('<128s2I4H28s', data)
      name = name[:name.index(0)].decode()
      yield data, Path(key) / name, offset, size, None
