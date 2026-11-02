#!/usr/bin/env bash
# Source video -> scrub-friendly media: all-intra MP4 (+ optional WebM) and a WebP image sequence + manifest.json.
# Usage: scrub.sh <input-video> <out-dir> [width=1280] [fps=30] [seq_fps=24]
# Why all-intra: seeking a normal GOP video decodes from the last keyframe, so scrubbing stutters. -g 1 makes every
# frame a keyframe; files are 3-6x larger, which is acceptable only for short clips (<= ~6 s, <= ~6 MB).
set -euo pipefail
IN=${1:?input video}; OUT=${2:?out dir}; W=${3:-1280}; FPS=${4:-30}; SEQ_FPS=${5:-24}
CRF=${SCRUB_CRF:-20}            # x264 quality; 18-23 sane
WEBP_Q=${SCRUB_WEBP_Q:-72}      # sequence frame quality; 65-80 sane
mkdir -p "$OUT/frames"
VF="scale='min($W,iw)':-2:flags=lanczos,fps=$FPS"
# all-intra H.264: every frame a keyframe, no B-frames, faststart for range requests, no audio
ffmpeg -y -loglevel error -i "$IN" -vf "$VF" -an -c:v libx264 -preset slow -crf "$CRF" -g 1 -bf 0 \
  -pix_fmt yuv420p -movflags +faststart "$OUT/scrub.mp4"
# optional VP9 all-intra WebM (Chrome/Firefox; Safari plays MP4 only): enable with SCRUB_WEBM=1
if [ "${SCRUB_WEBM:-0}" = 1 ]; then
  ffmpeg -y -loglevel error -i "$IN" -vf "$VF" -an -c:v libvpx-vp9 -crf 32 -b:v 0 -g 1 -row-mt 1 "$OUT/scrub.webm"
fi
# image sequence: canvas drawImage of decoded stills is the most predictable scrub path (works everywhere, no seek).
# WebP when this ffmpeg build has libwebp, else JPEG (mjpeg is always built in; -q:v 2-5 = high quality).
if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libwebp; then
  EXT=webp; ENC=(-c:v libwebp -quality "$WEBP_Q")
else
  EXT=jpg; ENC=(-c:v mjpeg -q:v "${SCRUB_JPG_Q:-4}")
fi
ffmpeg -y -loglevel error -i "$IN" -vf "scale='min($W,iw)':-2:flags=lanczos,fps=$SEQ_FPS" "${ENC[@]}" "$OUT/frames/f%04d.$EXT"
N=$(ls "$OUT/frames" | wc -l | tr -d ' ')
IFS=, read -r FW FH < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$OUT/scrub.mp4")
printf '{"frames": %s, "pattern": "frames/f%%04d.%s", "start": 1, "fps": %s, "width": %s, "height": %s}\n' "$N" "$EXT" "$SEQ_FPS" "$FW" "$FH" > "$OUT/manifest.json"
du -k "$OUT/scrub.mp4" "$OUT/frames" | sed 's/^/KB /'
cat "$OUT/manifest.json"
