# Project Aether

A cinematic trailer rendering pipeline built with Python and MoviePy.

## Overview

Project Aether processes raw video clips to automatically generate a polished, cinematic trailer. The script analyzes the input clips for visual dynamism, isolates the best segments, normalizes resolutions, applies a cinematic teal-and-orange color grade, and pieces them together using crossfade transitions. It finishes with an animated typographic overlay.

## Folder Structure

```
project-aether/
│
├── main.py               # Main render script
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation
├── PROCESS.md            # Details on the creative process and concept
├── WORKFLOW.md           # Pipeline execution flow
├── PROMPTS.md            # AI generation prompts
├── clips/                # Place input video clips here
├── fonts/                # Fonts are downloaded here automatically
├── audio/                # Optional directory for ambient audio track
└── output/               # Rendered output saves here
```

## Installation

Ensure you have Python 3.10+ installed along with `ffmpeg` configured in your system PATH.

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Project

1. Add your three source MP4 video files into the `clips/` directory. They should be named:
   - `shot1.mp4`
   - `shot2.mp4`
   - `shot3.mp4`

2. Run the main script:
   ```bash
   python main.py
   ```

## Output

The final rendered video will be placed in the `output/` directory as `project_aether.mp4`.

Output specification:
- **Resolution:** 1920x1080
- **Frame Rate:** 24 fps
- **Duration:** 15 seconds
- **Format:** H.264 / AAC (MP4)

## Notes

- **Fonts:** The script automatically attempts to download the Montserrat font family required for the typographic overlay. If the download fails, it will attempt to use standard system fonts as a fallback.
- **Audio:** You can place an ambient audio track (e.g., `.mp3`, `.wav`) inside the `audio/` directory. The script will automatically loop or trim the track to fit the 15-second duration and mix it with the trailer.
