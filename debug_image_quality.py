#!/usr/bin/env python3
"""
Debug image quality by analyzing pixel statistics
"""

from PIL import Image
import numpy as np
from pathlib import Path

def analyze_image(image_path):
    """Analyze image statistics"""
    img = Image.open(image_path)
    arr = np.array(img)

    print(f"\n=== {Path(image_path).name} ===")
    print(f"Size: {img.size}")
    print(f"Mode: {img.mode}")
    print(f"Array shape: {arr.shape}")
    print(f"Mean: {arr.mean():.2f}")
    print(f"Std: {arr.std():.2f}")
    print(f"Min: {arr.min()}, Max: {arr.max()}")
    print(f"Unique colors: {len(np.unique(arr.reshape(-1, arr.shape[-1]), axis=0))}")

    # Check if image is mostly one color (blurry/low quality indicator)
    flat = arr.reshape(-1, arr.shape[-1])
    unique_colors = len(np.unique(flat, axis=0))
    total_pixels = flat.shape[0]
    color_ratio = unique_colors / total_pixels
    print(f"Color diversity: {color_ratio:.4f} ({unique_colors}/{total_pixels})")

    if color_ratio < 0.1:
        print("⚠️  WARNING: Low color diversity - image may be blurry or low quality")

    return arr

if __name__ == "__main__":
    print("Analyzing generated images...")

    # Analyze native generated images
    native_imgs = [
        "output_native_test/test_single_stage.png",
        "output_native_test/test_progressive.png",
        "output_native_test/test_with_lora.png",
        "output_native_test/test_tweet_01.png",
    ]

    for img_path in native_imgs:
        if Path(img_path).exists():
            analyze_image(img_path)
        else:
            print(f"\n❌ {img_path} not found")
