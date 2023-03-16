
import streamlit as st
import requests
import os
from PIL import Image, ImageFont, ImageDraw
import textwrap

st.set_page_config(page_title="Barcode Generator")
filename = "barcode.png"  # define filename with a default value

# Download Arial.ttf if it doesn't exist
if not os.path.exists("Arial.ttf"):
    url = "https://github.com/matomo-org/travis-scripts/raw/71555936095b4d4252ec0a2eeacd710a17793db4/fonts/Arial.ttf"
    response = requests.get(url)
    with open("Arial.ttf", "wb") as f:
        f.write(response.content)

# Define example number and title values
example_number = 6938936708209
example_title = "Druckbett PEI-Guss ROUGH 330x330"

# Define widgets
barcode_textbox = st.text_input("Barcode:", value=str(example_number))
title_textbox = st.text_input("Title:", value=str(example_title))
generate_button = st.button("Generate Barcode")


# Define functions
def generate_barcode():
    global filename  # make filename accessible inside the function
    barcode = barcode_textbox
    title = title_textbox
    # Generate barcode image for the entered barcode
    # Set the barcode type to EAN13
    bcid = "ean13"

    # Set the font for the product title
    font = ImageFont.truetype("Arial.ttf", size=14)

    # Set the EAN13 number as the text to encode
    ean = barcode

    # Set the product title as the filename
    filename = "{}.png".format(barcode)

    # Set the API endpoint URL with includetext parameter
    url = "https://bwipjs-api.metafloor.com/?bcid={}&text={}&includetext=1&bg=ffffff".format(bcid, ean)

    # Send an HTTP GET request to the API endpoint
    response = requests.get(url)

    # Save the returned PNG image file with the product title as the filename
    with open(filename, "wb") as f:
        f.write(response.content)

# Open the saved barcode image
filename = filename.strip()

# Create a new image with extra margin to fit the wrapped product title text
with Image.open(filename) as img:
    # Get the size of the barcode image
    width, height = img.size

    max_title_width = width * 3 # Set the maximum width for the product title text to three times the width of the barcode
    wrapped_title = textwrap.wrap(title_textbox, width=max_title_width, break_long_words=True) # Wrap the product title text into multiple lines if it is too long to fit
    wrapped_title_height = 0 # Calculate the total height required for the wrapped product title text
    for line in wrapped_title:
        wrapped_title_height += font.getsize(line)[1]

    # Calculate the total width required for the title and barcode
    total_width = max(width, font.getsize(title_textbox)[0])

    new_width = width * 2 # Fix the width to twice the width of the barcode
    new_height = height + wrapped_title_height + 3 * height # Add extra margin at bottom
    new_img = Image.new("RGBA", (new_width, new_height), color=(255, 255, 255, 255))

    # Paste the barcode image onto the new image
    barcode_img = img.convert("RGBA") # Convert the mode of the barcode image to RGBA
    new_img.paste(barcode_img, (int((new_width - width) / 2), 0))

    # Get the actual width of the wrapped product title text
    actual_title_width = min([font.getsize(line)[0] for line in wrapped_title])

    # Create a transparent overlay for the wrapped product title text
    overlay = Image.new("RGBA", new_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Draw the wrapped product title text onto the overlay
    y = height + 2 * height
    for line in wrapped_title:
        w, h = font.getsize(line)
        x = int((new_width - w) / 2)
        draw.text((x, y), line, font=font, fill=(0, 0, 0, 255))
        y += h

    # Merge the overlay with the new image
    new_img = Image.alpha_composite(new_img, overlay)

    # Save the final image with the product title as the filename
    final_filename = "{}_final.png".format(title)
    new_img.save(final_filename)
    # Display the new image with the product title
    st.image(final_filename, width=width)


    
if generate_button:
    generate_barcode()
st.markdown("[products.csv in colab](https://colab.research.google.com/drive/16l0hgwL2Mg-FkCQBiKBLIVj1IX6GsCrA?usp=sharing)")
