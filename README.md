# VideoCondenser
VideoCondenser is a tool that allows you to adjust the playback speed of a video based on the volume of its audio. 
The intended usage is to speed up long lecture-type videos while retaining clarity and content.

## Features

- Dynamically adjust video playback speed based on audio volume levels.
- Simple command-line interface for easy usage.

## Installation

Arch LinuxPackage
```
pacman -Syy videocondenser-git
```

macOS packages and Windows distribution coming soon.

To run AudioSpeeder manually:

1. Clone this repository to your local machine.
2. Install the required dependencies (Python and assorted packages, Ffmpeg).
3. Run the script using the provided command-line arguments.

## Usage
Standard Lecture Shortening
```bash
python videocondenser.py input_video.mp4
```
Double talking speed 
```bash
python videocondenser.py input_video.mp4 --loud_speed 2
```

Completely cutting during silence
```bash
python videocondenser.py input_video.mp4 --quiet_speed 10000
```

Slow down content while speeding up breaks (I personally found this setting makes thie output video about the same length as the input)
```bash
python videocondenser.py input_video.mp4 --quiet_speed 4 --loud_speed 0.75
```
and many more!

## Showcase Videos
Before:

https://github.com/frank-monkey/videocondenser/assets/86938002/1cd11268-52c1-4689-ae9f-d117a797cdfd

After:

https://github.com/frank-monkey/videocondenser/assets/86938002/314ff9a4-80e9-4e06-b895-2b3364814d1a

(Original video [here](https://youtu.be/jANZxzetPaQ) Courtesy of MIT OCW)


## License

This project is licensed under the [GNU General Public License (GPL-3.0)](LICENSE.txt).
