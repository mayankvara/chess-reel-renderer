import os
import io
import tempfile
from typing import List, Optional
from fastapi import FastAPI, Response, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

import chess
import chess.svg
import cairosvg
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip

from flyer_service import (
    BusinessFlyerRequest,
    ChessQuoteFlyerRequest,
    render_business_flyer_image,
    render_chess_quote_image
)
from scrabble_service import (
    ScrabblePostRequest,
    render_scrabble_post,
)

app = FastAPI(title="Chess Reel & Flyer Renderer API")


# ==========================================
# Reel Request Schema
# ==========================================

class ReelRequest(BaseModel):
    title: str = "Chess Tactics"
    moves: List[str]
    fontSize: Optional[int] = 30
    readStyle: Optional[str] = "short"


# ==========================================
# Reel Generator Endpoint
# ==========================================

@app.post("/render")
def render_reel(req: ReelRequest):
    if not req.moves:
        raise HTTPException(status_code=400, detail="Move list cannot be empty.")

    board = chess.Board()
    temp_dir = tempfile.mkdtemp()
    frame_paths = []

    try:
        # Initial starting position
        svg_start = chess.svg.board(board=board, size=720)
        start_frame_path = os.path.join(temp_dir, "frame_000.png")
        cairosvg.svg2png(bytestring=svg_start.encode("utf-8"), write_to=start_frame_path)
        frame_paths.append(start_frame_path)

        # Generate each move with arrow highlights
        for idx, uci_move in enumerate(req.moves):
            try:
                move = chess.Move.from_uci(uci_move)
                if move not in board.legal_moves:
                    continue

                arrows = [chess.svg.Arrow(move.from_square, move.to_square, color="#ffaa00cc")]
                board.push(move)

                svg_board = chess.svg.board(board=board, size=720, arrows=arrows)
                frame_path = os.path.join(temp_dir, f"frame_{idx + 1:03d}.png")
                cairosvg.svg2png(bytestring=svg_board.encode("utf-8"), write_to=frame_path)
                frame_paths.append(frame_path)
            except Exception:
                continue

        if not frame_paths:
            raise HTTPException(status_code=500, detail="Failed to render move frames.")

        # Hold final frame longer
        frame_paths.extend([frame_paths[-1]] * 3)

        output_video_path = os.path.join(temp_dir, "chess_reel.mp4")
        clip = ImageSequenceClip(frame_paths, fps=1.2)

        # Attach move sound if present
        if os.path.exists("move.wav"):
            try:
                audio = AudioFileClip("move.wav")
                clip = clip.set_audio(audio)
            except Exception:
                pass

        clip.write_videofile(
            output_video_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            preset="ultrafast",
            threads=2,
            logger=None
        )

        return FileResponse(output_video_path, media_type="video/mp4", filename=f"{req.title}.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Business Flyer Endpoints (Vasant Laundry)
# ==========================================

@app.post("/render-flyer")
def render_business_flyer(req: BusinessFlyerRequest):
    try:
        png_bytes = render_business_flyer_image(req)
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flyer rendering error: {str(e)}")


@app.get("/render-flyer")
def render_business_flyer_get(
    business_name: str = Query("Vasant Power Laundry"),
    headline: str = Query("Premium Laundry & Steam Pressing"),
    cta_text: str = Query("Drop Off Today")
):
    req = BusinessFlyerRequest(business_name=business_name, headline=headline, cta_text=cta_text)
    png_bytes = render_business_flyer_image(req)
    return Response(content=png_bytes, media_type="image/png")


# ==========================================
# Chess Quote Flyer Endpoint (Master Quotes Sheet)
# ==========================================

@app.post("/render-quote-flyer")
def render_quote_flyer(req: ChessQuoteFlyerRequest):
    try:
        png_bytes = render_chess_quote_image(req)
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quote flyer rendering error: {str(e)}")


# ==========================================
# Scrabble Post Endpoint
# ==========================================

@app.post("/render-scrabble-post")
def render_scrabble_post_route(req: ScrabblePostRequest):
    try:
        return render_scrabble_post(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scrabble post rendering error: {str(e)}")


@app.get("/render-scrabble-post")
def render_scrabble_post_get(
    rack_letters: str = Query("Q, U, I, Z, Z, E, D"),
    hook_title: str = Query("Can you find a 35-point word?"),
    points: int = Query(35),
    hint: str = Query("Uses double Z and Q!"),
    branding: str = Query("Word Masters Club")
):
    req = ScrabblePostRequest(
        rack_letters=rack_letters,
        hook_title=hook_title,
        points=points,
        hint=hint,
        branding=branding
    )
    return render_scrabble_post(req)
