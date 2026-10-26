import io
import os
import uuid
import chess
import chess.svg
import cairosvg
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

class TrapRequest(BaseModel):
    title: str
    moves: list[str]

def get_font(size):
    """Try loading clean TrueType fonts available on Linux/Render, or fallback safely."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)  # Pillow 10.1+ supports size
    except Exception:
        return ImageFont.load_default()

def draw_pill(draw, box, fill_color, radius=18):
    """Draws rounded pill background for badges and titles."""
    draw.rounded_rectangle(box, radius=radius, fill=fill_color)

def create_board_frame(board, trap_title, is_first_frame=False):
    # 1. Render board SVG to PNG in memory (960px wide for optimal mobile borders)
    svg_data = chess.svg.board(board=board, size=960)
    png_bytes = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
    board_img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")

    # 2. Modern dark-slate background (1080x1920)
    canvas = Image.new("RGBA", (1080, 1920), (14, 17, 23, 255))
    
    # 3. Paste board slightly above center (Y: 480 to 1440) to leave room for Reel safe UI
    board_x = (1080 - 960) // 2
    board_y = 480
    canvas.paste(board_img, (board_x, board_y), board_img)

    draw = ImageDraw.Draw(canvas)
    
    # Load responsive font sizes
    title_font = get_font(52)
    sub_font = get_font(38)
    badge_font = get_font(32)
    brand_font = get_font(36)

    # --- TOP SECTION (Safe Zone: 240px to 460px) ---
    
    # Red/Gold "DIRTY TRAP" Badge
    badge_text = "♟️ CHESS OPENING TRAP"
    draw_pill(draw, [(540 - 240, 240), (540 + 240, 295)], fill_color=(220, 38, 38, 255), radius=14)
    draw.text((540, 267), badge_text, fill=(255, 255, 255), anchor="mm", font=badge_font)

    # Trap Title (Bold Gold with dark pill backing for contrast)
    draw.text((540, 355), trap_title.upper(), fill=(250, 204, 21), anchor="mm", font=title_font)

    # Sub-hook (Turn indicator)
    turn_text = "White to move and win 🎯" if board.turn == chess.WHITE else "Black to move and punish ⚡"
    draw.text((540, 420), turn_text, fill=(226, 232, 240), anchor="mm", font=sub_font)

    # --- BOTTOM SECTION (Safe Zone: 1470px to 1620px) ---
    
    # Branded Academy Footer Pill
    draw_pill(draw, [(540 - 320, 1490), (540 + 320, 1560)], fill_color=(30, 41, 59, 255), radius=16)
    draw.text((540, 1525), "Chess Players Ahmedabad", fill=(255, 255, 255), anchor="mm", font=brand_font)

    return np.array(canvas.convert("RGB"))

@app.post("/render")
def render_reel(req: TrapRequest):
    try:
        board = chess.Board()
        frames = []
        durations = []

        # Frame 1: The Initial Hook / Cover Look (Hold for 2.2 seconds so viewers can read)
        frames.append(create_board_frame(board, req.title, is_first_frame=True))
        durations.append(2.2)

        # Animate each move with clear pacing
        for move in req.moves:
            board.push_uci(move)
            frames.append(create_board_frame(board, req.title))
            durations.append(1.3)

        # Final checkmate / win hold (3.2 seconds)
        durations[-1] = 3.2

        output_path = f"/tmp/{uuid.uuid4().hex[:8]}.mp4"
        clip = ImageSequenceClip(frames, durations=durations)
        clip.write_videofile(output_path, fps=24, codec="libx264", audio=False, preset="ultrafast")

        return FileResponse(output_path, media_type="video/mp4", filename="chess_reel.mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
