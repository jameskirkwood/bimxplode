from .util import cut, unpack
import logging

def extract(buffer):

  buffer = memoryview(buffer)

  try:
    magic, count, u32_8, p = unpack('<4s2I', buffer)
    assert magic == b'OFS\x01'
  except:
    raise ValueError('No Offsets.bin header present.')

  chunks = {}
  for i in range(count):

    sp, name, chunk_offset, p = unpack('<b3sI', p)
    if not name[0]: break
    name = name[::-1]
    assert sp == 32
    logging.info(f'offsets for {repr(name)} begin at {chunk_offset}')

    q = buffer[chunk_offset:]
    name2, sbo, count, q = unpack('<3sbI', q)
    assert name2 == name and sbo == 1

    offsets = []
    for j in range(count):
      index, offset2, q = unpack('<iI', q)
      offsets.append((index, offset2))

    chunks[name.decode()] = offsets

  return chunks
