# Verification

The source snapshot contains public aggregate evidence from the exact
PR #10 Git commit. To verify an extracted copy with Python 3.10+:

```sh
python technical_package/verify_external_evidence.py .
```

This checks the fixed inventory, hashes, original receipt chain, confusion
matrix arithmetic, per-endpoint supports, macro averages, CI associations,
PR grid and claim boundaries. It does not access private records or CEDIA.
To verify a ZIP before extracting, pass the ZIP path instead of `.`.
The archive verifier rejects extra or unsafe members, duplicate names,
symlinks, oversized inputs and CRC failures.

From the full checkout, verify with the same script in
`scripts/evaluation/verify_external_evidence.py`; add `--repo .` to
compare snapshots and referenced blobs against Git. The archive omits
itself; its SHA-256 is in the sibling download checksum published with
the repository. `SHA256SUMS.txt` covers payload members (including the
manifest but excluding itself). The manifest records source commits,
original blob hashes and the role of each payload file.

The figures can be regenerated using
`python scripts/evaluation/render_external_evidence.py <output-directory>`
with Matplotlib and the frozen source commit available. Exported hashes
authenticate the shipped files, not byte-for-byte reproducibility across
different Matplotlib/font versions. No new data acquisition, inference,
training or test access is needed.
