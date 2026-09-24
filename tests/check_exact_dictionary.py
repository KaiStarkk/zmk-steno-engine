#!/usr/bin/env python3
"""Check the C decoder against source Lapwing entries and absent outlines.

Usage: python3 tests/check_exact_dictionary.py lapwing.json compiled_blob_directory
Requires cc on PATH. The compiled blobs must contain Lapwing only.
"""
import json
import random
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from compile_v4 import encode_key


def main():
    dictionary = json.loads(Path(sys.argv[1]).read_text())
    directory = Path(sys.argv[2]).resolve()
    expected = {}
    for outline, translation in dictionary.items():
        expected.setdefault(encode_key(outline)[1], translation.encode())
    unknown = set()
    # Near-matches and appended strokes exercise candidates which previously
    # could retract correct output when their four-bit fingerprints collided.
    for key in expected:
        mutated = bytearray(key)
        mutated[0] ^= 1
        for candidate in (bytes(mutated), key + struct.pack('<I', 1)):
            if candidate not in expected:
                unknown.add(candidate)
    rng = random.Random(0x5634)
    while len(unknown) < 300000:
        count = rng.choice((1, 1, 2, 3))
        candidate = b''.join(struct.pack('<I', rng.randrange(1, 1 << 23))
                             for _ in range(count))
        if candidate not in expected:
            unknown.add(candidate)
    vectors = directory / 'exact-vectors.bin'
    with vectors.open('wb') as stream:
        stream.write(struct.pack('<II', 0x56543456, len(expected) + len(unknown)))
        for known, entries in ((1, expected.items()),
                               (0, ((key, b'') for key in sorted(unknown)))):
            for key, text in entries:
                stream.write(struct.pack('<BBBB', 1, len(key) // 4, known, 0))
                stream.write(key)
                stream.write(struct.pack('<H', len(text)))
                stream.write(text)
    executable = directory / 'test-exact-dictionary'
    subprocess.run(['cc', '-O2', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                    '-I', str(ROOT / 'src'),
                    str(ROOT / 'tests/test_dict_v4.c'),
                    str(ROOT / 'src/dict_v4.c'), str(ROOT / 'src/inflate.c'),
                    '-o', str(executable)], check=True)
    subprocess.run([str(executable), str(directory / 'steno_v4_left.bin'),
                    str(directory / 'steno_v4_right.bin'), str(vectors)], check=True)


if __name__ == '__main__':
    main()
