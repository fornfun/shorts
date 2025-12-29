import os
import json
import subprocess
import sys
from datetime import datetime

VIDEOS_FILE = 'videos.txt'
JSON_FILE = 'videos.json'
OUTPUT_DIR = 'shorts'

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
    print(f"Reading from {input_file}...", flush=True)

    for url in urls:
        # Extract ID cheaply first using simple string manipulation or regex if possible
        # But yt-dlp is safer. Let's rely on --print-json output 
        # However, to skip already processed ones efficiently without hitting network we might want a quick check
        # But URLs might be different forms. Let's just run yt-dlp and leverage its skipping if we wanted
        # But we want to control the logic.
        
        # We'll rely on yt-dlp to tell us the ID after simulation or start.
        # Actually, let's just run it. If we have the ID in our JSON, we might have skipped it before? 
        # No, let's check if the file exists?
        
        # New approach: Run yt-dlp for each URL.
        # Flags:
        # -o "shorts/%(id)s.%(ext)s"
        # --max-filesize 100M
        # --print-json (to capture metadata)
        # --no-simulate (actually download)
        # --ignore-errors
        
        print(f"Processing {url}...", flush=True)
        
        # Check if we already have this URL processed? 
        # Hard to map URL to ID without calling yt-dlp.
        # We will let yt-dlp run. 

        cmd = [
            "yt-dlp",
            url,
            "-o", f"{OUTPUT_DIR}/%(id)s.%(ext)s",
            "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "--max-filesize", "100M",
            "--recode-video", "mp4",
            "--print-json",
            "--no-simulate",
            "--no-warnings"
        ]

        if os.path.exists("www.youtube.com_cookies.txt"):
            print("Using cookies from www.youtube.com_cookies.txt")
            cmd.extend(["--cookies", "www.youtube.com_cookies.txt"])
        elif os.path.exists("cookies.txt"):
            print("Using cookies from cookies.txt")
            cmd.extend(["--cookies", "cookies.txt"])
        
        try:
            # Capture output
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Check for max-filesize abort
            if result.returncode != 0:
                if "File is larger than" in result.stderr:
                    print(f"Skipped {url}: File larger than 100MB")
                else:
                    print(f"Error downloading {url}: {result.stderr.splitlines()[-1] if result.stderr else 'Unknown error'}")
                continue

            # Parse JSON output
            # yt-dlp --print-json outputs the JSON on one line, but video might be downloaded.
            # Sometimes it prints the JSON even if it downloads.
            
            output_json = None
            for line in result.stdout.splitlines():
                try:
                    data = json.loads(line)
                    if 'id' in data and 'title' in data:
                        output_json = data
                        break
                except json.JSONDecodeError:
                    continue
            
            if not output_json:
                print(f"Could not extract metadata for {url}")
                continue

            video_id = output_json['id']
            
            if video_id in processed_ids:
                print(f"Already tracked {video_id}. Updating metadata if needed.")
                continue

            expected_filename = os.path.join(OUTPUT_DIR, f"{video_id}.mp4")
            
            if not os.path.exists(expected_filename):
                print(f"File not found: {expected_filename} (maybe skipped or failed silently?)")
                continue

            file_size = os.path.getsize(expected_filename)

            # Metadata
            video_data = {
                'id': video_id,
                'title': output_json.get('title'),
                'description': output_json.get('description'),
                'poster_url': output_json.get('thumbnail'),
                'webpage_url': output_json.get('webpage_url'),
                'local_path': expected_filename,
                'file_size': file_size,
                'uploaded': False,
                'downloaded_at': datetime.now().isoformat()
            }
            
            processed_data.append(video_data)
            save_processed_videos(processed_data)
            processed_ids.add(video_id)
            print(f"Success: {video_id}")

        except Exception as e:
            print(f"Exception processing {url}: {e}")

if __name__ == "__main__":
    process_videos()
