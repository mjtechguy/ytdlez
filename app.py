from flask import Flask, render_template, request, jsonify, url_for, send_from_directory
import os
import re
import threading
from yt_dlp import YoutubeDL

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key

# Configure download directory
DOWNLOADS_DIR = os.path.join(os.getcwd(), 'downloads')
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Dictionary to keep track of download statuses
download_status = {}

def clean_filename(filename):
    """
    Sanitize the filename by converting to lowercase, replacing spaces with underscores,
    and removing special characters.
    """
    filename = filename.lower()
    filename = filename.replace(' ', '_')
    filename = re.sub(r'[^a-z0-9_.]', '', filename)
    return filename

def download_process(url, convert_to_mp3, task_id):
    try:
        # Extract video information to get the title
        with YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=False)
            title = info_dict.get('title', 'untitled')
            sanitized_title = clean_filename(title)

        # Set up yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best' if convert_to_mp3 else 'bestvideo+bestaudio',
            'outtmpl': os.path.join(DOWNLOADS_DIR, f'{sanitized_title}.%(ext)s'),
            'postprocessors': [],
        }

        if convert_to_mp3:
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            })

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Update status to ready
        download_status[task_id] = {
            'status': 'ready',
            'filename': f"{sanitized_title}.mp3" if convert_to_mp3 else f"{sanitized_title}.mp4"
        }
    except Exception as e:
        print(f"Error: {e}")
        # Update status to error
        download_status[task_id] = {'status': 'error'}

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    convert_to_mp3 = request.form.get('convert_to_mp3') == 'on'

    # Generate a unique task ID
    task_id = str(len(download_status) + 1)
    download_status[task_id] = {'status': 'processing'}

    # Start download process in a background thread
    thread = threading.Thread(target=download_process, args=(url, convert_to_mp3, task_id))
    thread.start()

    return render_template('download_status.html', task_id=task_id)

@app.route('/check_status/<task_id>', methods=['GET'])
def check_status(task_id):
    status_info = download_status.get(task_id, {'status': 'error'})
    if status_info['status'] == 'ready':
        download_url = url_for('download_file', filename=status_info['filename'])
        return jsonify(status='ready', download_url=download_url)
    elif status_info['status'] == 'error':
        return jsonify(status='error')
    else:
        return jsonify(status='processing')

@app.route('/downloads/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(DOWNLOADS_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)