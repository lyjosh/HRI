from flask import Flask, render_template, request, redirect, jsonify, url_for
import sqlite3
import base64
from PIL import Image
from skimage import io
from skimage.io import imread
import numpy as np
import io
import os


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_drawing', methods=['POST'])
def process_drawing():
    data = request.get_json()
    if not data or 'drawing' not in data:
        return jsonify({'error': 'No drawing data provided'}), 400

    image_data = data['drawing']
    width = int(data.get('width', 600))
    height = int(data.get('height', 400))
    
        
    header, encoded = image_data.split(",", 1)
    binary_data = base64.b64decode(encoded)
    
    image = Image.open(io.BytesIO(binary_data))
    
    os.makedirs("static/tiles", exist_ok=True)
    
    curr_image_num = check_number_of_images_in_static()
    tile_dir = f"static/tiles/img{curr_image_num}"
    os.makedirs(tile_dir, exist_ok=True)
    full_image_path = f"static/drawing_{curr_image_num}.png"
    
    image.save(full_image_path)
    
    tile_width = 100
    tile_height = 100
    cols = width // tile_width   # How many columns
    rows = height // tile_height # How many rows

    #  Loop through each tile grid position
    for row in range(rows):
        for col in range(cols):
            # Define coordinates for this tile
            left = col * tile_width
            upper = row * tile_height
            right = left + tile_width
            lower = upper + tile_height

            # Crop out this tile from the original image
            tile = image.crop((left, upper, right, lower))

            # Save the tile to disk
            tile.save(f"static/tiles/img{curr_image_num}/tile_{row}_{col}.png")
   
    find_average_color("static/tiles/img{curr_image_num}", width, height)
    
    # Return a success message
    return f"Saved {rows * cols} tiles", 200


def check_number_of_images_in_static():
    directory = "static/tiles"
    if not os.path.exists(directory):
        return 0
    
    files = os.listdir(directory)
    image_files = [f for f in files if f.endswith(('.png', '.jpg', '.jpeg'))]
    
    return len(image_files)


def find_average_color(image_path, width, height):
    Avg_values = []
    # loop though all sections of image
    for i in range(0, width):
        for j in range(0, height):
            # Read the image
            image = imread(image_path)
            
            # Resize the image to 1x1 pixel
            resized_image = Image.fromarray(image).resize((1, 1))
            
            # Convert to numpy array
            image_array = np.array(resized_image)
            
            # Calculate the average color
            average_color = np.mean(image_array, axis=(0, 1))
            
            Avg_values.append(tuple(average_color.astype(int)))
    
    # Calculate the average color
    average_color = np.mean(image_array, axis=(0, 1))
    
    return tuple(average_color.astype(int))

if __name__ == '__main__':
    app.run(debug=True)