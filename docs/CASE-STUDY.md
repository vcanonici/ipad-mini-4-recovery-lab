# Case study

## Device and original failure

- iPad mini 4 Wi‑Fi, iPad5,1, j96ap, A8, CPID 0x7000, BDID 0x08.
- ECID: `0x0009754808454226` / `2662227027247654`.
- Serial: `F9GSNGW3GHKL`.
- Original system observed through SSH: iOS 15.8.1 / 19H380.
- Attempted tethered downgrade: surrealra1n v2.2.3, target iOS 10.3.3 / 14G60, base iOS 15.8.8 / 19H422.
- The downgrade remained at zero progress after `Done sending NORData` for approximately 20 minutes. The owner then pressed Ctrl+C. The stall preceded the interruption.
- The wrapper printed completion and generated boot files despite the interruption. Its text explicitly said “assuming the restore has succeeded”; that was not a restore result.
- A subsequent Apple restore on a Mac failed with error 9. Several Linux stock restore attempts also lost communication around NORData.

The owner explicitly authorized erasing/restoring this device. No personal-data recovery claim is made; the restore erased the data. A limited Preboot backup was not a complete backup of user data.

## 25–26 October: a restore result without a working normal boot

An SSH diagnostic environment initially booted and could read storage. A SEP restore path using `--restore+art` produced a SEP ROM panic. A temporary restore service in RAM using `--restore` instead could proceed.

Additional problems in our diagnostic setup had to be corrected: platform entitlements, the generic bootstrap ticket versus the live restore ticket, and a writable temporary location for metadata extraction. These were defects of the diagnostic flow, not evidence of physical damage to the iPad.

At 00:24:17 on 26 October, the protocol reported a real completed restore, including sealing and snapshot creation. However, reboot returned to ROM DFU. This was correctly left as **restore completed; normal boot unconfirmed**.

The later audit uncovered a concrete omission in that earlier verification: official payloads and a common ticket did not establish that the stored `IM4R.BNCN` hashed to the ticket's `BNCH`.

## 30 October: stages were verified rather than inferred

Stock encrypted iBSS/iBEC repeatedly executed. Modified images could transfer successfully while the device remained in BootROM. We stopped sending later stages after such failures.

A data read showed the expected instruction at the patch address, yet a separate execution probe initially returned the behavior of the original instruction. After data-to-instruction cache synchronization, the same probe returned the patched behavior. The modified iBSS and iBEC then executed, and SSH became available. The cache issue was not assumed solely from `PWND` or the bytes read back.

The direct port and hub used different host USB controllers. Some attempts behaved differently, but that did not establish that every owner needs this hub or port. Manual DFU entry was sometimes necessary; some transitions could later be handled through the working loader without another physical DFU sequence.

## Separating diagnostic panics

A broad `ioreg -l -w 0` from the bundled diagnostic environment opened/reached user clients and was followed by a `Kernel data abort` with `ioreg` as the panicked process. We stopped using that broad probe and replaced the needed measurement with a small property reader that never calls `IOServiceOpen`.

Later, loading the installed SEP firmware produced `SEPOS is alive` and successful device-tree setup. A subsequent ROM-status query caused an `endpointHandle != EP_BOOTSTRAP` panic. That query was inappropriate after sepOS started. It must not be cited as proof that the installed SEP firmware failed to boot.

## Nonce inconsistency and correction

The earlier stored images contained:

```text
BNCN:        1e00573fd19f2d08
SHA1(BNCN):  2e78aecb48fd08151ad6e60eabea5122d44fb4fb
Ticket BNCH: ffe664e35d778e6d9853adc52cbf7778fd27a636
```

The BNCN matched the boot nonce exported by the diagnostic kernel. The ticket's BNCH matched the nonce observed earlier, before that bootstrap. This supports a mixed-context explanation for the inconsistent stored boot metadata. A published modern Image4 analysis describes why this relationship matters for local boot, but it is not a direct reverse-engineering result for this A8 ROM.

We then read the actual current diagnostic nonce, issued a ticket for its hash, and discovered another mismatch: the diagnostic kernel still had the generic `boot-manifest-hash`. Runtime metadata evaluation returned 13. We did not start a restore in that context.

The boot generator variable was initially absent. Setting it through the running kernel's `nvram` tool was denied. A newer local iBoot64Patcher had `-n`, but a further four-entry write allowlist remained. Its RAM-only `pwr-path` pointer was replaced by the already existing `com.apple.System.boot-nonce` string pointer. After this change, the exact generator could be read back and saved. Reloading iBEC produced the expected APNonce.

The new diagnostic bootstrap then had both the intended BNCN and the intended ticket hash. Runtime metadata evaluation returned 0. Only then was the new full restore started.

## Final restore and read-back audit

The 30 October restore ran from approximately 22:43 to 22:56:57 UTC. It copied and verified the filesystem, ran APFS checks, processed metadata with mtree and completed `apfs_sealvolume`. The client exited 0 with `Restore Finished` and `DONE`; the internal service reported `FINISHED-ENGINES: SUCCESS` and `initial_engine_success`.

The internal log also records endured NFC/secure-element updater failures. They are retained in the full log rather than hidden by the overall success result. Their effect on complete device functionality has not been validated.

Before reboot, we read the stored firmware media and LLB media again and extracted the active Preboot SEP image. Payload comparison, ticket equality, ART/Preboot agreement and the stored nonce relationship all passed. The final evidence files are in `evidence/final-audit/`.

After the audited reboot the owner reported the low-battery screen, then connected the iPad to a 10/12 W-or-higher wall charger. A startup progress bar was observed while it was still low on charge. The owner subsequently confirmed: **“bootou e ta a funcionar”** (“it booted and is working”). Configuration was postponed until after charging. This is the final observed outcome of this case; activation, all peripherals, battery health and long-term reliability were not independently tested.
