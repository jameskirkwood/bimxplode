from argparse import ArgumentParser
from pathlib import Path
import struct
from collections import Counter
import sys

ap = ArgumentParser()
ap.add_argument('file')
args = ap.parse_args()

path = Path(args.file)
data = open(path, 'rb').read()

magic, version, table_header_offset = struct.unpack('<4sIQ', data[:16])
assert magic == b'ADS.'

unknown1, unknown2, count = struct.unpack_from('<Q42sQ', data, offset=table_header_offset)
open('sdatable-hdr', 'wb').write(unknown2)

table_offset = table_header_offset + 58

def unpack_array(fmt, data, offset, count):
    end = offset + struct.calcsize(fmt) * count
    return [t[0] for t in struct.iter_unpack(fmt, data[offset:end])], end

sizes, cursor = unpack_array('<I', data, table_offset, count)

k = 0x80000000
p = cursor
for addr in range(cursor, len(data) - 16):
    if struct.unpack_from('<4I', data, offset=addr) == (k, 0, k, 0):
        # print(data[addr - 16 : addr], data[addr + 16 : addr + 32])
        print(addr - p)
        p = addr
