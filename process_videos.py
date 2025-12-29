import os
import json
import yt_dlp
from datetime import datetime

VIDEOS_FILE = 'videos.txt'
JSON_FILE = 'videos.json'
OUTPUT_DIR = 'shorts'
MAX_SIZE_MB = 99  # Slightly under 100MB to be safe

def load_processed_videos():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_processed_videos(data):
    with open(JSON_FILE, 'w') as f:
        json.dump(data, f, indent=2)

import sys

def get_video_urls(filename=None):
    if filename is None:
        filename = VIDEOS_FILE
    if not os.path.exists(filename):
        return []
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def process_videos():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    processed_data = load_processed_videos()
    processed_ids = {item['id'] for item in processed_data}
    
    input_file = sys.argv[1] if len(sys.argv) > 1 else VIDEOS_FILE
    urls = get_video_urls(input_file)
    print(f"Reading from {input_file}...")
    
    # Configure yt-dlp
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(OUTPUT_DIR, '%(id)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'ignoreerrors': True,
        'no_warnings': True,
        'quiet': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in urls:
            try:
                # Extract info first to get ID
                info = ydl.extract_info(url, download=False)
                if not info:
                    continue
                
                video_id = info['id']
                
                if video_id in processed_ids:
                    print(f"Skipping {video_id} (already processed)")
                    continue

                print(f"Processing {video_id}...")
                
                # Download
                info = ydl.extract_info(url, download=True)
                
                # Get the final filename
                # Note: ydl.prepare_filename(info) might not be accurate if merging happened or extension changed
                # So we verify strictly.
                expected_filename = os.path.join(OUTPUT_DIR, f"{video_id}.mp4")
                
                if not os.path.exists(expected_filename):
                    print(f"File not found after download: {expected_filename}")
                    continue

                file_size = os.path.getsize(expected_filename)
                file_size_mb = file_size / (1024 * 1024)

                if file_size_mb > MAX_SIZE_MB:
                    print(f"File {video_id}.mp4 is too large ({file_size_mb:.2f}MB). Deleting...")
                    os.remove(expected_filename)
                    continue

                # Prepare metadata
                video_data = {
                    'id': video_id,
                    'title': info.get('title'),
                    'description': info.get('description'),
                    'poster_url': info.get('thumbnail'),
                    'webpage_url': info.get('webpage_url'),
                    'local_path': expected_filename,
                    'file_size': file_size,
                    'uploaded': False,
                    'downloaded_at': datetime.now().isoformat()
                }

                processed_data.append(video_data)
                save_processed_videos(processed_data)
                processed_ids.add(video_id)
                print(f"Successfully processed {video_id}")

            except Exception as e:
                print(f"Error processing {url}: {str(e)}")

if __name__ == "__main__":
    process_videos()
