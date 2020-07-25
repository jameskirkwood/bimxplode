import struct
import numpy as np

def cut(buffer, offset):
  return buffer[:offset], buffer[offset:]

def unpack(format, buffer):
  size = struct.calcsize(format)
  return *struct.unpack(format, bytes(buffer[:size])), buffer[size:]

def product(t):
  if len(t): return t[0] * product(t[1:])
  else: return 1

def frombuffer(buffer, count=None, dtype=None, shape=(-1)):
  if count is None:
    count = -1 if -1 in shape else product(shape)
  r = np.frombuffer(buffer, count=count, dtype=dtype).reshape(shape)
  return r, buffer[int(np.dtype(dtype).itemsize) * count:]

def padded_str(s):
  return s[:s.index(0)].decode()
