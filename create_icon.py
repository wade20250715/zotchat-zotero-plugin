#!/usr/bin/env python3
"""Create ZotChat icons"""
from PIL import Image, ImageDraw
import os, shutil

def create_icon(size, output_path):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r = size // 4
    for y in range(size):
        ratio = y / size
        r_val = int(102 + (118 - 102) * ratio)
        g_val = int(126 + (75 - 126) * ratio)
        b_val = int(234 + (162 - 234) * ratio)
        for x in range(size):
            in_corner = False
            if x < r and y < r: in_corner = (x - r) ** 2 + (y - r) ** 2 > r ** 2
            elif x >= size - r and y < r: in_corner = (x - (size - r - 1)) ** 2 + (y - r) ** 2 > r ** 2
            elif x < r and y >= size - r: in_corner = (x - r) ** 2 + (y - (size - r - 1)) ** 2 > r ** 2
            elif x >= size - r and y >= size - r: in_corner = (x - (size - r - 1)) ** 2 + (y - (size - r - 1)) ** 2 > r ** 2
            if not in_corner:
                if x >= r and x < size - r and y >= r and y < size - r:
                    draw.point((x, y), fill=(r_val, g_val, b_val, 255))
                elif (x < r and y >= r and y < size - r) or (x >= size - r and y >= r and y < size - r) or (y < r and x >= r and x < size - r) or (y >= size - r and x >= r and x < size - r):
                    draw.point((x, y), fill=(r_val, g_val, b_val, 255))
    try:
        from PIL import ImageFont
        font_size = size // 2
        font = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", font_size)
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "Z", font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2
    ty = (size - th) // 2 - 2
    draw.text((tx, ty), "Z", fill=(255, 255, 255, 255), font=font)
    img.save(output_path, "PNG")
    print(f"Created: {output_path} ({size}x{size})")

if __name__ == "__main__":
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skin")
    for s in [16, 32, 48, 96]:
        create_icon(s, os.path.join(outdir, f"icon{s}.png"))
    shutil.copy2(os.path.join(outdir, "icon48.png"), os.path.join(outdir, "icon.png"))
    print("Done!")
