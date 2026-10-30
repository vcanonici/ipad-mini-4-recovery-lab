# Evidence from the owned-device case

These are selected complete technical logs and reports from the investigation, not invented example output. The device owner explicitly requested retaining technical identifiers, nonces, hashes and offsets so others can study the case. The timestamps are UTC.

## Final result

- [Restore console](restore.console.log): `Restore Finished`, `DONE`, final progress 1.0.
- [Client log](restore-client.log) and [internal device log](device-restore-stream.log): the full selected restore run, including endured updater errors.
- [Post-restore components](final-audit/components.json): official payload comparison and ticket/ART/Preboot agreement.
- [Stored nonce checks](final-audit/stored-nonce-validation.json): actual LLB and iBoot read-back; both relationships pass.
- [ART](final-audit/art.log), [Preboot/context](final-audit/preboot-and-context.log).

## Before/after measurements

- [Earlier inconsistent stored nonces](previous-restore-nonce-mismatch.json).
- [Runtime mismatch](runtime-mismatch.json), [metadata evaluation 13](metadata-mismatch.log).
- [Final runtime match](runtime-gate.json), [metadata evaluation 0](metadata-preflight.log).
- [Generator set/read-back](generator-set.jsonl), [APNonce after reload](generator-confirmed.txt).
- [Execution probe before cache sync](cache-probe-before.log), [sync result](cache-sync.log), [probe after](cache-probe-after.log).
- [Exact additional RAM table change](nonce-allowlist-patch.json).

No Apple image, personalized ticket, BootROM dump or third-party executable is included. Only account-key/authentication material is excluded from these logs. The device log had one account-key-related line omitted; all such changes and original/published file hashes are recorded in [manifest.json](manifest.json). The source files remain private in the owner's workspace. Do not treat the original technical identifiers as values suitable for another device.

**Final observed outcome:** restore and stored-component audit passed. After charging, the owner confirmed normal boot and operation: “bootou e ta a funcionar”. Configuration was deferred. See [the outcome record](outcome.json); a complete hardware/activation/stability test was not performed.
