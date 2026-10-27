import io
import os
import textwrap
import uuid

import cairosvg
import chess
import chess.svg
import numpy as np
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
from moviepy.editor import AudioFileClip, CompositeAudioClip, ImageSequenceClip
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel

app = FastAPI()


# ==========================================
# 1. SHARED HELPERS & FONTS
# ==========================================
def get_font(size: int, bold: bool = False, serif: bool = False):
    """Loads a system font with a safe fallback chain."""
    font_names = []
    if serif:
        font_names = [
            "DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf",
            "Times New Roman Bold.ttf" if bold else "Times New Roman.ttf",
            "Georgia Bold.ttf" if bold else "Georgia.ttf",
        ]
    else:
        font_names = [
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
            "Arial Bold.ttf" if bold else "Arial.ttf",
            "NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf",
        ]

    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue

    candidates = [
        "DejaVuSans.ttf",
        "Arial.ttf",
        "LiberationSans-Regular.ttf",
        "FreeSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue

    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def draw_pill(draw, box, fill_color, radius=18):
    draw.rounded_rectangle(box, radius=radius, fill=fill_color)


def draw_corner_fan(draw: ImageDraw.Draw, center: tuple, radius: int, quadrant: str):
    """Draws a luxury gold corner fan / concentric accent arc."""
    cx, cy = center
    gold_outer = (220, 175, 75, 230)
    gold_inner = (245, 210, 120, 160)

    angles = {
        "TL": (0, 90),
        "TR": (90, 180),
        "BL": (270, 360),
        "BR": (180, 270),
    }
    start_a, end_a = angles.get(quadrant, (0, 90))
    bbox_large = [(cx - radius, cy - radius), (cx + radius, cy + radius)]
    bbox_small = [
        (cx - radius * 0.6, cy - radius * 0.6),
        (cx + radius * 0.6, cy + radius * 0.6),
    ]

    draw.arc(bbox_large, start=start_a, end=end_a, fill=gold_outer, width=5)
    draw.arc(bbox_small, start=start_a, end=end_a, fill=gold_inner, width=3)


def draw_notched_card(draw: ImageDraw.Draw, box: list, radius: int, fill: tuple, outline: tuple, width: int = 2):
    """Draws a luxury card with a subtle inset border."""
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    inner_box = [(box[0][0] + 6, box[0][1] + 6), (box[1][0] - 6, box[1][1] - 6)]
    inner_gold = (outline[0], outline[1], outline[2], 90 if len(outline) > 3 else outline[0])
    draw.rounded_rectangle(inner_box, radius=max(4, radius - 4), outline=inner_gold, width=1)


# ==========================================
# 2. CHESS REEL PIPELINE (/render)
# ==========================================
class TrapRequest(BaseModel):
    title: str
    moves: list[str]


def create_board_frame(board, trap_title, last_move=None):
    custom_colors = {
        "square light": "#FDF5E6",
        "square dark": "#8E3200",
        "margin": "#1A1110",
        "coord": "#D4AF37",
    }

    arrows = []
    if last_move:
        arrows = [chess.svg.Arrow(last_move.from_square, last_move.to_square, color="#FFD700BB")]

    svg_data = chess.svg.board(
        board=board,
        size=960,
        colors=custom_colors,
        lastmove=last_move,
        arrows=arrows,
    )
    png_bytes = cairosvg.svg2png(bytestring=svg_data.encode("utf-8"))
    board_img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")

    canvas = Image.new("RGBA", (1080, 1920), (12, 15, 26, 255))
    board_x = (1080 - 960) // 2
    board_y = 480
    canvas.paste(board_img, (board_x, board_y), board_img)

    draw = ImageDraw.Draw(canvas)
    title_font = get_font(50, bold=True)
    sub_font = get_font(36)
    badge_font = get_font(30, bold=True)
    brand_font = get_font(34, bold=True)

    draw_pill(draw, [(540 - 230, 240), (540 + 230, 295)], fill_color=(234, 88, 12, 255), radius=14)
    draw.text((540, 267), "⚔️ SHATRANJ CHESS TRAP", fill=(255, 255, 255), anchor="mm", font=badge_font)
    draw.text((540, 355), trap_title.upper(), fill=(245, 197, 24), anchor="mm", font=title_font)

    turn_text = "White ki chaal, Black game over! 🎯" if board.turn == chess.WHITE else "Black to move & strike! ⚡"
    draw.text((540, 420), turn_text, fill=(229, 231, 235), anchor="mm", font=sub_font)

    draw_pill(draw, [(540 - 310, 1490), (540 + 310, 1560)], fill_color=(30, 41, 59, 255), radius=16)
    draw.text((540, 1525), "Chess Players Ahmedabad", fill=(255, 255, 255), anchor="mm", font=brand_font)

    return np.array(canvas.convert("RGB"))


@app.post("/render")
def render_reel(req: TrapRequest):
    try:
        board = chess.Board()
        frames = []
        durations = []
        audio_clips = []
        current_time = 0.0

        frames.append(create_board_frame(board, req.title))
        durations.append(2.2)
        current_time += 2.2

        has_move_sound = os.path.exists("move.wav")
        has_capture_sound = os.path.exists("capture.wav")
        has_checkmate_sound = os.path.exists("checkmate.wav")

        for move_uci in req.moves:
            move = chess.Move.from_uci(move_uci)
            is_capture = board.is_capture(move)
            board.push(move)

            frames.append(create_board_frame(board, req.title, last_move=move))
            move_duration = 1.3
            durations.append(move_duration)

            if is_capture and has_capture_sound:
                sfx = AudioFileClip("capture.wav").set_start(current_time)
                audio_clips.append(sfx)
            elif has_move_sound:
                sfx = AudioFileClip("move.wav").set_start(current_time)
                audio_clips.append(sfx)

            current_time += move_duration

        durations[-1] = 3.2
        if board.is_checkmate() and has_checkmate_sound:
            audio_clips.append(AudioFileClip("checkmate.wav").set_start(current_time - 1.3))

        output_path = f"/tmp/{uuid.uuid4().hex[:8]}.mp4"
        clip = ImageSequenceClip(frames, durations=durations)

        if audio_clips:
            final_audio = CompositeAudioClip(audio_clips)
            clip = clip.set_audio(final_audio)

        clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac" if audio_clips else None,
            preset="ultrafast",
        )
        return FileResponse(output_path, media_type="video/mp4", filename="chess_reel.mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 3. FLYER GENERATION (/render-flyer)
# ==========================================
class FlyerRequest(BaseModel):
    business_name: str = "Vasant Power Laundry"
    tagline: str = "Crisp • Clean • Express Care"
    headline: str = "Premium Laundry & Steam Pressing"
    subheadline: str = "Fast turnaround, hygienic washing, and door-to-door convenience."
    services: list[str] = [
        "Wash & Fold",
        "Steam Ironing / Pressing",
        "Dry Cleaning Care",
        "Curtain & Blanket Deep Clean",
    ]
    offer_badge: str = "Starting at ₹99 / Month / Plans Available"
    phone_or_whatsapp: str = "+91 XXXXXXXXXX"
    address_line: str = "Porbandar, Gujarat"
    cta_text: str = "Drop Off Today / WhatsApp for Pickup"
    canvas_size: tuple[int, int] = (1080, 1080)


def wrap_lines(draw: ImageDraw.Draw, text: str, font, max_width: int, max_lines: int = 3):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
            if len(lines) >= max_lines - 1:
                break

    if current:
        lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        if len(last) > 18:
            lines[-1] = last[:15] + "..."

    return "\n".join(lines)


def draw_service_chip(draw: ImageDraw.Draw, x: int, y: int, w: int, h: int, label: str):
    draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=16, fill=(240, 250, 252), outline=(0, 168, 150), width=2)
    draw.text((x + 20, y + h / 2), "✓", fill=(0, 168, 150), anchor="lm", font=get_font(26, bold=True))
    label_font = get_font(22, bold=True)
    wrapped = wrap_lines(draw, label, label_font, w - 70, max_lines=2)
    draw.multiline_text((x + 52, y + 16), wrapped, fill=(15, 41, 66), font=label_font, spacing=2)


def generate_flyer_image(req: FlyerRequest) -> Image.Image:
    width, height = req.canvas_size
    canvas = Image.new("RGB", (width, height), "#F4F8FB")
    draw = ImageDraw.Draw(canvas)

    outer_pad = 42
    card = [(outer_pad, outer_pad), (width - outer_pad, height - outer_pad)]
    draw.rounded_rectangle(card, radius=34, fill=(255, 255, 255), outline=(199, 218, 232), width=2)

    top_bubble = [(70, 70), (width - 70, 200)]
    draw.rounded_rectangle(top_bubble, radius=24, fill=(15, 41, 66), outline=(15, 41, 66), width=2)
    brand_font = get_font(38, bold=True)
    draw.text((width / 2, 107), req.business_name.upper(), fill=(255, 255, 255), anchor="mm", font=brand_font)

    tagline_font = get_font(18, bold=True)
    draw.text((width / 2, 150), req.tagline, fill=(123, 181, 214), anchor="mm", font=tagline_font)

    offer_box = [(130, 225), (width - 130, 290)]
    draw.rounded_rectangle(offer_box, radius=22, fill=(245, 158, 11), outline=(255, 216, 121), width=2)
    offer_font = get_font(24, bold=True)
    draw.text((width / 2, 257), req.offer_badge, fill=(255, 255, 255), anchor="mm", font=offer_font)

    hero_panel = [(80, 330), (width - 80, 710)]
    draw.rounded_rectangle(hero_panel, radius=28, fill=(245, 248, 251), outline=(200, 216, 231), width=2)

    accent_circle = [(760, 350), (980, 570)]
    draw.ellipse(accent_circle, fill=(2, 132, 199), outline=(0, 117, 180), width=2)
    icon_font = get_font(54, bold=True)
    draw.text((870, 460), "24H", fill=(255, 255, 255), anchor="mm", font=icon_font)

    headline_font = get_font(42, bold=True)
    headline_width = 540
    headline_text = wrap_lines(draw, req.headline, headline_font, headline_width, max_lines=3)
    draw.multiline_text((100, 380), headline_text, fill=(15, 41, 66), font=headline_font, spacing=6, align="left")

    subheadline_font = get_font(23, bold=False)
    subheadline_text = wrap_lines(draw, req.subheadline, subheadline_font, 560, max_lines=4)
    draw.multiline_text((100, 515), subheadline_text, fill=(37, 66, 90), font=subheadline_font, spacing=4, align="left")

    service_area = [(100, 640), (980, 820)]
    draw.rounded_rectangle(service_area, radius=26, fill=(255, 255, 255), outline=(214, 231, 239), width=2)

    service_items = req.services[:4]
    for idx, service in enumerate(service_items):
        col = idx % 2
        row = idx // 2
        x = 130 + (col * 400)
        y = 670 + (row * 90)
        draw_service_chip(draw, x, y, 330, 64, service)

    footer_box = [(60, 845), (width - 60, 1010)]
    draw.rounded_rectangle(footer_box, radius=30, fill=(15, 41, 66), outline=(15, 41, 66), width=2)

    cta_box = [(120, 882), (width - 120, 945)]
    draw.rounded_rectangle(cta_box, radius=20, fill=(0, 168, 150), outline=(0, 168, 150), width=2)
    cta_font = get_font(24, bold=True)
    draw.text((width / 2, 913), req.cta_text.upper(), fill=(255, 255, 255), anchor="mm", font=cta_font)

    footer_font = get_font(20, bold=True)
    draw.text((width / 2, 968), req.phone_or_whatsapp, fill=(255, 255, 255), anchor="mm", font=footer_font)
    draw.text((width / 2, 994), req.address_line, fill=(206, 225, 239), anchor="mm", font=get_font(18, bold=False))

    return canvas


@app.post("/render-flyer")
def render_flyer(req: FlyerRequest):
    try:
        image = generate_flyer_image(req)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        return Response(content=buffer.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/render-flyer")
def render_flyer_get(
    business_name: str = Query(default="Vasant Power Laundry"),
    tagline: str = Query(default="Crisp • Clean • Express Care"),
    headline: str = Query(default="Premium Laundry & Steam Pressing"),
    subheadline: str = Query(default="Fast turnaround, hygienic washing, and door-to-door convenience."),
    services: str = Query(default="Wash & Fold,Steam Ironing / Pressing,Dry Cleaning Care,Curtain & Blanket Deep Clean"),
    offer_badge: str = Query(default="Starting at ₹99 / Month / Plans Available"),
    phone_or_whatsapp: str = Query(default="+91 XXXXXXXXXX"),
    address_line: str = Query(default="Porbandar, Gujarat"),
    cta_text: str = Query(default="Drop Off Today / WhatsApp for Pickup"),
):
    req = FlyerRequest(
        business_name=business_name,
        tagline=tagline,
        headline=headline,
        subheadline=subheadline,
        services=[item.strip() for item in services.split(",") if item.strip()],
        offer_badge=offer_badge,
        phone_or_whatsapp=phone_or_whatsapp,
        address_line=address_line,
        cta_text=cta_text,
    )
    return render_flyer(req)


# NOTE: Keep the chess reel route intact for the original social-media video renderer.
