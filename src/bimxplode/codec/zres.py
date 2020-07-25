from . import ofs
from .. import quicklz
from .util import cut, unpack, frombuffer
from pathlib import Path
import json
import numpy as np
from collections import namedtuple
from tabulate import tabulate

class Vertex:

  def __init__(self, attrs=None):

    if attrs is not None:
      self.texcoord = attrs[:2]
      self.normal = attrs[2:5]
      self.position = attrs[5:]

  def __repr__(self):

    return f'Vertex({self.texcoord}, {self.normal}, {self.position})'

class Mesh:

  def __init__(self, buffer):

    _ = buffer
    i0, vertex_count, triangle_idx_count, edge_idx_count, i4, i5, q, _ = unpack('<I5HQ', _)
    self.unknown_info = (i0, i4, i5, q)
    self.unknown_matrix, _ = frombuffer(_, count=9, dtype=np.float32, shape=(3, 3))
    unknown_len, _ = unpack('<H', _)

    vertex_array, _ = frombuffer(_, dtype=np.float32, shape=(vertex_count, 8))
    self.vertices = [Vertex(a) for a in vertex_array]

    self.triangles, _ = frombuffer(_, count=triangle_idx_count, dtype=np.uint16, shape=(-1, 3))
    self.edges, _ = frombuffer(_, count=edge_idx_count, dtype=np.uint16, shape=(-1, 2))

    self.unknown_array = []
    for i in range(unknown_len):
      *item, _ = unpack('<2Hf', _)
      self.unknown_array.append(i)

    self.end = _

  def list(self):

    print(self.unknown_info, len(self.vertices), len(self.triangles), len(self.edges),
      len(self.unknown_array))

class AABB:

  def __init__(self, array):

    self.min, self.max, self.mid = tuple(array[:3])
    self.unknown = array[3:]

class Element:

  def __init__(self, buffer, id):

    self.id, sbz, _ = unpack('<I16s', buffer)
    assert self.id == id
    assert not any(sbz)

    aabb, _ = frombuffer(_, dtype=np.float32, shape=(5, 3))
    self.aabb = AABB(aabb)

    fa, fb, c, element_id, guid, sbz, _ = unpack('<2fI128s36s12s', _)
    self.element_id = element_id[:element_id.index(0)].decode()
    self.guid = guid.decode()
    assert not any(sbz)

    self.type, sbz, _ = unpack('<H82s', _)
    assert not any(sbz)

    *unknown32, magic, mesh_count, _ = unpack('<12I3sI', _)
    assert magic == b'MSH'

    self.unknown_info = (fa, fb, c, unknown32)

    self.meshes = []
    for j in range(mesh_count):
      mesh = Mesh(_)
      _ = mesh.end
      self.meshes.append(mesh)

    self.end = _

  def list(self):

    print(self.id, self.element_id, self.type, self.unknown_info)
    for mesh in self.meshes: mesh.list()

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

  _ = payload[-520 * file_count:]

  files = {}
  for i in range(file_count):

    name, offset, size, _ = unpack('<512s2I', _)
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

    data = export_bin[offset:][:size]

    try:

      if key == 'TEX' and id != -1:

        name, a, b, c, d, e, f, sbz, data = unpack('<128s2I4H28s', data)
        name = name[:name.index(0)].decode()
        yield data, Path(key) / name, offset, size, None

      elif key == 'ELM':

        if id == -1:
          magic, i0, i1, _ = unpack('<3s2I', data)
          assert magic == b'ELM'
          assert len(_) == 0
          print(f'ELM {i0}, {i1}')
        else:
          element = Element(data, id)
          element.list()

    except AssertionError as e:

      print(v)
      raise e
