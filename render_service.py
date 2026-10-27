import io
import os
import textwrap
import uuid
import chess
import chess.svg
import cairosvg
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

# ==========================================
# 1. SHARED HELPERS & FONTS
# ==========================================
def get_font(size, bold=False):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()

def draw_pill(draw, box, fill_color, radius=18):
    draw.rounded_rectangle(box, radius=radius, fill=fill_color)

# ==========================================
# 2. CHESS REEL PIPELINE (/render)
# ==========================================
class TrapRequest(BaseModel):
    title: str
    moves: list[str]

def create_board_frame(board, trap_title, last_move=None):
    custom_colors = {
        'square light': '#FDF5E6',
        'square dark': '#8E3200',
        'margin': '#1A1110',
        'coord': '#D4AF37',
    }

    arrows = []
    if last_move:
        arrows = [chess.svg.Arrow(last_move.from_square, last_move.to_square, color="#FFD700BB")]

    svg_data = chess.svg.board(
        board=board,
        size=960,
        colors=custom_colors,
        lastmove=last_move,
        arrows=arrows
    )
    png_bytes = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
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
            preset="ultrafast"
        )
        return FileResponse(output_path, media_type="video/mp4", filename="chess_reel.mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 3. VASANT LAUNDRY FLYER PIPELINE (/render-flyer)
# ==========================================
class FlyerRequest(BaseModel):
    title: str
    headline: str
    subtext: str

@app.post("/render-flyer")
def render_flyer(req: FlyerRequest):
    try:
        width, height = 1080, 1350
        canvas = Image.new("RGBA", (width, height), (10, 17, 40, 255))
        draw = ImageDraw.Draw(canvas)

        # 1. Elegant Double Borders
        draw.rounded_rectangle([(40, 40), (width - 40, height - 40)], radius=36, outline=(218, 165, 32, 220), width=4)
        draw.rounded_rectangle([(52, 52), (width - 52, height - 52)], radius=28, outline=(255, 255, 255, 40), width=2)

        # 2. Header Branding Pill (Clean Text without unsupported emoji)
        draw_pill(draw, [(140, 95), (width - 140, 175)], fill_color=(19, 31, 66, 255), radius=22)
        brand_font = get_font(36, bold=True)
        draw.text((width // 2, 135), "VASANT POWER LAUNDRY", fill=(245, 197, 24), anchor="mm", font=brand_font)

        # 3. Topic Badge
        category_font = get_font(26, bold=True)
        topic_tag = f"• {req.title.upper()} •"
        draw.text((width // 2, 225), topic_tag, fill=(180, 200, 240), anchor="mm", font=category_font)

        # 4. Central Graphic Card Container
        card_box = [(90, 280), (width - 90, 1020)]
        draw.rounded_rectangle(card_box, radius=30, fill=(18, 26, 54, 255), outline=(218, 165, 32, 120), width=2)

        # Decorative Geometric Accent (Replaces missing emoji glyphs)
        accent_font = get_font(34, bold=True)
        draw.text((width // 2, 360), "◆   ◆   ◆", fill=(218, 165, 32), anchor="mm", font=accent_font)

        # 5. Dynamic Headline (Auto text-wrapping)
        headline_font = get_font(46, bold=True)
        wrapped_headline = textwrap.fill(req.headline, width=25)
        draw.text((width // 2, 540), wrapped_headline, fill=(255, 255, 255), anchor="mm", font=headline_font, align="center")

        # 6. Supporting Subtext
        subtext_font = get_font(32, bold=False)
        wrapped_subtext = textwrap.fill(req.subtext, width=38)
        draw.text((width // 2, 820), wrapped_subtext, fill=(210, 222, 245), anchor="mm", font=subtext_font, align="center")

        # 7. Footer: Trust Badges & Porbandar Address (Safe margins)
        footer_pill_box = [(80, 1070), (width - 80, 1250)]
        draw.rounded_rectangle(footer_pill_box, radius=24, fill=(14, 21, 46, 255), outline=(218, 165, 32, 180), width=2)

        footer_title = get_font(27, bold=True)
        draw.text((width // 2, 1120), "100% Pocket Custody Guarantee  •  Smart WhatsApp Slips", fill=(245, 197, 24), anchor="mm", font=footer_title)

        address_font = get_font(24, bold=False)
        address_text = "Wagheshwari Plot, Porbandar (360575)  |  7 Days Open"
        draw.text((width // 2, 1190), address_text, fill=(220, 230, 245), anchor="mm", font=address_font)

        output_path = f"/tmp/{uuid.uuid4().hex[:8]}.png"
        canvas.convert("RGB").save(output_path, "PNG", quality=95)
        return FileResponse(output_path, media_type="image/png", filename="vasant_flyer.png")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
