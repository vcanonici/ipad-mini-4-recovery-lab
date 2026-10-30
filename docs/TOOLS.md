# Included tools

## Host-side IMG4 inspection

Python 3.10+; standard library only. It opens files read-only and performs no network/USB operations.

```sh
python3 tools/inspect_img4.py LLB.img4 --require-nonce
python3 tools/inspect_img4.py iBoot.img4 --require-nonce   --stock-im4p official-iBoot.im4p --expect-ticket-sha1 YOUR_TICKET_SHA1
python3 tools/inspect_img4.py sep.img4
```

The output contains the IMG4 component type, SHA256 of the image and IM4P object, SHA1 of the IM4M object, BNCN/BNCH when available and the relation between them. An optional official IM4P comparison is byte-for-byte.

Exit codes: 0 for requested structural/relationship checks passing; 1 for I/O or malformed/ambiguous data; 2 for a failed requested comparison. A zero result does **not** mean an Apple signature or normal boot has been verified. Unsupported/missing nonce formats are reported explicitly; `--require-nonce` makes them fail rather than silently pass. Trailing bytes are rejected unless `--allow-trailing` is explicit, useful for a measured firmware-media dump containing additional data.

## Exact-build RAM table preparation

```sh
python3 tools/prepare_nonce_allowlist.py iBoot-nvram iBoot-nonce-allowlist
```

Input must be the specific reviewed iBoot64Patcher output described in FINDINGS.md. The tool validates the image hash, load address, existing allowlist pointer and destination string before writing a **new local file**. It never uploads anything and refuses to overwrite a destination. The additional JSON report records the two hashes and exact byte change.

The original Apple image and the intermediate patched executable are intentionally not distributed. Obtain the relevant inputs yourself; matching filenames do not establish a matching build.

## DeviceTree reader source

`read_boot_context.c` uses dynamic IOKit/CoreFoundation lookup and only reads `IODeviceTree:/chosen` properties. It requires CFData of exactly eight and twenty bytes and prints:

```text
BOOT_NONCE=<16 hexadecimal characters>
BOOT_MANIFEST_HASH=<40 hexadecimal characters>
```

It does not call IOServiceOpen, enumerate drivers, modify DeviceTree, access firmware storage or load SEP firmware. It expects an already working diagnostic environment. It is not a jailbreak or a way to enter that environment.

Build with a compatible Apple SDK/toolchain and sign for your own authorized diagnostic environment. For example, with an appropriate SDK path and clang:

```sh
clang -target arm64-apple-ios12.0 -isysroot "$IOS_SDK_PATH"   tools/read_boot_context.c -o read-boot-context
```

The compilation/signing setup is environment-dependent and that command is not a complete deployment procedure. No prebuilt executable or Apple SDK is shipped here. In the case, overwriting a previously executed file at the same path sometimes produced a SIGKILL; using a new filename avoided the stale code-signing/cache issue observed there. That was not evidence of a new SEP panic.

## Tests

```sh
python3 -m unittest discover -s tests -v
cc -Wall -Wextra -Werror -fsyntax-only tools/read_boot_context.c
```

Tests use synthetic DER; they contain no Apple tickets or device secrets. They exercise nonce match/mismatch, missing/ambiguous fields and truncated input. They do not simulate a real restore.
