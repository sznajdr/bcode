import streamlit as st
import pandas as pd
import json
import requests
import textwrap
import os
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw

st.set_page_config(page_title="CursorBot Barcode Generator", layout="wide")

st.title("CursorBot Barcode Generator")

try:
    with open('products.json') as f:
        products = json.load(f)
except FileNotFoundError:
    products = {"products": []}

def add_row(barcode, title, lagerplatz):
    global products
    products["products"].append({"barcode": barcode, "title": title, "lagerplatz": lagerplatz})
    with open('products.json', 'w') as f:
        json.dump(products, f)

def add_barcode(barcode, title, lagerplatz):
    bcid = "ean13"

    font = ImageFont.truetype("Arial.ttf", size=14)

    ean = barcode

    filename = "{}.png".format(barcode)

    url = "https://bwipjs-api.metafloor.com/?bcid={}&text={}".format(bcid, ean)

    response = requests.get(url)

    with open(filename, "wb") as f:
        f.write(response.content)
    filename = filename.strip()
    with Image.open(filename) as img:

        width, height = img.size
        
        max_title_width = 40

        wrapped_title = textwrap.wrap(title, width=max_title_width, break_long_words=True)
        wrapped_lagerplatz = textwrap.wrap(lagerplatz, width=max_title_width, break_long_words=True)
    
        wrapped_title_height = 0
        for line in wrapped_title:
            wrapped_title_height += font.getsize(line)[1]

        wrapped_lagerplatz_height = 0
        for line in wrapped_lagerplatz:
            wrapped_lagerplatz_height += font.getsize(line)[1]

        total_width = max(width, font.getsize(title)[0])

        new_width = total_width + 2 # Add extra margin on both sides
        new_height = height + wrapped_title_height + wrapped_lagerplatz_height + 32 # Add extra margin at bottom
        new_img = Image.new("RGBA", (new_width, new_height), color=(255, 255, 255, 255))

        barcode_x = (new_width - width) // 2
        new_img.paste(img, (barcode_x, 0), img)

        draw = ImageDraw.Draw(new_img)

        x = new_width // 2
        y = height + 10 + (wrapped_title_height // 2)

        for line in wrapped_title:
            text_width, text_height = font.getsize(line)
            draw.text((x - text_width // 2, y - text_height // 4), line, font=font, fill=(0, 0, 0, 255))
            y += text_height

        # Add a clear space row between title and lagerplatz
        y += font.getsize(" ")[1]

        for line in wrapped_lagerplatz:
            text_width, text_height = font.getsize(line)
            draw.text((x - text_width // 2, y - text_height // 4), line, font=font, fill=(0, 0, 0, 255))
            y += text_height

        final_filename = "final_" + filename
        new_img.save(final_filename)
        return final_filename

# Streamlit UI
barcode_textbox = st.text_input("Barcode:")
title_textbox = st.text_input("Titel:")
lagerplatz_textbox = st.text_input("Lagerplatz:")

add_button = st.button("Hinzufügen")
add_barcode_button = st.button("Barcodes erstellen")

if add_button:
    add_row(barcode_textbox, title_textbox, lagerplatz_textbox)

if add_barcode_button:
    final_filename = add_barcode(barcode_textbox, title_textbox, lagerplatz_textbox)
    st.image(final_filename)
