# Social media asset pipeline

This directory contains the source asset catalog for the automated social media rendering pipeline.

Expected format rules
- All raster graphics should be saved as transparent PNG files.
- Use lossless compression or placeholder transparent files initially.
- Keep layered artwork on transparent canvas and preserve high-resolution source assets.
- Use consistent naming conventions with lowercase prefixes and explicit intent (for example: `ic_phone.png`, `bg_navy.png`).
- Font files must be shipped as TTF with valid glyph coverage for Latin characters and punctuation.

Folder requirements

## assets/logo
- Purpose: Brand logo variants for the service.
- Recommended source sizes: 1024x1024 px or larger, transparent background.
- Required format: PNG with alpha transparency.
- Files:
  - `logo_vasant_white.png`
  - `logo_vasant_dark.png`

## assets/fonts
- Purpose: Typography for text overlays and promotional content.
- Required format: TTF font files only.
- Recommended fallback stack: Poppins, Inter.
- Files:
  - `Poppins-Bold.ttf`
  - `Poppins-Medium.ttf`
  - `Inter-Regular.ttf`

## assets/icons
- Purpose: Small decorative and informational icons used across templates.
- Recommended size: 256x256 px, 512x512 px, or scalable vector source preserved for export.
- Required format: Transparent PNG with clean edges.
- Files:
  - `ic_phone.png`
  - `ic_pin.png`
  - `ic_clock.png`
  - `ic_basket.png`
  - `ic_steam_iron.png`
  - `ic_sparkles.png`

## assets/templates_bg
- Purpose: Background canvases and branded template base images.
- Recommended size: 1080x1920 px for portrait social content, or 1080x1080 px for square assets.
- Required format: Transparent PNG background with optional color fills and subtle gradients.
- Files:
  - `bg_cyan.png`
  - `bg_navy.png`
  - `bg_soft_ivory.png`

## assets/stickers_overlays
- Purpose: Small overlays, badges, callout cards, and decorative sticker elements.
- Recommended size: 800x800 px or larger with transparent background.
- Required format: Transparent PNG overlays that can be composited over templates.
- Files:
  - `notification_card.png`
  - `selection_box.png`
  - `bubble_pattern.png`

Suggested production notes
- Export final artwork at 2x or 3x resolution for sharp output on high-density displays.
- Keep a safe zone around the outer edges of each asset to avoid clipping after placement.
- Maintain consistent naming and file permissions so the pipeline can enumerate assets reliably.
