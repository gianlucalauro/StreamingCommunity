# 24.05.24

import struct

class Colors:
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    LIGHT_GRAY = "\033[37m"
    DARK_GRAY = "\033[90m"
    LIGHT_RED = "\033[91m"
    LIGHT_GREEN = "\033[92m"
    LIGHT_YELLOW = "\033[93m"
    LIGHT_BLUE = "\033[94m"
    LIGHT_MAGENTA = "\033[95m"
    LIGHT_CYAN = "\033[96m"
    WHITE = "\033[97m"
    RESET = "\033[0m"


def extract_png_chunk(png_with_wvd, out_wvd_path):
    with open(png_with_wvd, "rb") as f: data = f.read()
    pos = 8
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos+4])[0]
        chunk_type = data[pos+4:pos+8]
        chunk_data = data[pos+8:pos+8+length]
        if chunk_type == b"stEg":
            with open(out_wvd_path, "wb") as f: f.write(chunk_data)
            return
        pos += 12 + length


def _g(_=None):
    a = [100,101,118,105,99,101,46,119,118,100]
    return ''.join(map(chr, a))