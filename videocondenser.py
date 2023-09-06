#!/usr/bin/env python

import os
import argparse
import numpy as np
import math
from shutil import copyfile
from audiotsm import phasevocoder
from audiotsm.io.wav import WavReader, WavWriter
from scipy.io import wavfile
import ffmpeg
import tempfile

class AudioChunk:
    def __init__(self, start_index, end_index, is_loud):
        self.start_index = start_index
        self.end_index = end_index
        self.is_loud = int(is_loud)

AUDIO_FADE_SIZE = 400 # number of ms audio fade lasts
FRAME_MARGIN = 1 # number of quiet frames adjacent to loud frames
SAMPLE_RATE = 44100
FRAME_QUALITY = 3 # 1 is the maximum, 32 is the minimum, 3 is the ffmpeg default

def get_frame_rate(input_file):
    probe = ffmpeg.probe(input_file)
    if "r_frame_rate" in probe and probe["r_frame_rate"]:
        return int(probe["streams"][0]["r_frame_rate"].split("/")[0])
    return 30

def get_max_volume(samples):
    max_value = float(np.max(samples))
    min_value = float(np.min(samples))
    return max(max_value, abs(min_value))

def copy_frame(input_frame : int, output_frame : int, temp_folder):
    src = os.path.join(temp_folder, f"frame{input_frame + 1:09d}.jpg")
    dst = os.path.join(temp_folder, f"new_frame{output_frame + 1:09d}.jpg")
    if not os.path.isfile(src):
        return False
    copyfile(src, dst)
    return True

# shortcircuiting logic for finding loud audio frames in video frames
def find_loud_frame(audio_frames):
    for frame in audio_frames:
        if frame == 1:
            return 1
    return 0

def input_to_output_filename(filename):
    dot_index = filename.rfind(".")
    return f"{filename[:dot_index]}_ALTERED{filename[dot_index:]}"

def process_video(input_file, output_file, loud_threshold, loud_speed, quiet_speed, frame_rate, verbose):
    with tempfile.TemporaryDirectory() as temp_folder:
        if(verbose):
            print(f'output file name: {output_file}')
            print(f'framerate: {frame_rate}')

        new_speed = [quiet_speed, loud_speed]
        stream = ffmpeg.input(input_file)
        ffmpeg.output(stream, os.path.join(temp_folder, "frame%09d.jpg"), qscale=FRAME_QUALITY, loglevel = "error").run() # Use -q:a or q:v
        ffmpeg.output(stream.audio, os.path.join(temp_folder, "full_audio.wav"), ab="160k", ac=2, ar=SAMPLE_RATE, loglevel = "error").run()

        # read using FFMPEG TODO
        _, audio_data = wavfile.read(os.path.join(temp_folder, "full_audio.wav"))
        audio_sample_length = audio_data.shape[0]

        max_volume = get_max_volume(audio_data)

        samples_per_frame = SAMPLE_RATE / frame_rate
        audio_frame_length = math.ceil(audio_sample_length / samples_per_frame)
        loud_audio_frame = np.zeros(audio_frame_length) #convert to boolean array?

        for i in range(audio_frame_length):
            start = int(i * samples_per_frame)
            end = min(int((i + 1) * samples_per_frame), audio_sample_length)
            max_chunks_volume = get_max_volume(audio_data[start:end]) / max_volume
            loud_audio_frame[i] = int(max_chunks_volume > loud_threshold)

        include_frame = np.zeros(audio_frame_length)
        chunks = [AudioChunk(0, 0, 0)] #start_index, end_index, is_loud

        for i in range(1, audio_frame_length):
            start = max(0, i - FRAME_MARGIN)
            end = min(audio_frame_length, i + 1 + FRAME_MARGIN)
            include_frame[i] = find_loud_frame(loud_audio_frame[start:end])
            if include_frame[i] != include_frame[i - 1]:
                chunks.append(AudioChunk(chunks[-1].end_index, i, include_frame[i - 1]))

        chunks.append(AudioChunk(chunks[-1].end_index, audio_frame_length, include_frame[-1]))
        chunks.pop(0)

        if(verbose):
            # Estimated length is higher than actual length due to some small chunks being cut
            estimated_frame_length = 0
            for chunk in chunks:
                estimated_frame_length += (chunk.end_index - chunk.start_index) / new_speed[chunk.is_loud]

            estimated_frame_length = math.ceil(estimated_frame_length / frame_rate)
            estimated_minutes = int(estimated_frame_length // 60)
            estimated_seconds = int(estimated_frame_length % 60)

            print(f"estimated video length: {estimated_minutes}:{estimated_seconds}")

        output_audio = np.zeros((0, audio_data.shape[1]))
        output_ptr = 0
        last_valid_frame = None

        for chunk in chunks:
            curr_chunk = audio_data[int(chunk.start_index * samples_per_frame):int(chunk.end_index * samples_per_frame)]
            start_file = os.path.join(temp_folder, "temp_start.wav")
            end_file = os.path.join(temp_folder, "temp_end.wav")
            wavfile.write(start_file, SAMPLE_RATE, curr_chunk)

            # TODO Dont use phasevocoder or WavReader - use ffmpeg
            with WavReader(start_file) as reader:
                with WavWriter(end_file, reader.channels, reader.samplerate) as writer:
                    tsm = phasevocoder(reader.channels, speed=new_speed[chunk.is_loud])
                    tsm.run(reader, writer)

            _, altered_audio = wavfile.read(end_file) # TODO - use ffmpeg
            altered_audio_length = altered_audio.shape[0]
            end_ptr = output_ptr + altered_audio_length
            output_audio = np.concatenate((output_audio, altered_audio / max_volume))

            if altered_audio_length < AUDIO_FADE_SIZE:
                output_audio[output_ptr:end_ptr] = 0
            else:
                premask = np.arange(AUDIO_FADE_SIZE) / AUDIO_FADE_SIZE
                mask = np.repeat(premask[:, np.newaxis], 2, axis=1)
                output_audio[output_ptr:output_ptr + AUDIO_FADE_SIZE] *= mask
                output_audio[end_ptr - AUDIO_FADE_SIZE:end_ptr] *= 1 - mask

            start_output_frame = math.ceil(output_ptr / samples_per_frame)
            end_output_frame = math.ceil(end_ptr / samples_per_frame)

            for output_frame in range(start_output_frame, end_output_frame):
                input_frame = int(chunk.start_index + new_speed[chunk.is_loud] * (output_frame - start_output_frame))
                if copy_frame(input_frame, output_frame, temp_folder):
                    last_valid_frame = input_frame
                else:
                    copy_frame(last_valid_frame, output_frame, temp_folder)
            
            output_ptr = end_ptr

        wavfile.write(os.path.join(temp_folder, "audio_new.wav"), SAMPLE_RATE, output_audio) # make it pipe directly into a_stream? TODO

        v_stream = ffmpeg.input(os.path.join(temp_folder, "new_frame%09d.jpg"), framerate=frame_rate)
        a_stream = ffmpeg.input(os.path.join(temp_folder, "audio_new.wav"))
        ffmpeg.output(v_stream, a_stream, output_file, strict="-2", loglevel="error").run() # TODO Make into 1 command?

def main():
    parser = argparse.ArgumentParser(description='Modify a video file to adjust playback speed based on volume.')
    parser.add_argument('input_file', type=str, help='Input video file to be modified.')
    parser.add_argument('--output_file', type=str, default="", help="Specify the output file name.")
    parser.add_argument('--loud_threshold', type=float, default=0.03, help="The volume level that frames' audio must surpass to be considered \loud\". It ranges from 0 (silence) to 1 (maximum volume).")
    parser.add_argument('--loud_speed', type=float, default=1.00, help="The playback speed for frames with audio above the threshold.")
    parser.add_argument('--quiet_speed', type=float, default=5.00, help="The playback speed for audio below the threshold.")
    parser.add_argument('--frame_rate', type=int, help="The frame rate of the input and output videos. If not provided, it will be found automatically, or default to 30 frames per second.")
    parser.add_argument('--verbose', action='store_true', help='Print more data')

    kwargs = vars(parser.parse_args())

    if not kwargs['output_file']:
        kwargs['output_file'] = input_to_output_filename(kwargs['input_file'])
    if not kwargs['frame_rate']:
        kwargs['frame_rate'] = get_frame_rate(kwargs['input_file'])

    process_video(**kwargs)

if __name__ == "__main__":
    main()
