from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageEnhance

ROOT = Path(__file__).parent
OUTPUT = ROOT / "videos" / "studio-tour.mp4"
SOURCES = [
    ROOT / "images" / "mens-wear" / "mens-wear-1.jpeg",
    ROOT / "images" / "womens-wear" / "womens-wear-1.jpeg",
    ROOT / "images" / "kids-wear" / "kids-wear-1.jpg",
    ROOT / "images" / "accessories" / "accessories-1.jpg",
    ROOT / "images" / "costume-competitions" / "costume-competitions-1.jpg",
    ROOT / "images" / "functions" / "functions-1.jpeg",
]
WIDTH, HEIGHT = 1280, 720
FPS = 30
SECONDS_PER_IMAGE = 10
CROSSFADE_SECONDS = 1


def prepare_image(path):
    image = Image.open(path).convert("RGB")
    source_ratio = image.width / image.height
    target_ratio = WIDTH / HEIGHT
    if source_ratio > target_ratio:
        crop_width = int(image.height * target_ratio)
        left = (image.width - crop_width) // 2
        image = image.crop((left, 0, left + crop_width, image.height))
    else:
        crop_height = int(image.width / target_ratio)
        top = (image.height - crop_height) // 2
        image = image.crop((0, top, image.width, top + crop_height))
    image = image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    return ImageEnhance.Color(image).enhance(1.08)


OUTPUT.parent.mkdir(exist_ok=True)
images = [prepare_image(path) for path in SOURCES]
writer = imageio.get_writer(
    OUTPUT,
    format="FFMPEG",
    mode="I",
    fps=FPS,
    codec="libx264",
    quality=7,
    pixelformat="yuv420p",
    macro_block_size=1,
)

try:
    frames_per_image = SECONDS_PER_IMAGE * FPS
    fade_frames = CROSSFADE_SECONDS * FPS
    for index, image in enumerate(images):
        next_image = images[(index + 1) % len(images)]
        start = np.asarray(image, dtype=np.uint8)
        end = np.asarray(next_image, dtype=np.uint8)
        for frame_number in range(frames_per_image):
            if index < len(images) - 1 and frame_number >= frames_per_image - fade_frames:
                amount = (frame_number - (frames_per_image - fade_frames) + 1) / fade_frames
                frame = (start * (1 - amount) + end * amount).astype(np.uint8)
            else:
                frame = start
            writer.append_data(frame)
finally:
    writer.close()

print(f"Created {OUTPUT} ({OUTPUT.stat().st_size // 1024} KB)")
