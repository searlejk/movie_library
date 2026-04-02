from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ANIMAL_NAMES = [
    "Aardvark", "Albatross", "Alligator", "Alpaca", "Anaconda", "Antelope",
    "Baboon", "Badger", "Barracuda", "Bat", "Bear", "Beaver",
    "Bison", "Boar", "Buffalo", "Camel", "Capybara", "Caribou",
    "Cheetah", "Cobra", "Cougar", "Coyote", "Crocodile", "Crow",
    "Deer", "Dingo", "Dolphin", "Donkey", "Eagle", "Elephant",
    "Falcon", "Ferret", "Fox", "Frog", "Gazelle", "Giraffe",
    "Goat", "Gorilla", "Hamster", "Hawk", "Hippo", "Horse",
    "Hyena", "Iguana", "Jackal", "Jaguar", "Kangaroo", "Koala",
    "Lemur", "Leopard", "Liger", "Lion", "Lizard", "Llama",
    "Lynx", "Moose", "Narwhal", "Ocelot", "Otter", "Panda",
]

OUT_DIR = Path(__file__).resolve().parent / "movs"
WIDTH = 1280
HEIGHT = 720
FPS = 30
DURATION_SECONDS = 15
TOTAL_FRAMES = FPS * DURATION_SECONDS


def _build_frame(animal_name: str) -> np.ndarray:
    image = Image.new("RGB", (WIDTH, HEIGHT), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("Arial.ttf", 120)
    except OSError:
        font = ImageFont.load_default()

    text_box = draw.textbbox((0, 0), animal_name, font=font)
    text_w = text_box[2] - text_box[0]
    text_h = text_box[3] - text_box[1]
    x = (WIDTH - text_w) // 2
    y = (HEIGHT - text_h) // 2

    draw.text((x, y), animal_name, fill=(255, 255, 255), font=font)
    return np.asarray(image)


def generate_videos() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for animal in ANIMAL_NAMES:
        output_path = OUT_DIR / f"{animal}.mp4"
        frame = _build_frame(animal)

        writer = imageio.get_writer(
            output_path,
            fps=FPS,
            codec="libx264",
            pixelformat="yuv420p",
        )
        try:
            for _ in range(TOTAL_FRAMES):
                writer.append_data(frame)
        finally:
            writer.close()

        print(f"Created: {output_path}")


if __name__ == "__main__":
    generate_videos()
