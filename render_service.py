import io
import os
import textwrap
import uuid

import cairosvg
import chess
import chess.svg
import numpy as np
from fastapi import FastAPI, HTTPException
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
# 3. FLYER PIPELINE (/render-flyer)
# ==========================================
class FlyerRequest(BaseModel):
    title: str
    headline: str
    subtext: str


@app.post("/render-flyer")
def render_flyer(req: FlyerRequest):
    try:
        width, height = 1080, 1440
        canvas = Image.new("RGBA", (width, height), (11, 23, 48, 255))
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([(32, 32), (width - 32, height - 32)], outline=(200, 155, 65, 220), width=3)
        draw.rectangle([(44, 44), (width - 44, height - 44)], outline=(140, 105, 45, 120), width=1)

        fan_r = 52
        draw_corner_fan(draw, (44, 44), fan_r, "TL")
        draw_corner_fan(draw, (width - 44, 44), fan_r, "TR")
        draw_corner_fan(draw, (44, height - 44), fan_r, "BL")
        draw_corner_fan(draw, (width - 44, height - 44), fan_r, "BR")

        plaque_w, plaque_h = 420, 110
        plaque_x1 = (width - plaque_w) // 2
        plaque_y1 = 80
        plaque_box = [(plaque_x1, plaque_y1), (plaque_x1 + plaque_w, plaque_y1 + plaque_h)]
        draw_notched_card(draw, plaque_box, radius=18, fill=(35, 43, 50, 255), outline=(218, 172, 78, 240), width=2)

        vasant_font = get_font(42, bold=True, serif=True)
        draw.text((width // 2, plaque_y1 + 42), "VASANT", fill=(245, 204, 110), anchor="mm", font=vasant_font)

        sub_brand_font = get_font(20, bold=True, serif=True)
        draw.text((width // 2, plaque_y1 + 80), "POWER LAUNDRY", fill=(215, 175, 85), anchor="mm", font=sub_brand_font)

        pill_w, pill_h = 580, 60
        pill_x1 = (width - pill_w) // 2
        pill_y1 = 225
        pill_box = [(pill_x1, pill_y1), (pill_x1 + pill_w, pill_y1 + pill_h)]
        draw.rounded_rectangle(pill_box, radius=30, fill=(235, 185, 75, 255), outline=(255, 220, 130, 200), width=2)

        pill_tag = f"• {req.title.upper()} •"
        category_font = get_font(25, bold=True, serif=False)
        draw.text((width // 2, pill_y1 + pill_h // 2), pill_tag, fill=(11, 23, 48), anchor="mm", font=category_font)

        card_box = [(120, 320), (width - 120, 940)]
        draw_notched_card(draw, card_box, radius=24, fill=(36, 44, 52, 255), outline=(218, 172, 78, 230), width=3)

        headline_font = get_font(52, bold=True, serif=True)
        wrapped_headline = textwrap.fill(req.headline, width=22)
        draw.text((width // 2, 500), wrapped_headline, fill=(255, 255, 255), anchor="mm", font=headline_font, align="center")

        subtext_font = get_font(28, bold=False, serif=False)
        wrapped_subtext = textwrap.fill(req.subtext, width=34)
        draw.text((width // 2, 750), wrapped_subtext, fill=(220, 230, 245), anchor="mm", font=subtext_font, align="center")

        badge_y1 = 980
        badge_h = 160
        gap = 36
        badge_w = (width - 240 - gap) // 2

        b1_x1 = 120
        b1_box = [(b1_x1, badge_y1), (b1_x1 + badge_w, badge_y1 + badge_h)]
        draw_notched_card(draw, b1_box, radius=18, fill=(33, 40, 48, 255), outline=(218, 172, 78, 220), width=2)
        badge_font = get_font(24, bold=True, serif=True)
        b1_text = "100% Pocket\nCustody\nGuarantee"
        draw.text((b1_x1 + badge_w // 2, badge_y1 + badge_h // 2), b1_text, fill=(245, 204, 110), anchor="mm", font=badge_font, align="center")

        b2_x1 = b1_x1 + badge_w + gap
        b2_box = [(b2_x1, badge_y1), (b2_x1 + badge_w, badge_y1 + badge_h)]
        draw_notched_card(draw, b2_box, radius=18, fill=(33, 40, 48, 255), outline=(218, 172, 78, 220), width=2)
        b2_text = "Smart\nWhatsApp\nSlips"
        draw.text((b2_x1 + badge_w // 2, badge_y1 + badge_h // 2), b2_text, fill=(245, 204, 110), anchor="mm", font=badge_font, align="center")

        strip_y = height - 100
        draw.line([(32, strip_y), (width - 32, strip_y)], fill=(190, 145, 60, 180), width=2)

        address_font = get_font(22, bold=False, serif=False)
        address_text = "Wagheshwari Plot, Porbandar (360575)  |  7 Days Open"
        draw.text((width // 2, height - 52), address_text, fill=(240, 245, 255), anchor="mm", font=address_font)

        output_path = f"/tmp/{uuid.uuid4().hex[:8]}.png"
        canvas.convert("RGB").save(output_path, "PNG", quality=95)
        return FileResponse(output_path, media_type="image/png", filename="vasant_flyer.png")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
