# encoding: utf-8

import os
import sys
sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        u'..', u'python{0:d}.{1:d}'.format(
            sys.version_info.major, sys.version_info.minor),
        u'site-packages'))
try:
    import pylzma
except ImportError as e:
    print(u'Try to run make_pylzma.sh')
    raise e
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
