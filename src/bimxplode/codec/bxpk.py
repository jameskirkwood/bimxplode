from .util import cut, unpack
import hashlib
import logging
import struct

class Member:

  def __init__(self, buffer, inode=None, name=None):

    if inode:

      name_len, p = unpack('<I', inode)
      name, p = cut(p, name_len)
      u64_0, size, offset, digest, p = unpack('<3Q40s', p)

      self.unknown_u64_0 = u64_0
      self.name = name.tobytes().decode()
      self.digest = digest.decode()
      self.inode_end = p
      self.offset = offset
      self.data = buffer[offset:][:size]

    elif name:

      self.unknown_u64_0 = 0
      self.name = str(name)
      self.data = buffer
      self.digest = self.sha1hash()

  def sha1hash(self):

    h = hashlib.sha1()
    h.update(bytes(self.data))
    return h.hexdigest()

  def check_digest(self):

    return self.digest == self.sha1hash()

  def make_inode(self, offset):

    inode = struct.pack('<I', len(self.name))
    inode += bytes(self.name, 'utf-8')
    inode += struct.pack('<3Q40s',
      self.unknown_u64_0,
      len(self.data),
      offset,
      bytes(self.digest, 'utf-8'))

    return inode

def extract(buffer):
  """Yield all members in a BXPK archive as Member objects."""

  buffer = memoryview(buffer)

  try:
    payload, header = cut(buffer, -16)
    file_count, index_size, u32_8, magic, _ = unpack('<3I4s', header)
    assert magic == b'KPXB'
  except:
    raise ValueError('No BXPK header present.')

  if u32_8 != 1:
    logging.warning(f'abnormal third header field: 0x{u32_8:08x} / {u32_8}')

  try:
    inode = payload[-index_size:]
    for i in range(file_count):
      yield (member := Member(payload, inode))
      inode = member.inode_end
  except:
    raise ValueError('Index corrupted.')

def archive(members, writer):
  """Create a BXPK archive containing all members in a list."""

  offset = 0
  inodes = []
  for member in members:
    writer.write(bytes(member.data))
    inodes.append(member.make_inode(offset))
    offset += len(member.data)

  for inode in inodes:
    writer.write(inode)
  
  header = struct.pack('<3I4s',
    len(members),
    sum(len(i) for i in inodes),
    1,
    b'KPXB')

  writer.write(header)
