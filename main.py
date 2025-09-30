import base64
import io
import os
import random
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# openai images
try:
    from openai import OpenAI
except Exception:
    raise SystemExit("Install the sdk first: pip install openai")

openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    client = OpenAI(api_key=openai_api_key)

openai_model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
openai_size = os.getenv("OPENAI_IMAGE_SIZE", "1024x1792")

# docs: https://platform.openai.com/docs/guides/image-generation?image-generation-model=dall-e-3#generate-images

# layout and style
CARD_W, CARD_H = 825, 1275
RADIUS = 64
MARGIN = 28
ELLIPSE_MARGIN = 8
WHITE = (255, 255, 255)
COLOR_RED = (228, 39, 43)
COLOR_YEL = (253, 187, 48)
COLOR_GRN = (83, 175, 80)
COLOR_BLU = (0, 116, 188)
COLOR_BLK = (20, 20, 20)

# font paths
TEXT_FONT_PATH = "extras/fonts/Cabin-Bold.ttf"
SYMBOL_FONT_PATH = "extras/fonts/OpenSans.ttf"

# symbol to image mapping
SYMBOL_IMAGES = {
    "skip": "extras/images/symbol-skip.png",
    "reverse": "extras/images/symbol-reverse.png",
    "wild": "extras/images/symbol-star.png",
    "draw2": "extras/images/symbol-plus2.png",
    "wild_draw4": "extras/images/symbol-plus4.png",
}

# output directory and pdf path
OUTPUT_DIR = os.getenv("UNO_OUTPUT_DIR", "uno-cards-out")
PDF_PATH = os.path.join(OUTPUT_DIR, "uno-cards.pdf")

# load fonts
FONT_BIG = ImageFont.truetype(TEXT_FONT_PATH, 200)

# test mode
test_mode = os.getenv("UNO_TEST_MODE", "false").lower() == "true"
test_background_path = "extras/images/test-bg.png"

# generation control
generate_first_only = os.getenv("UNO_GENERATE_FIRST_ONLY", "false").lower() == "true"

# rendering quality
upscale_factor = int(os.getenv("UNO_UPSCALE_FACTOR", "3"))

# ellipse rotation
ellipse_rotation = float(os.getenv("UNO_ELLIPSE_ROTATION", "30"))

# border color
border_color = os.getenv("UNO_BORDER_COLOR", "#000000")


# deck specification
@dataclass
class Card:
    color: str
    kind: str
    value: Optional[int] = None
    copy_index: int = 1


def build_uno_deck() -> List[Card]:
    deck: List[Card] = []
    colors = ["red", "yellow", "green", "blue"]

    # zero: one per color
    for c in colors:
        deck.append(Card(color=c, kind="number", value=0, copy_index=1))

    # one to nine: two per color
    for c in colors:
        for n in range(1, 10):
            deck.append(Card(color=c, kind="number", value=n, copy_index=1))
            deck.append(Card(color=c, kind="number", value=n, copy_index=2))

    # action cards: two of each per color
    for c in colors:
        for i in (1, 2):
            deck.append(Card(color=c, kind="skip", copy_index=i))
            deck.append(Card(color=c, kind="reverse", copy_index=i))
            deck.append(Card(color=c, kind="draw2", copy_index=i))

    # wild cards: four each
    for i in range(1, 5):
        deck.append(Card(color="wild", kind="wild", copy_index=i))
        deck.append(Card(color="wild", kind="wild_draw4", copy_index=i))

    assert len(deck) == 108
    return deck


# themes by color
COLOR_THEME = {
    "red": (
        "Stories of Jesus",
        [
            "Jesus welcoming children in a sunny park",
            "Sermon on the Mount with smiling crowd",
            "Calming the storm gently while disciples watch",
            "Feeding the five thousand with bread and fish",
            "Walking on water in a peaceful sea scene",
            "Healing a child with kind smile, indoors",
            "Nativity with baby in manger and friendly animals",
            "Good Shepherd carrying a lamb on green hills",
            "Calling the disciples by the seaside",
            "Triumphal entry with children waving branches",
        ],
    ),
    "yellow": (
        "Old Testament heroes",
        [
            "Moses parting the Red Sea, joyful style",
            "David with sling facing Goliath playfully",
            "Noah with animals near a bright rainbow",
            "Abraham looking at stars with Isaac",
            "Joseph with colorful coat smiling",
            "Jonah near a big friendly fish",
            "Daniel in the lions’ den with cuddly lions",
            "Queen Esther brave before the king",
            "Ruth gathering wheat joyfully",
            "Young Samuel listening to God at night",
        ],
    ),
    "green": (
        "Parables of Jesus",
        [
            "Good Samaritan helping traveler on the road",
            "Wise and foolish builders, sun vs. rain",
            "Lost sheep found by smiling shepherd",
            "Mustard seed growing into a tree with birds",
            "Prodigal son hugged by his father happily",
            "Ten bridesmaids with glowing lamps",
            "Hidden treasure found in a field",
            "Pearl of great price in hands",
            "Sower scattering seeds with sprouts",
            "Vine and branches full of fruit",
        ],
    ),
    "blue": (
        "Miracles & key moments",
        [
            "Multiplication of loaves picnic scene",
            "Healing of a blind man with happy crowd",
            "Raising Jairus’s daughter gently",
            "Cleansing of a leper with gratitude",
            "Paralytic lowered through roof playfully",
            "Water turned into wine at Cana",
            "Miraculous catch of fish with nets",
            "Mary and Martha welcoming Jesus",
            "Zacchaeus waving from a tree branch",
            "Peter rescued from sinking, gentle help",
        ],
    ),
    "wild": (
        "Great moments of the Bible",
        [
            "Creation with sun, moon and smiling animals",
            "Empty tomb at sunrise, hopeful scene",
            "Pentecost with friendly flames above people",
            "Shining New Jerusalem with the river of life",
            "Ark of the Covenant stylized and bright",
            "Burning bush with warm glow",
            "Jacob’s ladder with playful angels",
            "Baptism in the Jordan, peaceful waters",
        ],
    ),
}


def concept_for_card(card: Card) -> str:
    if card.color == "wild":
        return random.choice(COLOR_THEME["wild"][1])

    theme_items = COLOR_THEME[card.color][1]

    if card.kind == "number" and card.value is not None:
        return theme_items[card.value % len(theme_items)]

    return theme_items[card.copy_index % len(theme_items)]


def prompt_for_card(card: Card) -> str:
    base_style = (
        "cute bible illustration, cartoon style for children, soft shading, "
        "bright colors, clean outlines, wholesome, friendly faces, high quality, "
        "no text overlay, simple background"
    )
    color_hint = {
        "red": "primary accent red tones",
        "yellow": "primary accent yellow tones",
        "green": "primary accent green tones",
        "blue": "primary accent blue tones",
        "wild": "balanced rainbow accents",
    }[card.color]

    return f"{concept_for_card(card)}, {base_style}, {color_hint}"


# openai image generation
def gen_image_from_openai(prompt: str, size: str = "1024x1024") -> Image.Image:
    result = client.images.generate(model="gpt-image-1", prompt=prompt, size=size)

    # response comes in base64
    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    return Image.open(io.BytesIO(image_bytes)).convert("RGBA")


# drawing helpers
def rounded_rect(
    draw: ImageDraw.ImageDraw,
    box: Tuple[int, int, int, int],
    radius: int,
    fill: Tuple[int, int, int],
):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def color_rgb(name: str) -> Tuple[int, int, int]:
    return {
        "red": COLOR_RED,
        "yellow": COLOR_YEL,
        "green": COLOR_GRN,
        "blue": COLOR_BLU,
        "wild": COLOR_BLK,
    }[name]


def parse_border_color(color_str: str) -> Tuple[int, int, int]:
    try:
        color_str = color_str.strip()

        if color_str.startswith("#"):
            # hex format
            hex_color = color_str[1:]
            if len(hex_color) == 3:
                # expand rgb to rrggbb
                hex_color = "".join(c * 2 for c in hex_color)
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        else:
            # rgb format
            r, g, b = map(int, color_str.split(","))
            return (r, g, b)
    except:
        return (0, 0, 0)


def symbol_for(card: Card) -> str:
    if card.kind == "number":
        return str(card.value)

    return "?"


def get_symbol_image_path(card: Card) -> Optional[str]:
    if card.kind in SYMBOL_IMAGES and os.path.exists(SYMBOL_IMAGES[card.kind]):
        return SYMBOL_IMAGES[card.kind]

    return None


def draw_card_base(bg_rgb: Tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # outer border with configurable color
    border_rgb = parse_border_color(border_color)
    rounded_rect(d, (0, 0, CARD_W - 1, CARD_H - 1), RADIUS + 8, border_rgb)

    # inner color face
    rounded_rect(d, (8, 8, CARD_W - 9, CARD_H - 9), RADIUS, bg_rgb)

    return img


def paste_into_ellipse(card_img: Image.Image, art: Image.Image) -> Image.Image:
    x0, y0 = ELLIPSE_MARGIN, ELLIPSE_MARGIN
    x1, y1 = CARD_W - ELLIPSE_MARGIN, CARD_H - ELLIPSE_MARGIN
    W, H = x1 - x0, y1 - y0

    # scale background image to full card width for better coverage
    art_aspect = art.width / art.height
    new_w = CARD_W
    new_h = int(CARD_W / art_aspect)
    art_resized = art.resize((new_w, new_h), Image.LANCZOS)

    # crop the ellipse area from the center
    left = (new_w - W) // 2
    top = (new_h - H) // 2
    crop = art_resized.crop((left, top, left + W, top + H))

    # create mask for ellipse
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((0, 0, W, H), fill=255)

    if abs(ellipse_rotation) > 0.1:
        # rotate only the mask, keep the background image straight
        mask = mask.rotate(-ellipse_rotation, expand=False, center=(W // 2, H // 2))

    card_img.paste(crop, (x0, y0), mask)

    return card_img


def draw_corners(card_img: Image.Image, card: Card):
    # use symbol image
    symbol_img_path = get_symbol_image_path(card)

    if symbol_img_path:
        # load and paste symbol image
        symbol_img = Image.open(symbol_img_path).convert("RGBA")
        # resize to fit in corner
        symbol_img = symbol_img.resize((120, 120), Image.LANCZOS)

        # top left
        card_img.alpha_composite(symbol_img, (MARGIN, MARGIN))

        # bottom right rotated
        rotated_symbol = symbol_img.rotate(180, expand=True)
        card_img.alpha_composite(
            rotated_symbol,
            (
                CARD_W - MARGIN - rotated_symbol.width,
                CARD_H - MARGIN - rotated_symbol.height,
            ),
        )
    else:
        # for numbers, draw text
        d = ImageDraw.Draw(card_img)
        s = symbol_for(card)
        d.text((MARGIN, MARGIN), s, font=FONT_BIG, fill=WHITE)

        # bottom right rotated
        tmp = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        td.text((0, 0), s, font=FONT_BIG, fill=WHITE)
        tmp = tmp.rotate(180, expand=True)
        card_img.alpha_composite(
            tmp, (CARD_W - MARGIN - tmp.width, CARD_H - MARGIN - tmp.height)
        )


def filename_for(card: Card) -> str:
    base = f"{card.color}_{card.kind}"

    if card.kind == "number":
        base += f"_{card.value}"

    base += f"-x{card.copy_index}"
    return base + ".png"


def render_card(card: Card, art: Image.Image) -> Image.Image:
    base = draw_card_base(color_rgb(card.color))
    base = paste_into_ellipse(base, art)
    draw_corners(base, card)

    # apply upscale for better quality when downscaling in pdf
    if upscale_factor > 1:
        final_w = int(CARD_W * upscale_factor)
        final_h = int(CARD_H * upscale_factor)
        base = base.resize((final_w, final_h), Image.LANCZOS)

    return base


# build and export
def load_test_background() -> Image.Image:
    if not os.path.exists(test_background_path):
        raise FileNotFoundError(
            f"Test background image not found: {test_background_path}"
        )

    return Image.open(test_background_path).convert("RGBA")


def ensure_dir(path: str):
    """ensure directory exists"""
    os.makedirs(path, exist_ok=True)


def generate_all_cards() -> List[str]:
    ensure_dir(OUTPUT_DIR)
    deck = build_uno_deck()
    saved: List[str] = []

    # load test background once if in test mode
    test_bg = load_test_background() if test_mode else None

    for i, card in enumerate(deck, 1):
        if test_mode:
            print(
                f"[{i:03d}/108] test mode: {card.color} {card.kind} {card.value if card.value is not None else ''} -> using test background"
            )
            art = test_bg
        else:
            prompt = prompt_for_card(card)
            print(
                f"[{i:03d}/108] {card.color} {card.kind} {card.value if card.value is not None else ''} -> {prompt}"
            )
            art = gen_image_from_openai(prompt)

        card_img = render_card(card, art)
        out_path = os.path.join(OUTPUT_DIR, filename_for(card))
        card_img.save(out_path, "PNG")
        saved.append(out_path)

        # gentle pacing to avoid rate limiting
        if not test_mode:
            time.sleep(0.6)

        # stop after first card if generate_first_only is enabled
        if generate_first_only:
            print(f"stopping after first card (generate_first_only=true)")
            break

    return saved


def images_to_pdf(image_paths: List[str], pdf_path: str):
    c = canvas.Canvas(pdf_path, pagesize=A4)
    pw, ph = A4

    # layout: exactly 3x3 cards per page
    cards_per_row = 3
    cards_per_column = 3
    cards_per_page = cards_per_row * cards_per_column

    # minimal margins
    margin = pw * 0.02  # 2 percent margin
    spacing = pw * 0.015  # 1.5 percent spacing between cards

    # calculate card dimensions to fit exactly 3x3
    available_width = pw - (2 * margin) - (2 * spacing)
    available_height = ph - (2 * margin) - (2 * spacing)

    card_width = available_width / cards_per_row
    card_height = available_height / cards_per_column

    # ensure aspect ratio is maintained
    target_aspect = 825 / 1275
    current_aspect = card_width / card_height

    if current_aspect > target_aspect:
        # too wide, adjust width
        card_width = card_height * target_aspect
    else:
        # too tall, adjust height
        card_height = card_width / target_aspect

    # recalculate spacing to center the cards
    total_width = cards_per_row * card_width
    total_height = cards_per_column * card_height
    spacing_horizontal = (pw - total_width) / (cards_per_row + 1)
    spacing_vertical = (ph - total_height) / (cards_per_column + 1)

    for i, p in enumerate(image_paths):
        with Image.open(p) as im:
            # calculate position on current page
            card_index_in_page = i % cards_per_page
            row = card_index_in_page // cards_per_row
            col = card_index_in_page % cards_per_row

            # calculate coordinates with equal spacing
            x = (col + 1) * spacing_horizontal + col * card_width
            y = ph - ((row + 1) * spacing_vertical + (row + 1) * card_height)

            # the image is already upscaled, so we draw it at the calculated size
            c.drawImage(
                ImageReader(im),
                x,
                y,
                width=card_width,
                height=card_height,
                preserveAspectRatio=True,
                mask="auto",
            )

            # start new page when page is full
            if (i + 1) % cards_per_page == 0 and i + 1 < len(image_paths):
                c.showPage()

    c.save()


def main():
    paths = generate_all_cards()
    print(f"Generated {len(paths)} card images at: {OUTPUT_DIR}")
    print(f"Building PDF: {PDF_PATH}")
    images_to_pdf(paths, PDF_PATH)
    print("Done!")


if __name__ == "__main__":
    main()
