from __future__ import annotations

import os
import sys
import glob
import urllib.request
import zipfile
import shutil
import numpy as np
from pathlib import Path

# Force UTF-8 output for terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from moviepy import (
    VideoFileClip,
    VideoClip,
    ImageClip,
    CompositeVideoClip,
    CompositeAudioClip,
    AudioFileClip,
    concatenate_videoclips,
)
from moviepy.video.fx import (
    CrossFadeIn,
    CrossFadeOut,
    FadeIn,
    FadeOut,
    GammaCorrection,
    LumContrast,
)
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut, AudioLoop

from PIL import Image, ImageDraw, ImageFont


# Configuration
OUTPUT_WIDTH = 1920
OUTPUT_HEIGHT = 1080
TARGET_FPS = 24
TARGET_DURATION = 15.0
CLIP_DURATION = 5.0
TRANSITION_DURATION = 0.5

# Brand palette
BG_COLOR = (26, 29, 32)
ACCENT_COLOR = (212, 197, 169)
HIGHLIGHT_COLOR = (245, 245, 247)

# Typography settings
TITLE_SIZE = 96
SUBTITLE_SIZE = 38
TITLE_SPACING = 14
SUBTITLE_SPACING = 8

# Directories
CLIPS_DIR = Path("clips")
AUDIO_DIR = Path("audio")
FONTS_DIR = Path("fonts")
OUTPUT_DIR = Path("output")

EXPECTED_CLIPS = ["shot1.mp4", "shot2.mp4", "shot3.mp4"]
MONTSERRAT_ZIP_URL = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"


def find_font(patterns: list[str]) -> str | None:
    """Locate a font file by matching name patterns in common directories."""
    search_directories = [FONTS_DIR, Path(r"C:\Windows\Fonts")]
    for pattern in patterns:
        for directory in search_directories:
            if not directory.exists():
                continue
            matches = list(directory.glob(f"*{pattern}*"))
            if matches:
                return str(matches[0])
    return None


def download_fonts() -> None:
    """Download required fonts if they are not available locally."""
    FONTS_DIR.mkdir(exist_ok=True)
    
    font_files = {
        "Montserrat-Bold.ttf": "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf",
        "Montserrat-Regular.ttf": "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Regular.ttf",
    }
    
    download_success = False
    for filename, url in font_files.items():
        destination = FONTS_DIR / filename
        print(f"[Setup] Downloading {filename}...")
        try:
            urllib.request.urlretrieve(url, destination)
            if destination.stat().st_size > 10000:
                download_success = True
            else:
                destination.unlink(missing_ok=True)
        except Exception as e:
            print(f"[Setup] Failed to download {filename}: {e}")
            
    if not download_success:
        raise RuntimeError("Failed to retrieve required fonts.")


def resolve_fonts() -> tuple[str, str]:
    """Ensure typography dependencies are met, returning paths for title and subtitle fonts."""
    bold_font = find_font(["Montserrat-Bold", "MontserratBold", "montserrat_bold"])
    regular_font = find_font(["Montserrat-Regular", "Montserrat-Light", "MontserratRegular"])

    if not bold_font or not regular_font:
        print("[Setup] Brand fonts not found locally. Attempting to download...")
        try:
            download_fonts()
            bold_font = find_font(["Montserrat-Bold", "MontserratBold"])
            regular_font = find_font(["Montserrat-Regular", "Montserrat-Light"])
        except Exception as e:
            print(f"[Setup] Using system fallback fonts due to download error: {e}")

    if not bold_font:
        bold_font = find_font(["calibrib", "arialbd", "segoeuib"])
    if not regular_font:
        regular_font = find_font(["calibri", "arial", "segoeui"])

    if not bold_font or not regular_font:
        raise RuntimeError("No usable fonts found. Please install Montserrat manually in the fonts directory.")

    return bold_font, regular_font


def locate_media() -> tuple[list[Path], Path | None]:
    """Find input video clips and optional ambient audio track."""
    video_paths = []
    for name in EXPECTED_CLIPS:
        for search_dir in [CLIPS_DIR, Path(".")]:
            file_path = search_dir / name
            if file_path.exists():
                video_paths.append(file_path)
                break

    if len(video_paths) != 3:
        missing = [name for name in EXPECTED_CLIPS if not any(name in str(p) for p in video_paths)]
        raise FileNotFoundError(f"Missing required input clips: {', '.join(missing)}")

    audio_path = None
    for pattern in ["*.mp3", "*.wav", "*.ogg", "*.aac", "*.m4a"]:
        matches = list(AUDIO_DIR.glob(pattern))
        if matches:
            audio_path = matches[0]
            print(f"[Media] Found ambient audio track: {audio_path.name}")
            break

    if not audio_path:
        print("[Media] No ambient audio found. Proceeding with video only.")

    return video_paths, audio_path


def apply_color_grade(clip: VideoFileClip) -> VideoFileClip:
    """Enhance the clip with a cinematic teal and orange-inspired color grade."""
    clip = clip.with_effects([
        GammaCorrection(gamma=0.92),
        LumContrast(lum=0, contrast=8, contrast_threshold=127),
    ])

    def color_transform(frame: np.ndarray) -> np.ndarray:
        current_frame = frame.astype(np.float32)
        luma = 0.299 * current_frame[..., 0] + 0.587 * current_frame[..., 1] + 0.114 * current_frame[..., 2]
        
        # Isolate shadows for styling
        shadow_mask = np.clip(1.0 - luma / 110.0, 0.0, 1.0)[..., np.newaxis]
        teal_shift = np.array([-6.0, +4.0, +10.0], dtype=np.float32)
        
        current_frame += shadow_mask * teal_shift
        return np.clip(current_frame, 0, 255).astype(np.uint8)

    return clip.image_transform(color_transform)


def format_clip(clip: VideoFileClip) -> VideoFileClip:
    """Resize the clip to fill the target frame while preserving aspect ratio."""
    src_width, src_height = clip.size
    scale_factor = max(OUTPUT_WIDTH / src_width, OUTPUT_HEIGHT / src_height)
    
    new_width = int(src_width * scale_factor)
    new_height = int(src_height * scale_factor)
    
    clip = clip.resized((new_width, new_height))
    
    x_offset = (new_width - OUTPUT_WIDTH) // 2
    y_offset = (new_height - OUTPUT_HEIGHT) // 2
    
    return clip.cropped(x1=x_offset, y1=y_offset, x2=x_offset + OUTPUT_WIDTH, y2=y_offset + OUTPUT_HEIGHT)


def select_best_segment(clip: VideoFileClip, duration: float = CLIP_DURATION) -> float:
    """Analyze the clip to find the most visually dynamic segment using luminance variance."""
    max_start_time = max(0.0, clip.duration - duration)
    if max_start_time <= 0:
        return 0.0

    best_start = 0.0
    highest_variance = -1.0
    
    current_time = 0.0
    while current_time <= max_start_time:
        sample_times = np.linspace(current_time, current_time + duration - 0.1, 5)
        variances = []
        
        for time_point in sample_times:
            try:
                frame = clip.get_frame(time_point)
                luma = 0.299 * frame[..., 0] + 0.587 * frame[..., 1] + 0.114 * frame[..., 2]
                variances.append(float(np.std(luma)))
            except Exception:
                continue
                
        if variances:
            avg_variance = float(np.mean(variances))
            if avg_variance > highest_variance:
                highest_variance = avg_variance
                best_start = current_time
                
        current_time += 1.0

    return best_start


def render_spaced_text(
    text: str,
    font_path: str,
    font_size: int,
    color: tuple[int, int, int],
    spacing: int,
) -> np.ndarray:
    """Generate a text image with precise letter spacing over a transparent background."""
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()

    probe_image = Image.new("RGBA", (1, 1))
    probe_draw = ImageDraw.Draw(probe_image)
    
    char_widths = []
    for char in text:
        bbox = probe_draw.textbbox((0, 0), char, font=font)
        char_widths.append(bbox[2] - bbox[0])

    total_width = sum(char_widths) + spacing * (len(text) - 1)
    bbox_full = probe_draw.textbbox((0, 0), text, font=font)
    text_height = bbox_full[3] - bbox_full[1]
    y_offset = bbox_full[1]

    canvas = Image.new("RGBA", (OUTPUT_WIDTH, OUTPUT_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    current_x = (OUTPUT_WIDTH - total_width) // 2
    current_y = (OUTPUT_HEIGHT - text_height) // 2 - y_offset // 2

    for index, char in enumerate(text):
        draw.text((current_x, current_y), char, font=font, fill=(*color, 255))
        current_x += char_widths[index] + spacing

    return np.array(canvas)


def scale_frame(frame: np.ndarray, scale: float) -> np.ndarray:
    """Apply a high-quality resize to a single frame for subtle animation effects."""
    if abs(scale - 1.0) < 0.001:
        return frame
        
    height, width = frame.shape[:2]
    new_width, new_height = int(width * scale), int(height * scale)
    
    image = Image.fromarray(frame, "RGBA")
    image = image.resize((new_width, new_height), Image.LANCZOS)
    
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    canvas.paste(image, ((width - new_width) // 2, (height - new_height) // 2))
    
    return np.array(canvas)


def create_kinetic_text(
    text: str,
    font_path: str,
    font_size: int,
    color: tuple[int, int, int],
    letter_spacing: int,
    duration: float,
    fade_in: float,
    fade_out: float,
    position: str | tuple = "center",
    start_time: float = 0.0,
) -> VideoClip:
    """Create a typography overlay layer featuring fade transitions and scale animations."""
    base_frame = render_spaced_text(text, font_path, font_size, color, letter_spacing)

    def calculate_opacity_and_scale(time_point: float) -> tuple[float, float]:
        if time_point < fade_in:
            opacity = time_point / fade_in
            scale = 1.06 - 0.06 * min(time_point / fade_in, 1.0) if fade_in > 0 else 1.0
        elif time_point > duration - fade_out:
            opacity = (duration - time_point) / fade_out
            scale = 1.0
        else:
            opacity = 1.0
            scale = 1.0
            
        return float(np.clip(opacity, 0.0, 1.0)), scale

    def render_rgb(time_point: float) -> np.ndarray:
        opacity, scale = calculate_opacity_and_scale(time_point)
        scaled_frame = scale_frame(base_frame.copy(), scale)
        
        rgb = scaled_frame[..., :3].astype(np.float32)
        alpha = scaled_frame[..., 3:4].astype(np.float32) / 255.0 * opacity
        
        return np.clip(rgb * alpha, 0, 255).astype(np.uint8)

    def render_mask(time_point: float) -> np.ndarray:
        opacity, scale = calculate_opacity_and_scale(time_point)
        scaled_frame = scale_frame(base_frame.copy(), scale)
        return (scaled_frame[..., 3].astype(np.float32) / 255.0 * opacity).astype(np.float32)

    rgb_layer = VideoClip(frame_function=render_rgb, duration=duration).with_fps(TARGET_FPS)
    mask_layer = VideoClip(frame_function=render_mask, is_mask=True, duration=duration).with_fps(TARGET_FPS)

    return rgb_layer.with_mask(mask_layer).with_start(start_time).with_position(position)


def assemble_project(video_files: list[Path], title_font: str, subtitle_font: str, audio_file: Path | None) -> None:
    """Coordinate the processing and rendering pipeline for the cinematic trailer."""
    
    print("[Pipeline] Preparing source clips...")
    processed_clips = []

    for index, filepath in enumerate(video_files):
        print(f"[Video] Processing clip {index + 1}/3: {filepath.name}")
        raw_video = VideoFileClip(str(filepath))
        
        start_marker = select_best_segment(raw_video)
        processed_video = raw_video.subclipped(start_marker, start_marker + CLIP_DURATION)
        
        processed_video = format_clip(processed_video)
        processed_video = processed_video.with_fps(TARGET_FPS)
        processed_video = apply_color_grade(processed_video)
        
        processed_clips.append(processed_video)

    print("[Pipeline] Arranging timeline and transitions...")
    processed_clips[0] = processed_clips[0].with_effects([CrossFadeOut(TRANSITION_DURATION)])
    processed_clips[1] = processed_clips[1].with_effects([CrossFadeIn(TRANSITION_DURATION), CrossFadeOut(TRANSITION_DURATION)])
    processed_clips[2] = processed_clips[2].with_effects([CrossFadeIn(TRANSITION_DURATION)])

    timeline = concatenate_videoclips(
        processed_clips,
        method="compose",
        padding=-TRANSITION_DURATION,
        bg_color=list(BG_COLOR),
    )
    
    # Ensure we don't request a duration longer than what we generated
    final_duration = min(TARGET_DURATION, timeline.duration)
    timeline = timeline.subclipped(0, final_duration).with_fps(TARGET_FPS)
    timeline = timeline.with_effects([FadeIn(0.6), FadeOut(1.2)])

    print("[Pipeline] Rendering typography...")
    
    # Plan text overlays to appear during the final 3.5 seconds
    text_end_time = final_duration
    text_start_time = max(0.0, final_duration - 3.5)
    text_display_duration = text_end_time - text_start_time

    title_overlay = create_kinetic_text(
        text="PROJECT AETHER",
        font_path=title_font,
        font_size=TITLE_SIZE,
        color=HIGHLIGHT_COLOR,
        letter_spacing=TITLE_SPACING,
        duration=text_display_duration,
        fade_in=1.0,
        fade_out=1.2,
        position="center",
        start_time=text_start_time,
    )

    subtitle_vertical_pos = int(OUTPUT_HEIGHT * 0.57)
    subtitle_overlay = create_kinetic_text(
        text="THE SILENT WAVE",
        font_path=subtitle_font,
        font_size=SUBTITLE_SIZE,
        color=ACCENT_COLOR,
        letter_spacing=SUBTITLE_SPACING,
        duration=max(0.5, text_display_duration - 0.3),
        fade_in=1.0,
        fade_out=1.2,
        position=("center", subtitle_vertical_pos),
        start_time=text_start_time + 0.3,
    )

    print("[Pipeline] Compositing final video sequence...")
    final_composition = CompositeVideoClip(
        [timeline, title_overlay, subtitle_overlay],
        size=(OUTPUT_WIDTH, OUTPUT_HEIGHT),
    ).subclipped(0, final_duration).with_fps(TARGET_FPS)

    if audio_file:
        ambient_track = AudioFileClip(str(audio_file))
        if ambient_track.duration < final_duration:
            required_loops = int(np.ceil(final_duration / ambient_track.duration))
            ambient_track = ambient_track.with_effects([AudioLoop(n_loops=required_loops)])
            
        ambient_track = ambient_track.subclipped(0, final_duration)
        ambient_track = ambient_track.with_effects([AudioFadeIn(1.0), AudioFadeOut(2.0)])

        if final_composition.audio is not None:
            original_audio = final_composition.audio.with_effects([AudioFadeIn(1.0), AudioFadeOut(2.0)])
            final_composition = final_composition.with_audio(
                CompositeAudioClip([original_audio, ambient_track.with_volume_scaled(0.35)])
            )
        else:
            final_composition = final_composition.with_audio(ambient_track)

    OUTPUT_DIR.mkdir(exist_ok=True)
    export_path = OUTPUT_DIR / "project_aether.mp4"

    print(f"[Export] Writing output to {export_path}...")
    final_composition.write_videofile(
        str(export_path),
        fps=TARGET_FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="8000k",
        audio_bitrate="192k",
        preset="slow",
        ffmpeg_params=[
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-profile:v", "high",
            "-level", "4.1",
        ],
        logger="bar",
    )

    print(f"\n[Success] Rendering complete. Output saved to {export_path.absolute()}")


def main() -> None:
    print("Starting Project Aether rendering pipeline...")
    
    try:
        title_font, subtitle_font = resolve_fonts()
        video_files, audio_file = locate_media()
        assemble_project(video_files, title_font, subtitle_font, audio_file)
    except Exception as error:
        print(f"[Error] Pipeline failed to start: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
