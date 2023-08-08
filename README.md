# VideoCondenser
VideoCondenser is a tool that allows you to adjust the playback speed of a video based on the volume of its audio. 
The intended usage is to speed up long lecture-type videos while retaining clarity and content.

## Features

- Dynamically adjust video playback speed based on audio volume levels.
- Simple command-line interface for easy usage.

## Installation

Linux packages, macOS packages and Windows distribution coming soon.

To use AudioSpeeder, follow these steps:

1. Clone this repository to your local machine.
2. Install the required dependencies (Python, FFmpeg, etc.).
3. Run the script using the provided command-line arguments.

## Usage
Standard Lecture Shortening
```bash
python videocondenser.py input_video.mp4
```

Completely cutting during silence
```bash
python videocondenser.py input_video.mp4 --loud_speed 10000
```

Slow down content while speeding up breaks
```bash
python videocondenser.py input_video.mp4 --quiet_speed 0.75
```
and many more!