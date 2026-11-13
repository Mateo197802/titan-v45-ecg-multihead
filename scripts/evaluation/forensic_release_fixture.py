"""Hash and load exact released models, then repeat a label-free CPU fixture."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--assets", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    a = parser.parse_args()
    sys.path.insert(0, str(a.repo/"src"))
    from titan_v45.models import frozen_pathology as fp
    from titan_v45.models import frozen_rhythm as fr

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    paths, hashes = fp.verified_assets(a.repo, a.assets, {fr.BACKBONE,*fr.HEADS.values(),fp.BACKBONE,fp.SPECIALIST})
    contract = json.loads((a.repo/"outputs/models/heads/global_head_contracts.json").read_bytes())
    event = fr.load_recorded_event_extractor(a.repo/"docs/provenance/recovered-original-sources-20261029.zip")
    rhythm, pathology = fr.FrozenRhythm(paths,contract,event,"cpu"),fp.FrozenPathology(paths,contract,"cpu")
    t = np.arange(1250, dtype=np.float32)/125
    x = np.stack([np.sin((i+1)*t) for i in range(12)])
    samples = [(x, np.ones(12,dtype=bool), np.linspace(0,.9,10,dtype=np.float32))]
    r1, aux1 = rhythm(samples)
    r2, aux2 = rhythm(samples)
    p1,p2 = pathology(samples),pathology(samples)
    if not (all(np.array_equal(r1[k],r2[k]) for k in r1) and np.array_equal(aux1,aux2) and p1==p2):
        raise ValueError("fixed CPU fixture differs across exact repeat")
    if not all(np.isfinite(x).all() for x in (*r1.values(),aux1,list(p1[0][0].values()))):
        raise ValueError("fixture inference nonfinite")
    obj = {
        "schema":"TITAN_FORENSIC_FIXTURE_V1","model_sha256":hashes,"strict_state_dict":True,
        "repeat_exact":True,"input_shape":[1,12,1250],"morphology_shape":[1,10],
        "rhythm_logit_shapes":{k:list(x.shape) for k,x in r1.items()},
        "pathology_classes":list(p1[0][0]),"rhythm_classes":{"P6":list(fr.P6_CLASSES),"P8":list(fr.P8_CLASSES)},
        "rhythm_stored_and_declared_width":rhythm.widths,
        "parameters":{k:sum(p.numel() for p in m.parameters()) for k,m in
                      {"V3F":rhythm.model,"V3AG":pathology.model,"P4":pathology.head,**rhythm.heads}.items()},
        "torch":str(torch.__version__),"device":"CPU","labels_used":False,
        "individual_or_score_values_exported":False,
    }
    with a.output.open("x",encoding="utf-8") as f:
        json.dump(obj,f,indent=2,sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    main()
