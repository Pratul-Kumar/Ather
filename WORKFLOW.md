# Workflow

This document describes the end-to-end execution pipeline for building the Project Aether trailer.

### 1. Concept
The pipeline begins with establishing the visual tone and pacing required for the trailer. For Project Aether, the requirement is a 15-second moody, atmospheric sci-fi sequence.

### 2. Prompt Engineering
Specific text prompts are drafted to guide generative AI models. These prompts are designed to ensure consistent lighting, slow camera motion, and a muted color palette across different shots.

### 3. AI Video Generation
The prompts are fed into a generative video AI (such as Runway, Sora, or Pika) to produce source MP4 clips. These clips are typically longer than necessary (e.g., 10-15 seconds) to allow the assembly script room to choose the best moments.

### 4. Clip Selection (Automated)
The Python script analyzes each raw video clip. It scans the footage using a sliding window to calculate the standard deviation of luminance across frames. The 5-second segment with the highest visual variance is automatically extracted.

### 5. Python Assembly
The selected segments are formatted:
- Scaled and center-cropped to a uniform 1920x1080 resolution.
- Frame rates are normalized to 24 fps.
- A cinematic color grade (teal shadow shift and contrast boost) is applied to each frame.
- The clips are arranged sequentially with 0.5-second crossfades bridging them.

### 6. Kinetic Typography
Text layers for "PROJECT AETHER" and "THE SILENT WAVE" are generated frame-by-frame using PIL. This step bakes in custom letter spacing, an opacity fade, and a subtle scale reduction (zoom-out) effect over the final 3.5 seconds of the timeline.

### 7. Rendering
The final composition, combining the graded video sequence, the typography overlay, and the optional ambient audio track, is compiled into a single timeline. Global fade-in and fade-out effects are applied to the entire composition.

### 8. Final Output
The project is exported using ffmpeg (via MoviePy) to an H.264 / AAC MP4 file, strictly bound to a 15-second duration.
