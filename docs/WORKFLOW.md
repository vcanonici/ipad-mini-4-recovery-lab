# Recovery workflow and verification points

This documents what was done on the owned iPad5,1. It is not an unattended restore script. The owner confirmed normal boot after charging; this single-device outcome is not a promise that the workflow fixes every device.

## Establish the case

Record the exact product, board, CPID/BDID, firmware build, last working stage, host USB controller and power state. Keep local originals of logs and ticket responses. Never use another device's ECID, serial, generator or personalized ticket from these examples.

Start with the ordinary Apple restoration path appropriate to your device. This case escalated after repeated restore failures and an interrupted tethered downgrade. Read the upstream tools' own requirements and licenses; their behavior can change between revisions.

## Verify each RAM stage

1. Confirm a real DFU identity, not an invalid ECID-0 query.
2. If using a supported diagnostic bootstrap, confirm modified iBSS actually executes before sending iBEC.
3. Confirm the iBEC stage/mode. A completed upload or `PWND` marker is insufficient.
4. If a memory patch appears present but does not execute, distinguish data visibility from instruction execution. The cache observation here was measured, not inferred from the marker.
5. Initialize the RAM diagnostic environment and verify SSH. A diagnostic screen is not a normal iPadOS boot.

Do not use broad driver/user-client probes merely to obtain two DeviceTree values. The read-only source tool included here reads only `boot-nonce` and `boot-manifest-hash`.

## Preserve a known generator

The published futurerestore flow sets `com.apple.System.boot-nonce`, saves it, reloads iBEC and checks the resulting APNonce. The crucial check is the measurement after reload.

In our firmware build, `-n` alone left an additional write allowlist. The narrowly scoped pointer change is documented in FINDINGS.md; the offline preparer requires the exact reviewed hash. It is not a general-purpose NVRAM patch and is not intended for flashing.

An absent or denied generator query could leave a previous response cached. The exact read-back and the reloaded APNonce were both required. Saving NVRAM successfully over the transport did not by itself prove the generator changed.

## Obtain a ticket for the actual intended context

Use your own device identity and **current SEP nonce** with the intended APNonce. For this A8, the intended APNonce was SHA1 of the eight-byte generator. Re-measure after boot transitions.

The relevant existing tool invocation was of this form, with real values supplied by the operator:

```sh
tsschecker -d iPad5,1 -B j96ap -m BuildManifest.plist -i 15.8.8   -e YOUR_ECID -g YOUR_GENERATOR   --apnonce YOUR_EXPECTED_APNONCE --sepnonce YOUR_CURRENT_SEPNONCE   --no-baseband --save --save-path YOUR_NEW_SESSION_DIRECTORY
```

`--no-baseband` reflects this Wi-Fi-only device. It must not be copied as a universal restore flag. Verify returned ECID, BNCH and SEP nonce instead of assuming that the command's exit status is sufficient. Signing status was observed on the date of this case, not guaranteed for future readers.

Use a new cache/session directory. The exact client version and mode matter: do not generalize one custom cache behavior to all stock restore paths.

## Align the bootstrap before restoring

Use the intended ticket consistently for the diagnostic components. Preserve the generator through the stage transitions. Then read the **running kernel** context again:

- SHA1(raw eight-byte `boot-nonce`) must equal the ticket's BNCH.
- The running `boot-manifest-hash` must match the intended ticket hash in this tested flow.
- The SEP nonce must still be the one used for the ticket.
- Evaluate the intended metadata through the actual runtime used by the restore. A prior evaluation from a different session is not sufficient.

In our case a mismatched runtime returned 13; the aligned context returned 0. We retained the restore service's ticket checks instead of bypassing their failure.

## Restore all components coherently

The diagnostic restore service was temporary in RAM, had the necessary platform entitlements and used `--restore` instead of the failing `--restore+art` SEP loading path. The service was not installed in iPadOS. A writable 384 MiB tmpfs at `/mnt5` was needed for the metadata workflow; `/mnt3` was a separate 64 MiB diagnostic tmpfs.

No manual APFS mounts were left open before starting the erase restore. The client was started in Restore mode with the exact intended ticket, a new cache directory and the original IPSW. This was a full erase restore, not a partial LLB-only repair.

The transcript includes the exact run and the endured updater errors. Allow a live restore to finish. `mtree` and `apfs_sealvolume` were quiet for minutes while still working; output silence was not treated as proof that the operation had ended.

## Audit the stored result before reboot

A restore success message is one piece of evidence. The audit additionally read:

- Firmware media (`disk1` in this measured session) and LLB media (`disk2`). Device nodes are observations, not constants for every environment.
- The active Preboot directory and its personalized SEP firmware.
- The current ART manifest hash.

Extract each stored IMG4, compare its IM4P with the official source, check ticket equality, and check the stored nonce relationship in LLB and iBoot. Require ART and active Preboot to agree with the intended ticket. The included inspector can help with structural/nonce checks; independent signature validation is still a separate task.

The final audit passed. Only then was the read-only audit mount unmounted, storage synchronized and normal reboot requested.

## Verify the actual user-visible outcome

Normal boot is demonstrated by the device reaching the expected iPadOS screen and remaining usable, not by ASR progress, a diagnostic logo, USB PID or a low-battery screen. In this case the owner later reported normal startup and operation after charging, and deferred configuration. Do not infer hardware, activation or long-term stability results that were not tested. Do not force DFU while evaluating an otherwise normal charging/startup sequence.
