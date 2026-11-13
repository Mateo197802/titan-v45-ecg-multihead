"""Inspect the checkpoint's saved P4 thresholds without loading ECG data."""
import json
import sys

import torch

checkpoint = torch.load(sys.argv[1], map_location="cpu", weights_only=True)
values = checkpoint["pathology4_thresholds"]
print(json.dumps({
    "classes": list(checkpoint["pathology4_classes"]),
    "container_type": type(values).__name__,
    "dtype": str(getattr(values, "dtype", "not_applicable")),
    "thresholds": [float(value) for value in values],
}, indent=2))
