import io
import os
import tempfile
import textwrap
from typing import List, Tuple
from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip

app = FastAPI(title="Scrabble Puzzle & Reel Generator")

# Official Scrabble Point Values
LETTER_POINTS = {
    'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4,
    'I': 1, 'J': 8, 'K': 5, 'L': 1, 'M': 3, 'N': 1, 'O': 1, 'P': 3,
    'Q': 10, 'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 4, 'W': 4, 'X': 8,
    'Y': 4, 'Z': 10
}

def get_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_scrabble_tile(draw: ImageDraw.Draw, x: int, y: int, size: int, letter: str):
    """Draws a classic beveled wooden Scrabble tile with point score."""
    # Outer Tile Shadow & Wood Color
    draw.rounded_rectangle([(x + 4, y + 4), (x + size + 4, y + size + 4)], radius=12, fill="#0F172A")
    draw.rounded_rectangle([(x, y), (x + size, y + size)], radius=12, fill="#F6E0B5", outline="#D7B576", width=3)

    # Main Letter
    letter_upper = letter.strip().upper()
    font_letter = get_font(int(size * 0.58), bold=True)
    lbox = draw.textbbox((0, 0), letter_upper, font=font_letter)
    lw, lh = lbox[2] - lbox[0], lbox[3] - lbox[1]
    draw.text((x + (size - lw) // 2 - 6, y + (size - lh) // 2 - 8), letter_upper, fill="#261A11", font=font_letter)

    # Point Subscript
    pts = str(LETTER_POINTS.get(letter_upper, 0))
    if pts != "0":
        font_pts = get_font(int(size * 0.22), bold=True)
        draw.text((x + size - int(size * 0.28), y + size - int(size * 0.32)), pts, fill="#5C3A21", font=font_pts)

class ScrabblePostRequest(BaseModel):
    rack_letters: str = "Q, U, I, Z, Z, E, D"
    hook_title: str = "Can you find a 35-point word?"
    points: int = 35
    hint: str = "Uses double Z and Q!"
    branding: str = "Word Masters Club"
    canvas_size: Tuple[int, int] = (1080, 1080)

@app.post("/render-scrabble-post")
def render_scrabble_post(req: ScrabblePostRequest):
    width, height = req.canvas_size
    img = Image.new("RGB", (width, height), color="#1E293B")  # Deep slate board
    draw = ImageDraw.Draw(img)

    # 1. Outer Border
    margin = 50
    draw.rounded_rectangle([(margin, margin), (width - margin, height - margin)], radius=24, outline="#334155", width=3)

    # 2. Top Badge Hook
    badge_font = get_font(28, bold=True)
    draw.rounded_rectangle([(margin + 60, margin + 40), (width - margin - 60, margin + 110)], radius=16, fill="#DC2626")
    draw.text((margin + 100, margin + 58), "🔥 DAILY SCRABBLE CHALLENGE", fill="#FFFFFF", font=badge_font)

    # 3. Main Question / Hook Title
    title_font = get_font(46, bold=True)
    lines = textwrap.wrap(req.hook_title, width=28)
    cur_y = margin + 150
    for l in lines:
        tbox = draw.textbbox((0, 0), l, font=title_font)
        draw.text(((width - (tbox[2] - tbox[0])) // 2, cur_y), l, fill="#F8FAFC", font=title_font)
        cur_y += 60

    # 4. Render the Wooden Tile Rack
    letters = [l.strip().upper() for l in req.rack_letters.split(",") if l.strip()]
    num_tiles = len(letters)
    tile_size = 110
    gap = 14
    total_rack_w = (num_tiles * tile_size) + ((num_tiles - 1) * gap)
    start_x = (width - total_rack_w) // 2
    rack_y = 480

    # Wooden Rack Shelf Bar
    draw.rounded_rectangle([(start_x - 30, rack_y + tile_size - 10), (start_x + total_rack_w + 30, rack_y + tile_size + 40)], radius=8, fill="#8B4513")
    draw.rectangle([(start_x - 20, rack_y + tile_size - 6), (start_x + total_rack_w + 20, rack_y + tile_size + 14)], fill="#A0522D")

    # Draw Each Letter Tile
    for i, l in enumerate(letters):
        tx = start_x + i * (tile_size + gap)
        draw_scrabble_tile(draw, tx, rack_y - 20, tile_size, l)

    # 5. Hint & Points Callout Box
    hint_y = rack_y + 190
    draw.rounded_rectangle([(margin + 80, hint_y), (width - margin - 80, hint_y + 90)], radius=14, fill="#0F172A", outline="#475569", width=2)
    hint_text = f"💡 Hint: {req.hint}  |  Max Score: {req.points} Pts"
    h_font = get_font(26, bold=False)
    hbox = draw.textbbox((0, 0), hint_text, font=h_font)
    draw.text(((width - (hbox[2] - hbox[0])) // 2, hint_y + 30), hint_text, fill="#38BDF8", font=h_font)

    # 6. Call To Action Footer
    cta_font = get_font(32, bold=True)
    cta_text = "👇 COMMENT YOUR WORD BELOW! 👇"
    cbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    draw.text(((width - (cbox[2] - cbox[0])) // 2, height - margin - 110), cta_text, fill="#FBBF24", font=cta_font)

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return Response(content=buf.getvalue(), media_type="image/png")
  
