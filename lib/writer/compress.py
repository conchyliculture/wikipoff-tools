# encoding: utf-8

import pylzma
import struct
from io import BytesIO

def LzmaCompress(data):
    data = data.encode(u'utf-8')
    c = pylzma.compressfile(BytesIO(data), eos=0)
    result_bin = c.read(5)
    result_bin += struct.pack(u'<Q', len(data))
    compressed_data = result_bin + c.read()
    return compressed_data

def LzmaDecompress(data):
    return pylzma.decompress(data)

