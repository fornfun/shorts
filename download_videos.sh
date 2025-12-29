#!/bin/bash

# Check if yt-dlp is installed
if ! command -v yt-dlp &> /dev/null; then
    echo "yt-dlp could not be found. Please install it first."
    echo "You can install it using brew: brew install yt-dlp"
    exit 1
fi

# Download videos listed in videos.txt
# -a: load/batch file containing URLs
# -o: output template (%(id)s.%(ext)s)
# --merge-output-format mp4: ensure the final container is mp4
# -f: select best video/audio combination that results in mp4 or can be merged to mp4

echo "Starting download of videos listed in videos.txt..."

yt-dlp \
    -a videos.txt \
    -o "%(id)s.%(ext)s" \
    --format "bestvideo+bestaudio/best" \
    --merge-output-format mp4 \
    --recode-video mp4 \
    --ignore-errors \
    --no-playlist

echo "Download complete."
