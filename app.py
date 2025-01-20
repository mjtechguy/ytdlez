from flask import Flask, render_template, request, send_file
import os
import threading
from yt_dlp import YoutubeDL

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key

# Configure download directory
DOWNLOADS_DIR = os.path.join(os.getcwd(), 'downloads')
TMP_DOWNLOADS_DIR = os.path.join(DOWNLOADS_DIR, 'tmp')

# Ensure directories exist
os.makedirs(TMP_DOWNLOADS_DIR, exist_ok=True)

# Initialize yt-dlp options to only download MP4
ydl_opts = {
    'format': 'bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
    'postprocessors': [{
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4',
    }],
    'outtmpl': os.path.join(TMP_DOWNLOADS_DIR, '%(title)s.%(ext)s'),
}

def clean_filename(filename):
    return ''.join(c if c.isalnum() else '_' for c in filename).rstrip('_')

def download_process(url, type_):
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Handle playlists
            if 'entries' in info:
                for entry in info['entries']:
                    process_video(entry, type_)
            else:
                process_video(info, type_)

        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def process_video(info, type_):
    title = clean_filename(info.get('title', 'untitled'))
    
    # Download the MP4 file to tmp directory
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([info['webpage_url']])
    
    input_path = os.path.join(TMP_DOWNLOADS_DIR, f"{title}.mp4")
    output_path_mp3 = os.path.join(DOWNLOADS_DIR, f"{title}_320kbps.mp3")
    
    try:
        if type_ == 'mp3':
            # Convert to MP3 using FFmpeg
            ffmpeg_command = (
                f"ffmpeg -i {input_path} "
                "-vn -ar 44100 -ac 2 -ab 320k -f mp3 "
                f"{output_path_mp3}"
            )
            result = os.system(ffmpeg_command)
            
            if result != 0:
                print("Error converting to MP3.")
                return False
            
        else:
            # Move the MP4 file to the main downloads directory
            output_path_mp4 = os.path.join(DOWNLOADS_DIR, f"{title}.mp4")
            os.rename(input_path, output_path_mp4)
    
    finally:
        # Clean up temporary files
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except Exception as e:
                print(f"Error removing temp file: {e}")
    
    return True

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    type_ = request.form.get('type')
    
    # Start download process in a background thread
    thread = threading.Thread(target=download_process, args=(url, type_))
    thread.start()
    
    return render_template('download_status.html', message="Download is processing...")

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
