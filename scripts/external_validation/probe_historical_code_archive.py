"""Inspect only aggregate header/layout details from the pinned historical archive."""
import json
import sys
import tarfile
from collections import Counter
from pathlib import PurePosixPath

import zstandard

paths, headers = Counter(), Counter()
with open(sys.argv[1], "rb") as archive, zstandard.ZstdDecompressor().stream_reader(archive) as decoder:
    with tarfile.open(fileobj=decoder, mode="r|") as tar:
        for entry in tar:
            path = PurePosixPath(entry.name)
            if not any("codetest" in part.lower() or "code-test" in part.lower() for part in path.parts):
                continue
            paths["/".join(path.parts[:2]) + "/" + path.suffix] += 1
            if path.suffix == ".hea" and entry.isfile():
                with tar.extractfile(entry) as source:
                    lines = [line.split() for line in source.read().decode("ascii", "replace").splitlines()
                             if line.strip() and not line.startswith("#")]
                spec = lines[0][1:4]
                types = sorted({PurePosixPath(line[0]).suffix for line in lines[1:]})
                headers[str((spec, types))] += 1
print(json.dumps({"archive_members_by_directory_and_suffix": paths, "header_contracts": headers}, indent=2))
