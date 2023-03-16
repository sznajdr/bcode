 # Import required libraries
import streamlit as st
import requests
import os
from PIL import Image, ImageFont, ImageDraw
import textwrap

# Set page title
st.set_page_config(page_title="Barcode Generator")

# Define example number and title values
example_number = 6938936708209
example_title = "Druckbett PEI-Guss ROUGH 330x330"

# Define widgets
barcode_textbox = st.text_input("Barcode:", value=str(example_number))
title_textbox = st.text_input("Title:", value=str(example_title))
generate_button = st.button("Generate Barcode")

# Download Arial.ttf if it doesn't exist
if not os.path.exists("Arial.ttf"):
    url = "https://github.com/matomo-org/travis-scripts/raw/71555936095b4d4252ec0a2eeacd710a17793db4/fonts/Arial.ttf"
    response = requests.get(url)
    with open("Arial.ttf", "wb") as f:
        f.write(response.content)

# Define function to generate barcode
def generate_barcode(barcode, title):
    # Set the barcode type to EAN13
    bcid = "ean13"

    # Set the font for the product title
    font = ImageFont.truetype("Arial.ttf", size=14)

    # Set the API endpoint URL with includetext parameter
    url = f"https://bwipjs-api.metafloor.com/?bcid={bcid}&text={barcode}&includetext=1&bg=ffffff"

    # Send an HTTP GET request to the API endpoint
    response = requests.get(url)

    # Save the returned PNG image file with the product title as the filename
    filename = f"{barcode}.png"
    with open(filename, "wb") as f:
        f.write(response.content)

    return filename

# Define function to create a new image with extra margin to fit the wrapped product title text
def create_final_image(filename, title):
    # Open the saved barcode image
    with Image.open(filename) as img:
        # Get the size of the barcode image
        width, height = img.size

        # Set the maximum width for the product title text to three times the width of the barcode
        max_title_width = width * 3

        # Wrap the product title text into multiple lines if it is too long to fit
        wrapped_title= textwrap.fill(title, width=max_title_width, font=font)

        # Calculate the size of the wrapped product title text
        title_size = font.getsize_multiline(wrapped_title)

        # Create a new image with extra margin to fit the wrapped product title text
        final_img = Image.new("RGB", (width, height + title_size[1] + 10), "white")

        # Paste the barcode image onto the new image
        final_img.paste(img, (0, 0))

        # Draw the wrapped product title text onto the new image
        draw = ImageDraw.Draw(final_img)
        draw.text((0, height + 5), wrapped_title, font=font, fill="black")

        # Save the final image
        final_img.save(f"final_{filename}")

        return f"final_{filename}"

# Call the generate_barcode and create_final_image functions when the Generate Barcode button is clicked
if generate_button:
    barcode_filename = generate_barcode(barcode_textbox, title_textbox)
    final_filename = create_final_image(barcode_filename, title_textbox)

    # Display the final image
    st.image(final_filename)
