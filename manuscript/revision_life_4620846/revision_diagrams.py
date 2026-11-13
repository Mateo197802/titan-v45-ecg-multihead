"""Draw new explanatory schematics without reusing third-party artwork."""
from matplotlib.patches import FancyBboxPatch
import matplotlib.pyplot as plt

from revision_data import save


def draw(name, boxes, edges=(), height=2.5):
    fig, ax = plt.subplots(figsize=(8, height))
    ax.set(xlim=(0, 1), ylim=(min(y for _,y,_ in boxes)-.12, max(y for _,y,_ in boxes)+.12))
    ax.axis("off")
    for x, y, text in boxes:
        ax.add_patch(FancyBboxPatch((x-.13, y-.095), .26, .19, boxstyle="round,pad=.008",
                                    facecolor="#f1f5f7", edgecolor="#315474", lw=1))
        ax.text(x, y, text, ha="center", va="center", fontsize=9, color="#172d3b")
    for start, end in edges:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "color":"#315474", "lw":1.2})
    save(fig, name)


def build():
    draw("fig00_ecg_ai_context",
         [(.15,.57,"Public ECG sources\nWaveforms and references"), (.50,.57,"Named 12 leads\nTen seconds at 125 Hz"),
          (.85,.75,"Rhythm reporting\nP6 and P8"), (.85,.34,"Pathology reporting\nP4 panels")],
         [((.29,.57),(.36,.57)), ((.64,.59),(.71,.74)), ((.64,.54),(.71,.35))])
    draw("fig00b_ecg_ai_evolution_gap",
         [(.15,.57,"Beat level\nEvent identity and time"), (.50,.57,"ECG level\nStatement on a tracing\nEndpoint in this study"),
          (.85,.57,"Longitudinal level\nOnset and first diagnosis")], height=1.65)
    draw("fig01_graphical_abstract",
         [(.15,.57,"12-lead ECG\nWaveform and mask"), (.50,.75,"V3F backbone\nRhythm profile"),
          (.50,.33,"V3AG backbone\nPathology profile"), (.85,.75,"P6 or P8 specialist\nTop-1 and membership"),
          (.85,.33,"P4 specialist\nFour binary panels")],
         [((.29,.59),(.36,.74)), ((.29,.53),(.36,.34)), ((.64,.75),(.71,.75)), ((.64,.33),(.71,.33))])
    draw("fig02_data_processing_bias_workflow",
         [(.15,.75,"Source waveform\nNamed lead alignment"), (.50,.75,"Filter and resample\n12 × 1,250 samples"),
          (.85,.75,"Per-window scaling\nLead mask and proxies"), (.15,.26,"Historical development\nPartial provenance"),
          (.50,.26,"Selected P6 / P8 / P4\nArchived comparisons"), (.85,.26,"Separate confirmatory work\nNo outcome reported")],
         [((.29,.75),(.36,.75)), ((.64,.75),(.71,.75))], height=2.9)
    draw("fig03_internal_architecture",
         [(.15,.68,"Waveform + lead mask\n12 × 1,250 and 12"), (.15,.28,"Morphology\n10 normalized proxies"),
          (.50,.68,"ResNet-1D / Transformer\n640 waveform features"),
          (.50,.28,"Global rhythm inputs\n640 waveform + 10 proxies"),
          (.85,.68,"Global pathology head\n640 waveform features"), (.85,.28,"P6 / P8 and P4\n10 direct proxy inputs")],
         [((.29,.68),(.36,.68)), ((.64,.68),(.71,.68)), ((.50,.57),(.50,.39)),
          ((.29,.28),(.36,.28)), ((.64,.28),(.71,.28)),
          ((.24,.18),(.76,.18))], height=2.25)
    draw("fig03_cascade_contract",
         [(.15,.73,"Primary P6\nAFIB SB STACH\nRBBB 1AVB PVC"), (.50,.73,"P8 additions\nNSR and PAC"),
          (.85,.73,"Primary P4\nASMI LVH IMI ISC"),
          (.15,.28,"Secondary rhythm candidates\nFlutter and paced rhythm"),
          (.50,.28,"Other global rhythm outputs\nLBBB 2AVB 3AVB LQTS"),
          (.85,.28,"Outside primary P4\nALMI ILMI LAE")], height=3.1)


if __name__ == "__main__":
    build()
