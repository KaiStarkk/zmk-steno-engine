# Exact membership extension (binary version 5)

The `dict_v4` backend now emits and requires binary version 5. Both halves
must be rebuilt together. Version 4 blobs are rejected. Existing section IDs
1–7 and the split BLE protocol retain their layouts.

Section 8 (`KEYS`) stores the exact union of dictionary outlines on the central
half. Its directory parameter is the block count. The section starts with
`block_count + 1` little-endian 32-bit offsets relative to the section start;
the final offset equals the section length. Blocks are sorted by their first
outline's byte order.

Each block contains a one-byte first-outline length, that outline (32-bit
little-endian stroke masks), then a raw DEFLATE stream. The stream holds up
to 256 sorted outlines, each represented by a one-byte shared-prefix length,
one-byte suffix length and suffix bytes. The first record has prefix zero.
Inflated blocks must fit 4096 bytes; the compiler rejects larger blocks.

Lookup retains the four-bit fingerprint as a cheap rejection filter, then
binary-searches block leaders and compares the complete decoded outline.
Only an exact match may return a local or remote hit. Missing sections or
malformed blocks cannot produce a translation. Membership verification uses
one static 4096-byte buffer, under the backend's serialized lookup contract.
No additional BLE request is needed for membership checking.

The compiler verifies every source entry and requires zero unknown-outline
accepts. `tests/check_exact_dictionary.py` also runs the actual C decoder
against all Lapwing entries and 300,000 absent outlines, including mutated
and extended real outlines, with address and undefined-behavior sanitizers.

Exact membership consumes additional central flash. The complete Lapwing
base fits the Sweep's configured budgets; other dictionary selections still
fail compilation if either budget is exceeded, without trimming entries.
