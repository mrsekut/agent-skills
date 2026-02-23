#!/usr/bin/env python3
"""
Generate Chrome Web Store listing images from an extension icon.

Usage:
    python3 generate_store_images.py <icon_path> <output_dir> [--name "Extension Name"] [--color "#4A90D9"]

Generates:
    - store_icon_128.png   (128x128, icon with 16px transparent padding)
    - promo_tile_440x280.png (440x280, small promo tile)
    - marquee_1400x560.png (1400x560, marquee promo tile)
    - screenshot_1280x800.png (1280x800, placeholder screenshot)

Requirements: Pillow (pip install Pillow)
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)


def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def darken(color: tuple, factor: float = 0.7) -> tuple:
    return tuple(max(0, int(c * factor)) for c in color)


def lighten(color: tuple, factor: float = 0.3) -> tuple:
    return tuple(min(255, int(c + (255 - c) * factor)) for c in color)


def generate_store_icon(icon_path: str, output_path: str):
    """Generate 128x128 store icon with 16px transparent padding."""
    icon = Image.open(icon_path).convert("RGBA")
    icon = icon.resize((96, 96), Image.LANCZOS)
    canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    canvas.paste(icon, (16, 16), icon)
    canvas.save(output_path, "PNG")
    print(f"  Created: {output_path}")


def generate_promo_tile(
    icon_path: str, output_path: str, name: str, color: tuple
):
    """Generate 440x280 small promo tile."""
    canvas = Image.new("RGB", (440, 280), color)
    draw = ImageDraw.Draw(canvas)

    # Gradient overlay
    lighter = lighten(color, 0.2)
    for y in range(280):
        ratio = y / 280
        r = int(color[0] * (1 - ratio) + lighter[0] * ratio)
        g = int(color[1] * (1 - ratio) + lighter[1] * ratio)
        b = int(color[2] * (1 - ratio) + lighter[2] * ratio)
        draw.line([(0, y), (440, y)], fill=(r, g, b))

    # Icon centered
    try:
        icon = Image.open(icon_path).convert("RGBA")
        icon = icon.resize((80, 80), Image.LANCZOS)
        x = (440 - 80) // 2
        canvas.paste(icon, (x, 70), icon)
    except Exception:
        # Draw placeholder circle
        draw.ellipse([180, 70, 260, 150], fill="white")

    # Extension name
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24
            )
        except (OSError, IOError):
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), name, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text(((440 - text_w) // 2, 175), name, fill="white", font=font)

    canvas.save(output_path, "PNG")
    print(f"  Created: {output_path}")


def generate_marquee(icon_path: str, output_path: str, name: str, color: tuple):
    """Generate 1400x560 marquee promo tile."""
    canvas = Image.new("RGB", (1400, 560), color)
    draw = ImageDraw.Draw(canvas)

    lighter = lighten(color, 0.15)
    for y in range(560):
        ratio = y / 560
        r = int(color[0] * (1 - ratio) + lighter[0] * ratio)
        g = int(color[1] * (1 - ratio) + lighter[1] * ratio)
        b = int(color[2] * (1 - ratio) + lighter[2] * ratio)
        draw.line([(0, y), (1400, y)], fill=(r, g, b))

    try:
        icon = Image.open(icon_path).convert("RGBA")
        icon = icon.resize((160, 160), Image.LANCZOS)
        canvas.paste(icon, (620, 140), icon)
    except Exception:
        draw.ellipse([620, 140, 780, 300], fill="white")

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48
            )
        except (OSError, IOError):
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), name, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text(((1400 - text_w) // 2, 340), name, fill="white", font=font)

    canvas.save(output_path, "PNG")
    print(f"  Created: {output_path}")


def generate_screenshot_placeholder(
    output_path: str, name: str, color: tuple
):
    """Generate 1280x800 screenshot placeholder."""
    canvas = Image.new("RGB", (1280, 800), (245, 245, 245))
    draw = ImageDraw.Draw(canvas)

    # Browser chrome mockup
    draw.rectangle([0, 0, 1280, 72], fill=(222, 222, 222))
    draw.rectangle([80, 16, 500, 56], fill="white", outline=(200, 200, 200))
    draw.ellipse([20, 28, 36, 44], fill=(255, 95, 87))
    draw.ellipse([44, 28, 60, 44], fill=(255, 189, 46))
    draw.ellipse([68, 28, 84, 44], fill=None, outline=(200, 200, 200))

    # Content area with extension popup mockup
    popup_w, popup_h = 360, 480
    px, py = 820, 100
    draw.rectangle(
        [px, py, px + popup_w, py + popup_h],
        fill="white",
        outline=(200, 200, 200),
    )
    draw.rectangle([px, py, px + popup_w, py + 48], fill=color)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        small_font = ImageFont.truetype(
            "/System/Library/Fonts/Helvetica.ttc", 14
        )
    except (OSError, IOError):
        font = ImageFont.load_default()
        small_font = font

    draw.text((px + 16, py + 14), name, fill="white", font=font)

    # Placeholder content lines
    for i in range(6):
        y = py + 72 + i * 40
        w = popup_w - 40 - (i % 3) * 40
        draw.rectangle(
            [px + 20, y, px + 20 + w, y + 12], fill=(230, 230, 230)
        )

    # Left side page content placeholder
    for i in range(8):
        y = 120 + i * 50
        draw.rectangle([60, y, 60 + 600 - (i % 4) * 60, y + 14], fill=(235, 235, 235))
        if i < 7:
            draw.rectangle([60, y + 22, 60 + 500 - (i % 3) * 80, y + 32], fill=(242, 242, 242))

    canvas.save(output_path, "PNG")
    print(f"  Created: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Chrome Web Store listing images"
    )
    parser.add_argument("icon_path", help="Path to extension icon (PNG)")
    parser.add_argument("output_dir", help="Output directory for generated images")
    parser.add_argument("--name", default="My Extension", help="Extension name")
    parser.add_argument("--color", default="#4A90D9", help="Brand color (hex)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    color = hex_to_rgb(args.color)
    print(f"Generating store images for '{args.name}'...")

    generate_store_icon(
        args.icon_path, str(output_dir / "store_icon_128.png")
    )
    generate_promo_tile(
        args.icon_path,
        str(output_dir / "promo_tile_440x280.png"),
        args.name,
        color,
    )
    generate_marquee(
        args.icon_path,
        str(output_dir / "marquee_1400x560.png"),
        args.name,
        color,
    )
    generate_screenshot_placeholder(
        str(output_dir / "screenshot_1280x800.png"), args.name, color
    )
    print("\nDone! Generated images:")
    for f in sorted(output_dir.glob("*.png")):
        print(f"  {f}")


if __name__ == "__main__":
    main()
