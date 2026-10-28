# Chess Reel Renderer

A Python FastAPI service that creates:

- chess-themed social media video reels from move sequences
- branded promotional flyers for local businesses

This project combines chess board rendering, image generation, and video export into a simple API service suitable for deployment on Render or a local FastAPI server.

## Project purpose

The app is designed to generate visually rich marketing content:

- `render_service.py` builds a chess board animation from UCI move lists and exports it as an MP4 reel.
- `flyer_service.py` generates a PNG flyer for businesses with customizable branding, headline, services, and CTA copy.
- `render.yaml` configures deployment on Render.

## Repository structure

- `render_service.py` — main FastAPI app for chess reel generation and flyer support logic
- `flyer_service.py` — standalone flyer generation service with similar API patterns
- `render.yaml` — Render deployment configuration
- `requirements.txt` — Python dependencies
- `README.md` — project documentation

## How the chess reel works

The `/render` endpoint accepts a POST request with:

```json
{
  "title": "Royal Defense",
  "moves": [
    "e2e4",
    "e7e5",
    "g1f3",
    "b8c6"
  ]
}
```

Flow:

1. Initializes a chess board
2. Creates frames for the opening position and every move
3. Highlights the latest move with an arrow
4. Renders board SVGs to PNG using CairoSVG
5. Combines frames into an MP4 video using MoviePy
6. Optionally attaches sound effects if `move.wav`, `capture.wav`, or `checkmate.wav` are available in the runtime directory

The API responds with the generated MP4 file.

## How the flyer generator works

The `/render-flyer` endpoint accepts a POST payload matching the `FlyerRequest` model.

Example payload:

```json
{
  "business_name": "Vasant Power Laundry",
  "tagline": "Crisp • Clean • Express Care",
  "headline": "Premium Laundry & Steam Pressing",
  "subheadline": "Fast turnaround, hygienic washing, and door-to-door convenience.",
  "services": [
    "Wash & Fold",
    "Steam Ironing / Pressing",
    "Dry Cleaning Care",
    "Curtain & Blanket Deep Clean"
  ],
  "offer_badge": "Starting at ₹99 / Month / Plans Available",
  "phone_or_whatsapp": "+91 XXXXXXXXXX",
  "address_line": "Porbandar, Gujarat",
  "cta_text": "Drop Off Today / WhatsApp for Pickup"
}
```

It generates a square promotional flyer image using PIL and returns it as a PNG response.

There is also a GET version for simple URL-based usage:

```text
/render-flyer?business_name=Your%20Business&headline=Your%20Headline
```

## Local setup

1. Create a virtual environment and activate it
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the API server:

```bash
uvicorn render_service:app --host 0.0.0.0 --port 8000
```

4. Open the API docs at:

```text
http://localhost:8000/docs
```

## Deployment

This repository includes a Render configuration in `render.yaml`.

```yaml
services:
  - type: web
    name: chess-reel-renderer
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn render_service:app --host 0.0.0.0 --port $PORT
    plan: free
```

Deploying on Render will run the FastAPI app with the required dependencies installed automatically.

## Dependencies

Key libraries used in the service include:

- `fastapi` — API framework
- `uvicorn` — ASGI server
- `python-chess` — chess board logic and move generation
- `cairosvg` — SVG to PNG conversion
- `moviepy` — video composition and export
- `Pillow` — image generation and text rendering
- `pydantic` — request validation

## Notes

- The reel generation route is intentionally designed for short social-media-style chess content.
- Sound files like `move.wav`, `capture.wav`, and `checkmate.wav` can be added to enhance the output if available.
- The flyer engine is modular and can be adapted for different business categories or branding styles.

## License

This project does not include a license file, so usage and redistribution should follow the repository owner's policy unless explicitly stated otherwise.
