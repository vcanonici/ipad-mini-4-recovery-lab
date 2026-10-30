# iPad mini 4 Recovery Lab

A documented recovery investigation for **iPad mini 4 Wi‑Fi — iPad5,1 / j96ap / A8 (CPID 0x7000, BDID 0x08)** after an interrupted surrealra1n downgrade.

[Português](README.pt-BR.md) · [Case timeline](docs/CASE-STUDY.md) · [Technical findings](docs/FINDINGS.md) · [Recovery workflow](docs/WORKFLOW.md) · [Evidence](evidence/README.md)

**If this investigation saves you time, please give this repository a ⭐.** Contributions with reproducible observations are welcome.

## Actual outcome

On 2026-10-30, iOS **15.8.8 / 19H422** completed a full restore, verification and system-volume sealing. The restore client exited successfully. A subsequent read-back audit confirmed:

- Stored LLB, iBoot and SEP payloads were byte-identical to the official IPSW components.
- Those components, ART and the active Preboot directory agreed on the restore ticket.
- `SHA1(IM4R.BNCN)` matched the 20-byte `IM4M.BNCH` in both stored LLB and iBoot.

**Normal boot is now confirmed by the owner.** After charging, the owner reported: “bootou e ta a funcionar” (“it booted and is working”). Device configuration was deferred until it had more charge. This is an owner-observed boot confirmation, not a complete hardware, activation or long-term stability test.

This is a case study of **one iPad5,1**, not a universal repair recipe. The iPad mini 4 cellular model (`iPad5,2 / j97ap`) and other firmware builds were not validated. Fixed offsets below apply only to the exact reviewed image hashes.

## What made this case difficult

1. A successful USB transfer did not prove that iBSS executed. Check `IBFL`, `SRTG`, mode and the exact device identity.
2. A BootROM patch appeared in a data read while instruction execution still used the original instruction. A separate execution probe distinguished the two; cache synchronization changed the result and allowed the modified chain to execute.
3. The earlier successful restore had **internally inconsistent boot nonces**: the ticket had been obtained before the diagnostic bootstrap changed the boot context. Official payloads and matching ticket hashes alone did not catch this.
4. The diagnostic kernel's `boot-manifest-hash` also had to match the new ticket. Metadata evaluation returned `EACCES` (13) with a mismatched context and returned 0 after alignment.
5. `getenv` could expose a stale previous response for an absent or rejected variable. `setenv` transport success was not proof that the generator changed.
6. The local patcher's `-n` left another command-variable allowlist in this iBoot build. A narrowly scoped RAM-only table change enabled setting the generator. Its value was then confirmed through read-back **and the APNonce after reloading iBEC**.

Read [the findings](docs/FINDINGS.md) before attempting to reproduce any part of the workflow. The two diagnostic panics caused by our own probes are documented separately from the original failure. The final correction was followed by the owner-confirmed normal boot.

## Included tools

The Python tools run on your computer and do not access USB, write firmware, set NVRAM or contact Apple:

```sh
python3 tools/inspect_img4.py LLB.img4 --require-nonce
python3 tools/inspect_img4.py iBoot.img4 --require-nonce --stock-im4p official-iBoot.im4p
python3 tools/prepare_nonce_allowlist.py iBoot-nvram iBoot-nonce-allowlist
python3 -m unittest discover -s tests -v
```

`inspect_img4.py` reports structural fields, hashes and the eight-byte generator relationship. **It does not verify Apple's signature, certificate chain, signing status, SEP health or bootability.** It rejects malformed/truncated DER and ambiguous nonce fields. The patch preparation tool refuses any input other than the reviewed build/hash and only creates a local output file.

`tools/read_boot_context.c` is source for a read-only utility run inside an already working diagnostic environment. It reads two properties from `IODeviceTree:/chosen`; it never opens an IOService user client. See [tool usage](docs/TOOLS.md).

No Apple firmware, decrypted bootloader, BootROM dump, personalized IMG4, SHSH ticket or third-party executable is redistributed here. Obtain firmware and upstream tools from their original sources. Technical identifiers and nonces from this owned-device case are deliberately retained in the evidence at the owner's request; they must not be copied to another device.

## Start here

- [Case study and chronology](docs/CASE-STUDY.md)
- [Findings, failed assumptions and exact build details](docs/FINDINGS.md)
- [Workflow and verification points](docs/WORKFLOW.md)
- [Tool scope and examples](docs/TOOLS.md)
- [Primary sources and upstream credits](docs/REFERENCES.md)
- [Complete selected logs and audit reports](evidence/README.md)

The material covers restoring a device you own. It does not remove Activation Lock or replace account recovery. Original project licenses still apply to all upstream tools; the MIT license here covers this repository's original text and code.

## Help improve the record

Please open an issue with your model, board, build, last verified stage and the exact error. Separate a transfer result from an execution result, and a completed restore from a successful normal boot. A report from another device is new evidence, not automatic confirmation of this case.

And if this helped: **please leave a ⭐ so other iPad mini 4 owners can find it.**
