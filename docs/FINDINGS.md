# Findings and exact scope

## 1. Transfer is not execution

The libirecovery CLI could return success in situations where the underlying operation had not advanced the stage. The investigation switched to checking library results and the resulting identity/mode.

Observed for this device/build:

| Stage | Mode | IBFL | SRTG |
|---|---|---|---|
| BootROM DFU | DFU | 0x1c | iBoot-1992.0.0.1.19 |
| Executed iBSS | DFU | 0x1d | N/A |
| Executed iBEC | Recovery | 0x1c | N/A |

PID `0x1227` alone does not distinguish BootROM DFU from an executed iBSS. A transient query once produced CPID 0x8900 and ECID 0; it was rejected as invalid identification, not accepted as a different device.

## 2. Instruction visibility matters

At `0x100007e98`, a data read found `000080d2` (`mov x0, #0`). An execution probe that deliberately prepared the matching epilogue frame still returned the original test value `0x1234`. After `dc cvau` for that address followed by `dsb sy; ic iallu; dsb sy; isb`, it returned 0. The modified loader then executed.

This is a bounded observation on this A8 session, not a claim that every gaster failure is a cache problem. An earlier variant that failed during exploitation was inconclusive. No BootROM dump or copied gaster executable is included in this repository.

## 3. Generator, BNCN and BNCH

For the 20-byte nonce relationship examined here:

```text
raw_generator = uint64_generator encoded as 8 little-endian bytes
BNCH_expected = SHA1(raw_generator)
```

`IM4R.BNCN` stores the eight bytes. A textual `0x...` generator is a number, not the bytes of the text. Reversing the display order is a representation issue, not an alternative hash algorithm. For 32-byte or otherwise different nonce formats, this repository's A8 check is unsupported.

The final generator was `0x858d326c58e5be63`; its raw bytes were `63bee5586c328d85`. Its expected APNonce/BNCH was `067fee9d13dbc3ae55163a84cfb5c0631522e1f2`.

A matching relationship is necessary evidence for the audited case, but is not an Apple signature verification or proof of bootability. Do not try to recover an unknown generator from a SHA1 digest by guessing, and do not change only BNCN while leaving an incompatible ticket.

## 4. The running diagnostic context is part of the restore

The generic context had `BOOT_MANIFEST_HASH=63f4c02000efdbd486f301f0d9f16f482ffc6077`. A new ticket matching the measured BNCN still failed runtime metadata evaluation with 13 because the running context was not aligned.

The final context had:

```text
BOOT_NONCE=63bee5586c328d85
BOOT_MANIFEST_HASH=55e9f7a41cf94dcae269a6596599153db2fa4e3d
```

Both the nonce relation and SHA1 of the actual ticket matched this context. Metadata evaluation then returned 0. Rebooting or changing bootstrap components can invalidate previous measurements; remeasure after the transition.

## 5. Console output can be misleading

`ea0f64a4253252:453` was initially called a rejection in the working notes. Disassembly corrected that interpretation: the wrapper prints `%llx:%d\n` unconditionally **before** parsing a command. The restricted command table does not include `help`.

`getenv` may leave an old `cmd-results` response untouched when a variable is absent or rejected. Thus a repeated build-version string is not the requested generator. Library transport success does not establish that `setenv` changed a value. Verify the exact value and, decisively, the APNonce after reloading iBEC.

## 6. Exact reviewed iBoot images and RAM-only adjustment

Firmware: 15.8.8 / 19H422, iBoot-7459.140.15, base `0x870000000`. The decrypted iBoot and iBEC compared byte-for-byte identical in this case.

| File/stage | SHA256 |
|---|---|
| Official decrypted iBoot/iBEC input | `4aa54791904b6030b3c08f85f666885e92dcde7421504348d23829acacf3ec00` |
| Local patcher output, `-b '-v' -n -f` | `8d6f8239cf6630fe33c23b3eac7efb1fd83b682e324375bf94163d38010840e2` |
| Same output with the additional nonce allowlist pointer | `42553f871d94486c5e0c778de673ec6f38abedc2762c7d3c83e0c1ebcd8c49c0` |

The local patcher identified itself as commit `7fd877ee7d57a91d2506155752077aad51f896aa-39`. Its `-n` applied the freshnonce patch and several NVRAM checks, but another write check at `0x870001d00` still only allowed `auto-boot`, `boot-args`, `debug-uarts`, and `pwr-path`.

The additional change replaced the `pwr-path` pointer at file offset `0x54040`:

```text
before: 476a057008000000
after:  9a6a057008000000
```

The destination is the existing `com.apple.System.boot-nonce` string. No new executable code was added by this table change. It removed `pwr-path` from that particular RAM loader's write allowlist and added the generator instead. This modified loader was **not flashed**. A separate restore-arguments variant kept `rd=md0 ... -restore` and the same generator-preservation behavior for the diagnostic boot.

The generic `-l` local-boot option was not needed for this. A test including it left a yellow screen and no USB response. Do not equate that trial with a full normal boot or recommend `-l` as a generic command-permission fix.

## 7. SEP and ART evidence

A parseable ART and `boot-check` preflight are not proof that SEP or iPadOS will actually run. In this case `SEPOS is alive` provided additional evidence of SEP startup during one test.

The local seputil's help suggested a filename after `--boot-check`/`--dump-fw`, but its option table treated those as no-argument options and resolved a path from the running bootstrap. A temporary path-only diagnostic copy selected the installed SEP file; validation code was unchanged. This workaround was not installed in iPadOS.

`--rom status` after SEP startup caused a diagnostic panic. Do not repeat that query after starting sepOS based on this case. A broad bundled `ioreg` probe caused another diagnostic panic; the source property reader here avoids opening user clients.

ART was not manually cleared, no counter self-test was run, and no Activation Lock/account mechanism was changed. The earlier truncated ART capture was not evidence of corruption; later complete reads parsed successfully.
