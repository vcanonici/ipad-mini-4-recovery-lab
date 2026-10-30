# Contributing

Please distinguish observations, hypotheses and confirmed outcomes. State the exact product/board/build and the last stage independently verified. A working USB upload does not prove execution, and a completed restore does not prove normal boot.

Useful contributions include another independently reproduced case, exact upstream revisions, corrections to an interpretation, and tests for malformed IMG4 input. A build-specific change needs its input hash and proof of scope. Do not generalize an iPad5,1 offset to iPad5,2.

Keep Apple firmware and other projects' executables out of pull requests. The owner deliberately retained technical identifiers in the original case evidence; contributors should decide what to share about their own devices and must not post credentials or another person's account data.

Run `python3 -m unittest discover -s tests -v` before changing the host tools. A normal-boot confirmation should identify what was actually seen and tested, not just update a status badge.
