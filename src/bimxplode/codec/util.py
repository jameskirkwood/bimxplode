import struct

def cut(buffer, offset):
    return buffer[:offset], buffer[offset:]

def unpack(format, buffer):
    size = struct.calcsize(format)
    return *struct.unpack(format, bytes(buffer[:size])), buffer[size:]
