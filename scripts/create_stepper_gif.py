#!/usr/bin/env python3
"""
scripts/create_stepper_gif.py
Generates an authentic retro terminal animated GIF of the five-stage digging stepper.
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "static" / "screenshots" / "live_dig_stepper.gif"

WIDTH, HEIGHT = 720, 360
BG_COLOR = (24, 24, 24)        # Terminal dark background
HEADER_COLOR = (235, 120, 35)  # Retro cempasúchil orange
TEXT_MUTED = (130, 130, 130)   # Dimmed pending text
TEXT_ACTIVE = (245, 245, 245)  # Bright white text
TEXT_SUCCESS = (60, 190, 90)   # Green checkmark
BORDER_COLOR = (55, 55, 55)

stages_info = [
    ("ARCHAEOLOGIST", "Establishing capture lifeline & snapshot dates (CDX API)"),
    ("EXHUMER",      "Extracting historical DOM via Browserbase CDP & screenshots"),
    ("CORONER",       "Forensic autopsy: acquired_then_shut_down"),
    ("EULOGIST",      "Gemma 26B Día de los Muertos remembrance composed"),
    ("FACT-CHECKER",  "Auditing claims: 5 verified, 0 ungrounded assertions")
]

def make_frame(active_stage, is_final=False):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Outer border
    draw.rectangle([10, 10, WIDTH - 10, HEIGHT - 10], outline=BORDER_COLOR, width=2)
    # Header bar
    draw.rectangle([10, 10, WIDTH - 10, 48], fill=(36, 36, 36))
    
    # Fonts: try standard monospace or default
    try:
        font_title = ImageFont.truetype("consola.ttf", 16)
        font_mono = ImageFont.truetype("consola.ttf", 14)
        font_bold = ImageFont.truetype("consolab.ttf", 14)
    except Exception:
        font_title = ImageFont.load_default()
        font_mono = ImageFont.load_default()
        font_bold = ImageFont.load_default()

    draw.text((25, 20), "GRAVEYARD OF DEAD SOFTWARE -- LIVE EXHUMATION TERMINAL", fill=HEADER_COLOR, font=font_title)
    draw.text((25, 65), "TARGET: https://geocities.com  |  DISCOVERY: 1996 - 2009", fill=(180, 180, 180), font=font_mono)
    draw.line([(25, 90), (WIDTH - 25, 90)], fill=BORDER_COLOR, width=1)

    y = 110
    for idx, (name, desc) in enumerate(stages_info):
        if idx < active_stage:
            # Completed
            draw.text((30, y), "[✓]", fill=TEXT_SUCCESS, font=font_bold)
            draw.text((65, y), f"{name:<15}", fill=HEADER_COLOR, font=font_bold)
            draw.text((215, y), desc, fill=TEXT_ACTIVE, font=font_mono)
        elif idx == active_stage and not is_final:
            # In progress
            draw.text((30, y), "[*]", fill=(240, 200, 50), font=font_bold)
            draw.text((65, y), f"{name:<15}", fill=(240, 200, 50), font=font_bold)
            draw.text((215, y), "Digging in progress...", fill=TEXT_ACTIVE, font=font_mono)
        else:
            # Pending
            draw.text((30, y), "[ ]", fill=TEXT_MUTED, font=font_mono)
            draw.text((65, y), f"{name:<15}", fill=TEXT_MUTED, font=font_mono)
            draw.text((215, y), desc, fill=TEXT_MUTED, font=font_mono)
        y += 34

    draw.line([(25, y + 15), (WIDTH - 25, y + 15)], fill=BORDER_COLOR, width=1)
    if is_final:
        draw.text((30, y + 25), "STATUS: EXHUMATION COMPLETE -> Memorial published to /grave/geocities", fill=TEXT_SUCCESS, font=font_bold)
    else:
        draw.text((30, y + 25), f"STATUS: Digging stage {active_stage+1}/5 active...", fill=(220, 220, 220), font=font_mono)

    return img

frames = []
# Frame 0: starting
frames.append((make_frame(0, False), 1200))
# Stages 1 to 4
for s in range(5):
    frames.append((make_frame(s, False), 1100))
    # Add frame where stage completes
    frames.append((make_frame(s + 1, False if s < 4 else True), 1100))

# Final frame pause
frames.append((make_frame(5, True), 3000))

# Save animated GIF
first_frame, first_dur = frames[0]
first_frame.save(
    OUT_PATH,
    save_all=True,
    append_images=[f for f, d in frames[1:]],
    duration=[d for f, d in frames],
    loop=0
)

print(f"Created animated GIF: {OUT_PATH} ({OUT_PATH.stat().st_size} bytes)")
