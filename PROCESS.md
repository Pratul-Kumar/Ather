# Process

This document outlines the creative direction and technical decisions driving Project Aether.

## Creative Concept

Project Aether is designed to evoke a sense of quiet tension and high-concept science fiction. The goal was to build a cinematic trailer that feels atmospheric and eerie, focusing on visual storytelling rather than dialogue or fast-paced action. The pacing is deliberate, meant to build a slow sense of scale and mystery.

## Visual Direction

The visual style relies heavily on a muted, dark color palette. We chose deep slate (#1A1D20) as the underlying background tone to keep shadows rich without falling into absolute black. 

During the rendering pipeline, a specific cinematic color grade is applied programmatically to the raw video clips:
1. **Gamma Compression:** Lowers the midtones slightly to emphasize shadows.
2. **Contrast Boost:** Enhances the separation between light and dark areas.
3. **Teal Shift in Shadows:** We apply a pixel-level transformation to shift darker regions towards a cool teal hue while leaving highlights unaffected, a technique common in modern sci-fi grading.

## Prompt Engineering Decisions

To generate the underlying video assets, I tailored prompts for generative AI video tools to ensure the outputs naturally fit the pacing and lighting requirements.

The prompts specifically requested:
- Slow motion or slow camera movements (e.g., slow drone ascents, slow push-ins).
- Cinematic lighting keywords (e.g., volumetric lighting, anamorphic lens flares).
- Muted color palettes to give the grading script a good baseline to work from.

By keeping the prompts focused on scale and atmosphere rather than chaotic action, the resulting clips blend smoothly during the crossfade transitions.

## Typography Approach

The typography is intended to look premium and modern. I selected Montserrat for its clean, geometric sans-serif structure, which aligns well with sci-fi themes.

Instead of relying on standard video editor text overlays, the text is rendered frame-by-frame using Python's PIL library. This allows for precise control over letter spacing (tracking) and enables the subtle cinematic scale animation where the text slowly pulls back as it fades in. The title is rendered in an ice white (#F5F5F7) for stark contrast, while the subtitle uses a muted gold (#D4C5A9) to add a slight warmth without breaking the cool overall tone.

## Rendering Pipeline

The Python pipeline is built using MoviePy for sequence assembly and NumPy/PIL for frame manipulation. 

A core feature of the pipeline is the automated segment selection. Instead of hardcoding trim times, the script analyzes the luminance variance across every one-second window of the source clips. It selects the 5-second window with the highest variance, effectively finding the most visually dynamic portion of the clip automatically. This ensures the trailer is always built using the best available footage.
