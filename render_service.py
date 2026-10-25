import io
import os
import uuid
import chess
import chess.svg
import cairosvg
import numpy as np
from PIL import Image, ImageDraw
from moviepy.editor import ImageSequenceClip
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

class TrapRequest(BaseModel):
    title: str
    moves: list[str]

def create_board_frame(board, trap_title):
    svg_data = chess.svg.board(board=board, size=900)
    png_bytes = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
    board_img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")

    # 1080x1920 vertical canvas
    canvas = Image.new("RGBA", (1080, 1920), (18, 22, 30, 255))
    canvas.paste(board_img, (90, 510), board_img)

    draw = ImageDraw.Draw(canvas)
    draw.text((540, 320), trap_title, fill=(255, 215, 0), anchor="mm")
    draw.text((540, 400), "Can you spot the win?", fill=(255, 255, 255), anchor="mm")
    draw.text((540, 1550), "♟️ Chess Players Ahmedabad", fill=(180, 180, 180), anchor="mm")

    return np.array(canvas.convert("RGB"))

@app.post("/render")
def render_reel(req: TrapRequest):
    try:
        board = chess.Board()
        frames = [create_board_frame(board, req.title)]
        durations = [2.5]

        for move in req.moves:
            board.push_uci(move)
            frames.append(create_board_frame(board, req.title))
            durations.append(1.4)

        durations[-1] = 3.0  # Hold checkmate

        output_path = f"/tmp/{uuid.uuid4().hex[:8]}.mp4"
        clip = ImageSequenceClip(frames, durations=durations)
        clip.write_videofile(output_path, fps=24, codec="libx264", audio=False, preset="ultrafast")

        return FileResponse(output_path, media_type="video/mp4", filename="chess_reel.mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
