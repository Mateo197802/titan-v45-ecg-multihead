"""Bounded parallel resumable download of the exact Zenodo CODE-15% archives."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from code15_io import PROTOCOL, digest

CHUNK = 64 * 1024**2
WORKERS = 4


def range_download(code: Path, filename: str, entry: dict):
    total = entry["size"]
    final = code / filename
    partial = final.with_suffix(".zip.part")
    chunks = code / (filename + ".ranges")
    if not final.exists():
        prefix = partial.stat().st_size if partial.exists() else 0
        if not 0 <= prefix <= total or shutil.disk_usage(code).free <= 2 * total + 10 * 1024**3:
            raise ValueError("existing prefix or shared-space guard failed")
        chunks.mkdir(exist_ok=True)

        def fetch(start):
            end = min(start + CHUNK, total) - 1
            path = chunks / f"{start}-{end}.bin"
            if path.is_file() and path.stat().st_size == end + 1 - start:
                return path
            tmp = path.with_suffix(".part")
            result = subprocess.run([
                "curl", "--fail", "--silent", "--show-error", "--location", "--proto", "=https",
                "--proto-redir", "=https", "--retry", "3", "--connect-timeout", "20", "--max-time", "420",
                "--header", "Accept-Encoding: identity", "--range", f"{start}-{end}", "--max-filesize",
                str(end + 1 - start), "--output", str(tmp), "--dump-header", "-",
                f"https://zenodo.org/records/4916206/files/{filename}?download=1",
            ], capture_output=True, text=True, check=True)
            headers = {line.strip().lower() for line in result.stdout.splitlines()}
            if (f"content-range: bytes {start}-{end}/{total}" not in headers
                    or tmp.stat().st_size != end + 1 - start):
                raise ValueError("server did not return the exact requested range")
            tmp.replace(path)
            print(json.dumps({"archive": filename, "range_verified_bytes": end + 1 - start,
                              "range_start": start}), flush=True)
            return path

        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            obtained = list(pool.map(fetch, range(prefix, total, CHUNK)))
        candidate = final.with_suffix(".assembled")
        with candidate.open("wb") as dst:
            for source in ([partial] if prefix else []) + obtained:
                with source.open("rb") as inp:
                    shutil.copyfileobj(inp, dst, length=1024 * 1024)
    else:
        candidate = final
        obtained = []
    md5 = hashlib.md5(usedforsecurity=False)
    with candidate.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(block)
    if candidate.stat().st_size != total or "md5:" + md5.hexdigest() != entry["checksum"]:
        raise ValueError("assembled archive differs from Zenodo identity")
    if filename == "exams_part10.zip":
        with zipfile.ZipFile(candidate) as archive:
            if archive.namelist() != ["exams_part10.hdf5"] or archive.testzip() is not None:
                raise ValueError("first archive layout or CRC failure")
    if candidate != final:
        candidate.replace(final)
        for item in obtained:
            item.unlink()
        chunks.rmdir()
    return {"archive": filename, "bytes": total, "publisher_md5": md5.hexdigest(), "sha256": digest(final)}


def run(code: Path, mode: str):
    protocol = json.loads(PROTOCOL.read_bytes())
    catalog = code / "record.json"
    if digest(catalog) != protocol["catalog_sha256"]:
        raise ValueError("CODE publisher catalog digest mismatch")
    entries = {entry["key"]: entry for entry in json.loads(catalog.read_bytes())["files"]
               if entry["key"].endswith(".zip")}
    if entries.keys() != {f"exams_part{i}.zip" for i in range(18)}:
        raise ValueError("CODE archive names differ from frozen catalog")
    names = sorted(entries, key=lambda name: hashlib.sha256(("20261111|code15-transport|" + name).encode()).digest())
    if mode == "first":
        names = names[:1]
    results = []
    for name in names:
        result = range_download(code, name, entries[name])
        results.append(result)
        print(json.dumps(result), flush=True)
    result = {"scope": mode, "archives": results, "labels_read": False}
    (code / f"range_{mode}_receipt.json").write_bytes((json.dumps(result, indent=2) + "\n").encode())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("code", type=Path)
    parser.add_argument("mode", choices=("first", "all"))
    args = parser.parse_args()
    run(args.code, args.mode)
