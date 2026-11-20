#!/usr/bin/env python3
"""Classify the photos of media.gpkg as soilprofile / soilsite with CLIP (zero-shot).

Usage:
  pip install torch transformers pillow
  python classify_media.py media.gpkg [--threshold 0.75] [--all] [--dry-run]

By default only rows with mediatype='photo' and subject NULL are processed. With --all every
photo is recomputed (also those already labelled by hand: use with care). Below the threshold the
row gets subject='to_verify'. The confidence is written to `ai_confidence`. Audio and raster
rows are never touched.
"""
import argparse
import sqlite3
from pathlib import Path

LABELS = {
    "soilprofile": [
        "a photo of a soil profile showing horizontal soil horizons in a vertical pit wall",
        "a vertical cut of soil with layers of different colour, with a measuring tape or scale",
    ],
    "soilsite": [
        "a landscape photograph with sky, horizon and vegetation",
        "a wide view of a field, hills or countryside",
    ],
}


def decide(probs_by_class, threshold):
    """probs_by_class: {class: probability}. Returns (subject, confidence)."""
    best = max(probs_by_class, key=probs_by_class.get)
    conf = probs_by_class[best]
    return (best if conf >= threshold else "to_verify"), conf


def build_classifier():
    import torch
    from PIL import Image
    from transformers import CLIPModel, CLIPProcessor

    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").eval()
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    classes = list(LABELS)
    prompts = [p for c in classes for p in LABELS[c]]
    counts = [len(LABELS[c]) for c in classes]

    def classify(path):
        img = Image.open(path).convert("RGB")
        inp = proc(text=prompts, images=img, return_tensors="pt", padding=True)
        with torch.no_grad():
            logits = model(**inp).logits_per_image[0]
        probs = logits.softmax(dim=0).tolist()
        out, i = {}, 0
        for c, n in zip(classes, counts):
            out[c] = sum(probs[i:i + n])
            i += n
        return out

    return classify


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gpkg")
    ap.add_argument("--threshold", type=float, default=0.75)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    gpkg = Path(args.gpkg).resolve()
    con = sqlite3.connect(gpkg)
    where = "mediatype='photo'" if args.all else "mediatype='photo' AND subject IS NULL"
    rows = con.execute(f"SELECT fid, path, subject FROM media WHERE {where}").fetchall()
    if not rows:
        print("No photos to classify.")
        return
    classify = build_classifier()
    for fid, rel, old in rows:
        f = gpkg.parent / rel
        if not f.exists():
            print(f"[missing] {rel}")
            continue
        subject, conf = decide(classify(f), args.threshold)
        print(f"{rel}: {old} -> {subject} ({conf:.2f})")
        if not args.dry_run:
            con.execute("UPDATE media SET subject=?, ai_confidence=? WHERE fid=?", (subject, round(conf, 3), fid))
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
