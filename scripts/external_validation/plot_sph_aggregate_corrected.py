"""Render frozen aggregate figures with absolute bootstrap interval endpoints."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

from matplotlib.axes import Axes

if __package__:
    from .plot_sph_aggregate import plot_sph_aggregate
else:
    from plot_sph_aggregate import plot_sph_aggregate


def _absolute_interval(axis, x, y, *, xerr=None, fmt="o", color=None,
                       markersize=4, capsize=2, linewidth=1, **kwargs):
    if kwargs:
        raise ValueError(f"unexpected errorbar arguments: {sorted(kwargs)}")
    if xerr is not None:
        lower = float(x) - float(xerr[0][0])
        upper = float(x) + float(xerr[1][0])
        if lower > upper:
            raise ValueError("bootstrap interval endpoints are inverted")
        axis.hlines(y, lower, upper, colors=color, linewidth=linewidth)
        if capsize:
            axis.plot([lower, upper], [y, y], linestyle="none", marker="|",
                      color=color, markersize=2 * capsize)
    axis.plot(x, y, fmt, color=color, markersize=markersize)


def plot_corrected(report, output_dir):
    with patch.object(Axes, "errorbar", _absolute_interval):
        return plot_sph_aggregate(report, output_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    result = plot_corrected(json.loads(args.input.read_text(encoding="utf-8")), args.output_dir)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
