import streamlit as st
import pandas as pd
import json
import requests
import textwrap
import os
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw

st.set_page_config(page_title="Barcode Generator", layout="wide")
st.set_page_config(page_title='-', page_icon='🎲')

import csv
import re
import time
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
import unicodedata

def get_data():
    url = 'https://www.winamax.de/sportwetten/sports/100000'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Use prettify() method to format HTML output
    pretty_html = soup.prettify()

    # Write output to a text file
    with open('output.txt', 'w', encoding='utf-8') as f:
        f.write(pretty_html)

    # Read in the file
    with open('output.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    text = unicodedata.normalize('NFKD', text)
    text = text.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
    text = text.replace('\u00e4', 'ae').replace('\u00f6', 'oe').replace('\u00fc', 'ue').replace('\u00a0', ' ')


    # Write the modified text back to the file
    with open('output.txt', 'w', encoding='utf-8') as f:
        f.write(text)        
        
    # Open the file and read its contents
    with open('output.txt', 'r') as f:
        data = f.read()

    data = unicodedata.normalize('NFKD', data)    

    data = data.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
    data = data.replace('\u00e4', 'ae').replace('\u00f6', 'oe').replace('\u00fc', 'ue').replace('\u00a0', ' ')

    # Find all occurrences of the pattern to extract ID-label pairs
    pattern_boosts = r'"(\d+)":{"label":"([^"]+)","available":true,"code":"yes"}'
    matches_boosts = re.findall(pattern_boosts, data)

    # Create a dictionary to store the ID-label pairs
    id_boost_dict = {}
    for match in matches_boosts:
        id_boost_dict[match[0]] = {'boost': match[1], 'prevOdd': None, 'odds': None}

    # Extract the odds data and store it in a dictionary
    odds_data = data.split('"odds":{')[1].split('},"cc"')[0]
    odds_dict = eval('{' + odds_data + '}')
    for id, odds in odds_dict.items():
        if id in id_boost_dict:
            id_boost_dict[id]['odds'] = odds

    # Find all occurrences of the pattern to extract previous odds
    pattern_prev_odds = r'"previousOdd":([\d.]+)'
    matches_prev_odds = re.findall(pattern_prev_odds, data)
    for i, match in enumerate(matches_prev_odds):
        id_boost_dict[list(id_boost_dict.keys())[i]]['prevOdd'] = match

    return id_boost_dict


def save_to_csv(id_boost_dict):
    with open('output.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['boost', 'prevOdd', 'odds']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for id, data in id_boost_dict.items():
            boost = data['boost'].replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
            prevOdd = str(data['prevOdd']).replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
            odds = str(data['odds']).replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
            writer.writerow({'boost': boost, 'prevOdd': prevOdd, 'odds': odds})

    
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

        total_width = width * 2 # Fixed width as twice the width of the initial barcode

        new_width = total_width
        new_height = height + wrapped_title_height + wrapped_lagerplatz_height + 22 # Adjusted margin at bottom
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

        for line in wrapped_lagerplatz:
            text_width, text_height = font.getsize(line)
            draw.text((x - text_width // 2, y - text_height // 4), line, font=font, fill=(0, 0, 0, 255))
            y += text_height

        final_filename = "final_" + filename
        new_img.save(final_filename)

        # Cut the image in half horizontally and only use the bottom half
        with Image.open(final_filename) as final_img:
            final_width, final_height = final_img.size
            cropped_img = final_img.crop((0, final_height // 2, final_width, final_height))
            cropped_filename = "cropped_" + final_filename
            cropped_img.save(cropped_filename)

        return cropped_filename

# Streamlit UI
barcode_textbox = st.text_input("Barcode:")
title_textbox = st.text_input("Titel:")
lagerplatz_textbox = st.text_input("Lagerplatz:")
add_barcode_button = st.button("Barcode erstellen")

st.markdown('<a href="https://colab.research.google.com/drive/16l0hgwL2Mg-FkCQBiKBLIVj1IX6GsCrA?authuser=2#scrollTo=uXPh6wWK_oD0">mehrere & csv in colab</a>', unsafe_allow_html=True)

if add_barcode_button:
    final_filename = add_barcode(barcode_textbox, title_textbox, lagerplatz_textbox)
    st.image(final_filename)
