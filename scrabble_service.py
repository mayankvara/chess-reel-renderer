import io
import math
import os
import textwrap
import traceback
from typing import Tuple, Union

from fastapi import FastAPI, Response
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFilter, ImageFont

app = FastAPI(title="Scrabble Puzzle & Reel Generator")

LETTER_POINTS = {
    'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4,
    'I': 1, 'J': 8, 'K': 5, 'L': 1, 'M': 3, 'N': 1, 'O': 1, 'P': 3,
    'Q': 10, 'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 4, 'W': 4, 'X': 8,
    'Y': 4, 'Z': 10,
}


def safe_rounded_rectangle(draw: ImageDraw.ImageDraw, box, radius: int, **kwargs):
    try:
        draw.rounded_rectangle(box, radius=radius, **kwargs)
    except Exception:
        try:
            draw.rectangle(box, **kwargs)
        except Exception:
            pass


def safe_textbbox(draw: ImageDraw.ImageDraw, text: str, font, fallback_size: int = 16):
    try:
        return draw.textbbox((0, 0), text, font=font)
    except Exception:
        try:
            width = len(text) * fallback_size * 0.6
            return (0, 0, width, fallback_size)
        except Exception:
            return (0, 0, 0, 0)


def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()


def get_mono_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "C:\\Windows\\Fonts\\consola.ttf",
        "DejaVuSansMono.ttf",
        "Consolas.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return get_font(size, bold=True)


def safe_points(value) -> int:
    try:
        raw = str(value).strip().strip("\"'")
        if not raw:
            return 0
        if "." in raw:
            return int(float(raw))
        return int(raw)
    except (TypeError, ValueError):
        return 0


def draw_star(draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float, color, inner_ratio: float = 0.45):
    try:
        inner_r = radius * inner_ratio
        points = []
        for i in range(10):
            angle = -math.pi / 2 + (i * math.pi / 5)
            r = radius if i % 2 == 0 else inner_r
            points.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        draw.polygon(points, fill=color)
    except Exception:
        try:
            draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=color)
        except Exception:
            pass


def draw_tile(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, letter: str):
    try:
        shadow_color = (19, 18, 16, 200)
        safe_rounded_rectangle(draw, [(x + 8, y + 10), (x + size + 8, y + size + 10)], 18, fill=shadow_color)
        safe_rounded_rectangle(draw, [(x, y), (x + size, y + size)], 18, fill=(247, 214, 120), outline=(191, 122, 35), width=3)
        safe_rounded_rectangle(draw, [(x + 8, y + 8), (x + size - 8, y + size - 8)], 14, fill=(255, 233, 163), outline=(241, 186, 72), width=2)

        letter_upper = (letter or "").strip().upper()
        font_letter = get_font(int(size * 0.58), bold=True)
        lbox = safe_textbbox(draw, letter_upper, font_letter, fallback_size=int(size * 0.58))
        lw = max(0, lbox[2] - lbox[0])
        lh = max(0, lbox[3] - lbox[1])
        draw.text((x + (size - lw) // 2, y + (size - lh) // 2 - 4), letter_upper, fill=(30, 27, 24), font=font_letter)

        pts = str(LETTER_POINTS.get(letter_upper, 0))
        if pts != "0":
            font_pts = get_font(int(size * 0.22), bold=True)
            draw.text((x + size - int(size * 0.34), y + size - int(size * 0.34)), pts, fill=(92, 58, 28), font=font_pts)
    except Exception:
        traceback.print_exc()
        try:
            safe_rounded_rectangle(draw, [(x, y), (x + size, y + size)], 0, fill=(247, 214, 120), outline=(191, 122, 35), width=3)
            draw.text((x + 12, y + 12), (letter or "").strip().upper(), fill=(30, 27, 24), font=ImageFont.load_default())
        except Exception:
            traceback.print_exc()


class ScrabblePostRequest(BaseModel):
    rack_letters: str = "Q, U, I, Z, Z, E, D"
    hook_title: str = "Can you find a 35-point word?"
    points: Union[int, str] = 35
    hint: str = "Uses double Z and Q!"
    branding: str = "Word Masters Club"
    canvas_size: Tuple[int, int] = (1080, 1080)


def generate_scrabble_image(req: ScrabblePostRequest):
    width, height = req.canvas_size
    try:
        base = Image.new("RGBA", (width, height), (10, 15, 29, 255))
        bg = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw_bg = ImageDraw.Draw(bg)

        for y in range(height):
            ratio = y / max(1, height)
            r = int(10 + (30 - 10) * ratio)
            g = int(15 + (43 - 15) * ratio)
            b = int(29 + (68 - 29) * ratio)
            draw_bg.line([(0, y), (width, y)], fill=(r, g, b, 255), width=1)

        for x in range(0, width, 28):
            for y in range(0, height, 28):
                alpha = 18 if ((x // 28) + (y // 28)) % 2 == 0 else 12
                draw_bg.ellipse((x, y, x + 3, y + 3), fill=(148, 163, 184, alpha))

        glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse((120, 80, 960, 900), fill=(56, 189, 248, 40))
        glow_draw.ellipse((260, 260, 820, 1020), fill=(129, 140, 248, 24))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=30))

        base = Image.alpha_composite(base, bg)
        base = Image.alpha_composite(base, glow)
        base = base.convert("RGB")
        draw = ImageDraw.Draw(base)

        header_x1, header_y1 = 90, 80
        header_x2, header_y2 = width - 90, 170
        safe_rounded_rectangle(draw, [(header_x1, header_y1), (header_x2, header_y2)], 30, fill=(15, 23, 42, 210), outline=(56, 189, 248, 255), width=3)
        safe_rounded_rectangle(draw, [(header_x1 + 14, header_y1 + 12), (header_x2 - 14, header_y2 - 12)], 22, fill=(20, 30, 46, 180), outline=(120, 119, 250, 180), width=2)

        draw_star(draw, header_x1 + 74, (header_y1 + header_y2) // 2, 16, (251, 191, 36), inner_ratio=0.45)
        draw_star(draw, header_x2 - 74, (header_y1 + header_y2) // 2, 14, (56, 189, 248), inner_ratio=0.42)

        badge_text = "WORD MASTERS | DAILY CHALLENGE"
        badge_font = get_font(28, bold=True)
        bbox = safe_textbbox(draw, badge_text, badge_font, fallback_size=28)
        badge_w = max(0, bbox[2] - bbox[0])
        draw.text(((width - badge_w) / 2, header_y1 + 34), badge_text, fill=(248, 250, 252), font=badge_font)

        title_font = get_font(68, bold=True)
        hook_lines = textwrap.wrap((req.hook_title or "SCRABBLE CHALLENGE").strip(), width=22)
        start_y = 250
        for idx, line in enumerate(hook_lines):
            line_bbox = safe_textbbox(draw, line, title_font, fallback_size=68)
            line_w = max(0, line_bbox[2] - line_bbox[0])
            draw.text(((width - line_w) / 2, start_y + idx * 76), line, fill=(255, 255, 255), font=title_font, stroke_width=2, stroke_fill=(15, 23, 42))

        letters = [part.strip().upper() for part in (req.rack_letters or "Q, U, I, Z, Z, E, D").split(",") if part.strip()]
        if not letters:
            letters = ["Q", "U", "I", "Z", "Z", "E", "D"]

        tile_size = 116
        gap = 18
        total_rack_w = len(letters) * tile_size + (len(letters) - 1) * gap
        start_x = (width - total_rack_w) // 2
        rack_y = 450

        rack_shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        rack_draw = ImageDraw.Draw(rack_shadow)
        safe_rounded_rectangle(rack_draw, [(start_x - 30, rack_y + tile_size - 10), (start_x + total_rack_w + 30, rack_y + tile_size + 52)], 18, fill=(45, 36, 30, 240))
        safe_rounded_rectangle(rack_draw, [(start_x - 20, rack_y + tile_size - 4), (start_x + total_rack_w + 20, rack_y + tile_size + 26)], 12, fill=(136, 90, 56, 240))
        safe_rounded_rectangle(rack_draw, [(start_x - 12, rack_y + tile_size - 2), (start_x + total_rack_w + 12, rack_y + tile_size + 18)], 10, fill=(184, 132, 82, 255))
        rack_draw.line([(start_x - 18, rack_y + tile_size - 2), (start_x + total_rack_w + 18, rack_y + tile_size - 2)], fill=(245, 206, 129, 255), width=3)
        base = Image.alpha_composite(base, rack_shadow)
        draw = ImageDraw.Draw(base)

        for i, letter in enumerate(letters):
            tx = start_x + i * (tile_size + gap)
            draw_tile(draw, tx, rack_y, tile_size, letter)

        card_w = 760
        card_h = 110
        card_x = (width - card_w) // 2
        card_y = 640
        safe_rounded_rectangle(draw, [(card_x, card_y), (card_x + card_w, card_y + card_h)], 22, fill=(17, 24, 39, 205), outline=(46, 204, 255, 180), width=2)

        hint_text = "HINT: " + (req.hint or "Use the rack strategically.").strip()
        hint_font = get_font(24, bold=True)
        hbox = safe_textbbox(draw, hint_text, hint_font, fallback_size=24)
        hint_w = max(0, hbox[2] - hbox[0])
        draw.text((card_x + 36, card_y + 28), hint_text, fill=(148, 163, 184), font=hint_font)

        score_value = safe_points(req.points)
        score_text = f"MAX SCORE: {score_value} PTS"
        score_font = get_mono_font(28)
        sbox = safe_textbbox(draw, score_text, score_font, fallback_size=28)
        score_w = max(0, sbox[2] - sbox[0])
        draw.text((card_x + card_w - score_w - 36, card_y + 30), score_text, fill=(94, 234, 212), font=score_font)

        cta_text = "[ >> ] COMMENT YOUR WORD BELOW"
        cta_font = get_font(30, bold=True)
        cbox = safe_textbbox(draw, cta_text, cta_font, fallback_size=30)
        cta_w = max(0, cbox[2] - cbox[0])
        cta_x = (width - cta_w) // 2
        cta_y = 835
        safe_rounded_rectangle(draw, [(cta_x - 28, cta_y - 18), (cta_x + cta_w + 28, cta_y + 60)], 22, fill=(245, 158, 11), outline=(255, 220, 120), width=2)
        draw.text((cta_x, cta_y + 2), cta_text, fill=(17, 24, 39), font=cta_font)

        footer_brand = (req.branding or "WORD MASTERS CLUB").strip() or "WORD MASTERS CLUB"
        footer_font = get_font(22, bold=True)
        footer_box = safe_textbbox(draw, footer_brand.upper(), footer_font, fallback_size=22)
        draw.text(((width - max(0, footer_box[2] - footer_box[0])) / 2, 970), footer_brand.upper(), fill=(184, 195, 209), font=footer_font)

        output = io.BytesIO()
        base.save(output, format="PNG")
        return output.getvalue()
    except Exception:
        traceback.print_exc()
        try:
            fallback = Image.new("RGB", (width, height), (15, 23, 42))
            d = ImageDraw.Draw(fallback)
            default_font = ImageFont.load_default()
            d.rectangle([(30, 30), (width - 30, height - 30)], fill=(27, 38, 54))
            d.text((60, 80), "DAILY SCRABBLE CHALLENGE", fill=(255, 255, 255), font=default_font)
            d.text((60, 140), str(req.hook_title or "Can you find a word?"), fill=(255, 255, 255), font=default_font)
            d.text((60, 220), f"MAX SCORE: {safe_points(req.points)}", fill=(255, 255, 255), font=default_font)
            out = io.BytesIO()
            fallback.save(out, format="PNG")
            return out.getvalue()
        except Exception:
            traceback.print_exc()
            final = Image.new("RGB", (width, height), (15, 23, 42))
            final_buf = io.BytesIO()
            final.save(final_buf, format="PNG")
            return final_buf.getvalue()


@app.post("/render-scrabble-post")
def render_scrabble_post(req: ScrabblePostRequest):
    try:
        png_bytes = generate_scrabble_image(req)
        return Response(content=png_bytes, media_type="image/png")
    except Exception:
        traceback.print_exc()
        raise


@app.get("/render-scrabble-post")
def render_scrabble_post_get(
    rack_letters: str = "Q, U, I, Z, Z, E, D",
    hook_title: str = "Can you find a 35-point word?",
    points: str = "35",
    hint: str = "Uses double Z and Q!",
    branding: str = "Word Masters Club",
):
    req = ScrabblePostRequest(
        rack_letters=rack_letters,
        hook_title=hook_title,
        points=points,
        hint=hint,
        branding=branding,
    )
    return render_scrabble_post(req)
    
