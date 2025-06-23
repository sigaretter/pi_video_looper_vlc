import os
import time
import vlc
import threading
import logging
import subprocess
import re
import random
# Setup logging
logging.basicConfig(level=logging.DEBUG)

VIDEO_DIR = '/home/pi/video'
CHECK_INTERVAL = 1.0  # seconds

# Expanded list of supported file extensions
SUPPORTED_EXTENSIONS = [
    # Video files
    '.mp4', '.avi', '.mkv', '.flv', '.mov', '.wmv', '.mpg', '.mpeg', '.m4v',
    '.3gp', '.3g2', '.mxf', '.ogm', '.ogv', '.asf', '.rm', '.rmvb', '.webm',
    '.vob', '.ts', '.divx', '.dvr-ms', '.m2ts', '.mts', '.h264', '.h265',
    # Audio files
    '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.wma', '.opus',
    '.alac', '.aiff', '.dts', '.ac3', '.mid', '.midi',
    # Image files (if needed)
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'
]


vlc_instance = vlc.Instance()
player = vlc_instance.media_player_new()
media_lock = threading.Lock()

def get_media_list():
    logging.debug(f"Listing files in directory: {VIDEO_DIR}")
    return [f for f in os.listdir(VIDEO_DIR) if any(f.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)]

def play_file(filename, loop=False):
    filepath = os.path.join(VIDEO_DIR, filename)
    if os.path.exists(filepath):
        with media_lock:
            media = vlc_instance.media_new(filepath)
            player.set_media(media)
            player.set_fullscreen(True)
            if loop:
                player.get_media().add_option('input-repeat=999999')
            player.play()
            logging.info(f"Playing file: {filename} {'(loop)' if loop else ''}")
    else:
        logging.error(f"File not found: {filename}")

def pause_or_resume():
    with media_lock:
        state = player.get_state()
        if state == vlc.State.Playing:
            player.pause()
            logging.info("Paused playback")
        elif state == vlc.State.Paused:
            player.play()
            logging.info("Resumed playback")

def stop():
    with media_lock:
        player.stop()
        logging.info("Stopped playback")

def jump_to(timestamp):
    with media_lock:
        total_time = player.get_length() // 1000  # seconds
        if total_time > 0 and 0 <= timestamp <= total_time:
            player.set_time(timestamp * 1000)
            logging.info(f"Jumped to {timestamp} seconds")
        else:
            logging.error("Invalid timestamp")

def print_state():
    with media_lock:
        state = player.get_state()
        if state in [vlc.State.Playing, vlc.State.Paused]:
            media = player.get_media()
            filename = media.get_mrl().replace('file://', '') if media else 'No file'
            current_time = player.get_time() // 1000
            total_time = player.get_length() // 1000
        else:
            filename = 'No file'
            current_time = 0
            total_time = 0
    current_time_str = time.strftime('%H:%M:%S', time.gmtime(current_time))
    total_time_str = time.strftime('%H:%M:%S', time.gmtime(total_time))
    print(f"State: {state}, File: {filename}, Position: {current_time_str} / {total_time_str}")

def check_player_state():
    while True:
        with media_lock:
            state = player.get_state()
            if state == vlc.State.Ended or (state == vlc.State.Paused and player.get_time() >= player.get_length()):
                player.stop()
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    state_check_thread = threading.Thread(target=check_player_state, daemon=True)
    state_check_thread.start()

    # Play a random video file immediately on script start
    files = get_media_list()
    if files:
        random_file = random.choice(files)
        play_file(random_file, loop=False)
        print(f"Randomly selected and playing: {random_file}")
    else:
        print("No media files found to play.")

    print("VLC Player CLI Control")
    print("Available commands: list, play <file>, loop <file>, pause, stop, jump <seconds>, state, quit")
    while True:
        cmd = input("> ").strip()
        if cmd == "list":
            files = get_media_list()
            for f in files:
                print(f)
        elif cmd.startswith("play "):
            _, filename = cmd.split(" ", 1)
            play_file(filename, loop=False)
        elif cmd.startswith("loop "):
            _, filename = cmd.split(" ", 1)
            play_file(filename, loop=True)
        elif cmd == "pause":
            pause_or_resume()
        elif cmd == "stop":
            stop()
        elif cmd.startswith("jump "):
            try:
                _, t = cmd.split(" ", 1)
                jump_to(int(t))
            except Exception:
                print("Usage: jump <seconds>")
        elif cmd == "state":
            print_state()
        elif cmd == "quit":
            stop()
            break
        else:
            print("Unknown command")
