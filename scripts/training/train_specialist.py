from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Train a TITAN specialist from frozen, precomputed features."
    )
    parser.add_argument("--features", type=Path, required=True, help="NPZ with x_train and y_train.")
    parser.add_argument("--task", choices=("binary", "multiclass"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--classes", required=True, help="Comma-separated frozen class order.")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=192)
    parser.add_argument("--dropout", type=float, default=0.25)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=197802)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    import numpy as np
    import torch
    from torch.utils.data import DataLoader, TensorDataset

    from titan_v45.models.specialists import ClassWiseBinaryMLP, SpecialistMLP
    from titan_v45.training.loops import train_binary_epoch, train_multiclass_epoch

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    payload = np.load(args.features)
    x_train = torch.from_numpy(np.asarray(payload["x_train"], dtype=np.float32))
    y_train = torch.from_numpy(np.asarray(payload["y_train"]))
    classes = tuple(item.strip() for item in args.classes.split(",") if item.strip())
    if not classes:
        raise ValueError("at least one class is required")
    output_dim = len(classes)
    model_class = ClassWiseBinaryMLP if args.task == "binary" else SpecialistMLP
    model = model_class(
        int(x_train.shape[1]),
        output_dim,
        hidden_dim=args.hidden_dim,
        dropout=args.dropout,
    ).to(args.device)
    loader = DataLoader(
        TensorDataset(x_train, y_train),
        batch_size=args.batch_size,
        shuffle=True,
        generator=torch.Generator().manual_seed(args.seed),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    train_epoch = train_binary_epoch if args.task == "binary" else train_multiclass_epoch
    losses = [
        train_epoch(model, loader, optimizer, device=args.device) for _ in range(args.epochs)
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": model.state_dict(),
            "task": args.task,
            "classes": classes,
            "input_dim": int(x_train.shape[1]),
            "hidden_dim": args.hidden_dim,
            "dropout": args.dropout,
            "seed": args.seed,
            "training_losses": losses,
        },
        args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
