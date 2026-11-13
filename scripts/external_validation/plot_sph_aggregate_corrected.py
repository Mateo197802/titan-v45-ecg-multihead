"""Render frozen aggregate figures with absolute bootstrap interval endpoints."""
from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path
from unittest.mock import patch

from matplotlib.axes import Axes

if __package__:
    from . import plot_sph_aggregate as base
else:
    import plot_sph_aggregate as base


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
    original_set_yticks = Axes.set_yticks
    original_save = base._save

    def preserve_shared_labels(axis, ticks, labels=None, *args, **kwargs):
        if isinstance(labels, list) and not labels:
            return original_set_yticks(axis, ticks, *args, **kwargs)
        return original_set_yticks(axis, ticks, labels, *args, **kwargs)

    def save_with_clear_notes(fig, directory, stem):
        axis = fig.axes[0]
        if stem == "sph_profile_coverage" and fig.texts:
            note = fig.texts[0]
            axis.set_xlabel(axis.get_xlabel() + "\n" + textwrap.fill(note.get_text(), width=95), fontsize=8)
            note.remove()
        if stem == "sph_duplicate_sensitivity":
            fig.set_size_inches(fig.get_figwidth(), fig.get_figheight() + 1.5, forward=True)
            for note in list(axis.texts):
                if note.get_text().startswith("Endpoint-specific exclusion"):
                    axis.set_xlabel(axis.get_xlabel() + "\n" + note.get_text(), fontsize=8)
                    note.remove()
            handles, labels = axis.get_legend_handles_labels()
            legend = axis.get_legend()
            if legend is not None:
                legend.remove()
            axis.legend(handles, labels, frameon=False, loc="upper center",
                        bbox_to_anchor=(0.5, -0.20), fontsize=8)
        return original_save(fig, directory, stem)

    with patch.object(Axes, "errorbar", _absolute_interval), patch.object(
        Axes, "set_yticks", preserve_shared_labels
    ), patch.object(base, "_save", save_with_clear_notes):
        return base.plot_sph_aggregate(report, output_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    result = plot_corrected(json.loads(args.input.read_text(encoding="utf-8")), args.output_dir)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
