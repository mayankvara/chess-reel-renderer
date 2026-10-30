#!/usr/bin/env bash
set -euo pipefail

mkdir -p \
  assets/logo \
  assets/fonts \
  assets/icons \
  assets/templates_bg \
  assets/stickers_overlays

# Create placeholder asset files.
# These are intentionally empty HTML/text placeholders for the scaffold; replace with actual binary assets.
: > assets/logo/logo_vasant_white.png
: > assets/logo/logo_vasant_dark.png
: > assets/fonts/Poppins-Bold.ttf
: > assets/fonts/Poppins-Medium.ttf
: > assets/fonts/Inter-Regular.ttf
: > assets/icons/ic_phone.png
: > assets/icons/ic_pin.png
: > assets/icons/ic_clock.png
: > assets/icons/ic_basket.png
: > assets/icons/ic_steam_iron.png
: > assets/icons/ic_sparkles.png
: > assets/templates_bg/bg_cyan.png
: > assets/templates_bg/bg_navy.png
: > assets/templates_bg/bg_soft_ivory.png
: > assets/stickers_overlays/notification_card.png
: > assets/stickers_overlays/selection_box.png
: > assets/stickers_overlays/bubble_pattern.png

printf '%s\n' 'Asset scaffold created successfully.'
