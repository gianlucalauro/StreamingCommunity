# 31.01.24

import sys
import time
import logging
import subprocess
from typing import List, Dict


# Internal utilities
from StreamingCommunity.Util._jsonConfig import config_manager
from StreamingCommunity.Util.os import os_manager, os_summary, suppress_output
from StreamingCommunity.Util.console import console


# Logic class
from .util import need_to_force_to_ts, check_duration_v_a
from .capture import capture_ffmpeg_real_time
from ..M3U8 import M3U8_Codec


# Config
DEBUG_MODE = config_manager.get_bool("DEFAULT", "debug")
DEBUG_FFMPEG = "debug" if DEBUG_MODE else "error"
USE_CODEC = config_manager.get_bool("M3U8_CONVERSION", "use_codec")
USE_VCODEC = config_manager.get_bool("M3U8_CONVERSION", "use_vcodec")
USE_ACODEC = config_manager.get_bool("M3U8_CONVERSION", "use_acodec")
USE_BITRATE = config_manager.get_bool("M3U8_CONVERSION", "use_bitrate")
USE_GPU = config_manager.get_bool("M3U8_CONVERSION", "use_gpu")
FFMPEG_DEFAULT_PRESET = config_manager.get("M3U8_CONVERSION", "default_preset")


# Variable
TQDM_USE_LARGE_BAR = config_manager.get_int('M3U8_DOWNLOAD', 'tqdm_use_large_bar')
FFMPEG_PATH = os_summary.ffmpeg_path


def join_video(video_path: str, out_path: str, codec: M3U8_Codec = None):
    
    """
    Joins single ts video file to mp4
    
    Parameters:
        - video_path (str): The path to the video file.
        - out_path (str): The path to save the output file.
        - vcodec (str): The video codec to use. Defaults to 'copy'.
        - acodec (str): The audio codec to use. Defaults to 'aac'.
        - bitrate (str): The bitrate for the audio stream. Defaults to '192k'.
        - force_ts (bool): Force video path to be mpegts as input.
    """

    if not os_manager.check_file(video_path):
        logging.error("Missing input video for ffmpeg conversion.")
        sys.exit(0)

    # Start command with locate ffmpeg
    ffmpeg_cmd = [FFMPEG_PATH]

    # Enabled the use of gpu
    if USE_GPU:
        ffmpeg_cmd.extend(['-hwaccel', 'cuda'])

    # Add mpegts to force to detect input file as ts file
    if need_to_force_to_ts(video_path):
        console.log("[red]Force input file to 'mpegts'.")
        ffmpeg_cmd.extend(['-f', 'mpegts'])
        vcodec = "libx264"

    # Insert input video path
    ffmpeg_cmd.extend(['-i', video_path])

    # Add output Parameters
    if USE_CODEC and codec != None:
        if USE_VCODEC:
            if codec.video_codec_name: 
                if not USE_GPU: 
                    ffmpeg_cmd.extend(['-c:v', codec.video_codec_name])
                else: 
                    ffmpeg_cmd.extend(['-c:v', 'h264_nvenc'])
            else: 
                console.log("[red]Cant find vcodec for 'join_audios'")
        else:
            if USE_GPU:
                ffmpeg_cmd.extend(['-c:v', 'h264_nvenc'])


        if USE_ACODEC:
            if codec.audio_codec_name: 
                ffmpeg_cmd.extend(['-c:a', codec.audio_codec_name])
            else: 
                console.log("[red]Cant find acodec for 'join_audios'")

        if USE_BITRATE:
            ffmpeg_cmd.extend(['-b:v',  f'{codec.video_bitrate // 1000}k'])
            ffmpeg_cmd.extend(['-b:a',  f'{codec.audio_bitrate // 1000}k'])

    else:
        ffmpeg_cmd.extend(['-c', 'copy'])

    # Ultrafast preset always or fast for gpu
    if not USE_GPU:
        ffmpeg_cmd.extend(['-preset', FFMPEG_DEFAULT_PRESET])
    else:
        ffmpeg_cmd.extend(['-preset', 'fast'])

    # Overwrite
    ffmpeg_cmd += [out_path, "-y"]

    # Run join
    if DEBUG_MODE:
        subprocess.run(ffmpeg_cmd, check=True)
    else:

        if TQDM_USE_LARGE_BAR:
            capture_ffmpeg_real_time(ffmpeg_cmd, "[cyan]Join video")
            print()

        else:
            console.log(f"[purple]FFmpeg [white][[cyan]Join video[white]] ...")
            with suppress_output():
                capture_ffmpeg_real_time(ffmpeg_cmd, "[cyan]Join video")
                print()

    time.sleep(0.5)
    if not os_manager.check_file(out_path):
        logging.error("Missing output video for ffmpeg conversion video.")
        sys.exit(0)


def join_audios(video_path: str, audio_tracks: List[Dict[str, str]], out_path: str, codec: M3U8_Codec = None):
    """
    Joins audio tracks with a video file using FFmpeg.
    
    Parameters:
        - video_path (str): The path to the video file.
        - audio_tracks (list[dict[str, str]]): A list of dictionaries containing information about audio tracks.
            Each dictionary should contain the 'path' key with the path to the audio file.
        - out_path (str): The path to save the output file.
    """

    if not os_manager.check_file(video_path):
        logging.error("Missing input video for ffmpeg conversion.")
        sys.exit(0)

    video_audio_same_duration = check_duration_v_a(video_path, audio_tracks[0].get('path'))

    # Start command with locate ffmpeg
    ffmpeg_cmd = [FFMPEG_PATH]

    # Enabled the use of gpu
    if USE_GPU:
        ffmpeg_cmd.extend(['-hwaccel', 'cuda'])

    # Insert input video path
    ffmpeg_cmd.extend(['-i', video_path])

    # Add audio tracks as input
    for i, audio_track in enumerate(audio_tracks):
        if os_manager.check_file(audio_track.get('path')):
            ffmpeg_cmd.extend(['-i', audio_track.get('path')])
        else:
            logging.error(f"Skip audio join: {audio_track.get('path')} dont exist")

    # Map the video and audio streams
    ffmpeg_cmd.append('-map')
    ffmpeg_cmd.append('0:v')            # Map video stream from the first input (video_path)
    
    for i in range(1, len(audio_tracks) + 1):
        ffmpeg_cmd.append('-map')
        ffmpeg_cmd.append(f'{i}:a')     # Map audio streams from subsequent inputs

    # Add output Parameters
    if USE_CODEC:
        if USE_VCODEC:
            if codec.video_codec_name: 
                if not USE_GPU: 
                    ffmpeg_cmd.extend(['-c:v', codec.video_codec_name])
                else: 
                    ffmpeg_cmd.extend(['-c:v', 'h264_nvenc'])
            else: 
                console.log("[red]Cant find vcodec for 'join_audios'")
        else:
            if USE_GPU:
                ffmpeg_cmd.extend(['-c:v', 'h264_nvenc'])

        if USE_ACODEC:
            if codec.audio_codec_name: 
                ffmpeg_cmd.extend(['-c:a', codec.audio_codec_name])
            else: 
                console.log("[red]Cant find acodec for 'join_audios'")

        if USE_BITRATE:
            ffmpeg_cmd.extend(['-b:v',  f'{codec.video_bitrate // 1000}k'])
            ffmpeg_cmd.extend(['-b:a',  f'{codec.audio_bitrate // 1000}k'])

    else:
        ffmpeg_cmd.extend(['-c', 'copy'])

    # Ultrafast preset always or fast for gpu
    if not USE_GPU:
        ffmpeg_cmd.extend(['-preset', FFMPEG_DEFAULT_PRESET])
    else:
        ffmpeg_cmd.extend(['-preset', 'fast'])

    # Use shortest input path for video and audios
    if not video_audio_same_duration:
        logging.info("[red]Use shortest input.")
        ffmpeg_cmd.extend(['-shortest', '-strict', 'experimental'])

    # Overwrite
    ffmpeg_cmd += [out_path, "-y"]

    # Run join
    if DEBUG_MODE:
        subprocess.run(ffmpeg_cmd, check=True)
    else:

        if TQDM_USE_LARGE_BAR:
            capture_ffmpeg_real_time(ffmpeg_cmd, "[cyan]Join audio")
            print()

        else:
            console.log(f"[purple]FFmpeg [white][[cyan]Join audio[white]] ...")
            with suppress_output():
                capture_ffmpeg_real_time(ffmpeg_cmd, "[cyan]Join audio")
                print()

    time.sleep(0.5)
    if not os_manager.check_file(out_path):
        logging.error("Missing output video for ffmpeg conversion audio.")
        sys.exit(0)


def join_subtitle(video_path: str, subtitles_list: List[Dict[str, str]], out_path: str):
    """
    Joins subtitles with a video file using FFmpeg.
    
    Parameters:
        - video (str): The path to the video file.
        - subtitles_list (list[dict[str, str]]): A list of dictionaries containing information about subtitles.
            Each dictionary should contain the 'path' key with the path to the subtitle file and the 'name' key with the name of the subtitle.
        - out_path (str): The path to save the output file.
    """

    if not os_manager.check_file(video_path):
        logging.error("Missing input video for ffmpeg conversion.")
        sys.exit(0)

    # Start command with locate ffmpeg
    ffmpeg_cmd = [FFMPEG_PATH, "-i", video_path]

    # Add subtitle input files first
    for subtitle in subtitles_list:
        if os_manager.check_file(subtitle.get('path')):
            ffmpeg_cmd += ["-i", subtitle['path']]
        else:
            logging.error(f"Skip subtitle join: {subtitle.get('path')} doesn't exist")

    # Add maps for video and audio streams
    ffmpeg_cmd += ["-map", "0:v", "-map", "0:a"]

    # Add subtitle maps and metadata
    for idx, subtitle in enumerate(subtitles_list):
        ffmpeg_cmd += ["-map", f"{idx + 1}:s"]
        ffmpeg_cmd += ["-metadata:s:s:{}".format(idx), "title={}".format(subtitle['language'])]

    # Add output Parameters
    if USE_CODEC:
        ffmpeg_cmd.extend(['-c:v', 'copy', '-c:a', 'copy', '-c:s', 'mov_text'])
    else:
        ffmpeg_cmd.extend(['-c', 'copy', '-c:s', 'mov_text'])

    # Overwrite
    ffmpeg_cmd += [out_path, "-y"]
    logging.info(f"FFmpeg command: {ffmpeg_cmd}")


    # Run join
    if DEBUG_MODE:
        subprocess.run(ffmpeg_cmd, check=True)
    else:

        if TQDM_USE_LARGE_BAR:
            capture_ffmpeg_real_time(ffmpeg_cmd, "[cyan]Join subtitle")
            print()

        else:
            console.log(f"[purple]FFmpeg [white][[cyan]Join subtitle[white]] ...")
            with suppress_output():
                capture_ffmpeg_real_time(ffmpeg_cmd, "[cyan]Join subtitle")
                print()

    time.sleep(0.5)
    if not os_manager.check_file(out_path):
        logging.error("Missing output video for ffmpeg conversion subtitle.")
        sys.exit(0)
