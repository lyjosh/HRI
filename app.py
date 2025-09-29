from flask import Flask, render_template, request, jsonify
import base64
from PIL import Image
import numpy as np
import io as pyio
import os
import re
import logging

app = Flask(__name__)

# Set up logging for better debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_drawing', methods=['POST'])
def process_drawing():
    try:
        # Validate request data
        data = request.get_json()
        if not data or 'drawing' not in data:
            logger.error("No drawing data provided in request")
            return jsonify({'error': 'No drawing data provided'}), 400

        image_data = data['drawing']
        
        # Validate data URL format
        if not isinstance(image_data, str) or 'data:image' not in image_data:
            logger.error("Invalid image data format")
            return jsonify({'error': 'Invalid image data format'}), 400

        # Split data URL
        try:
            header, encoded = image_data.split(",", 1)
            logger.info(f"Processing image with header: {header}")
        except ValueError:
            logger.error("Invalid data URL format - missing comma separator")
            return jsonify({'error': 'Invalid data URL format'}), 400

        # Decode base64 image
        try:
            binary_data = base64.b64decode(encoded)
            image = Image.open(pyio.BytesIO(binary_data)).convert("RGBA")
            logger.info(f"Successfully decoded image of size: {image.size}")
        except Exception as e:
            logger.error(f"Failed to decode image: {e}")
            return jsonify({'error': f'Failed to decode image: {str(e)}'}), 400

        # Create directories
        try:
            os.makedirs("static/tiles", exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create tiles directory: {e}")
            return jsonify({'error': 'Failed to create storage directory'}), 500

        # Get next image ID
        curr_image_num = next_image_id("static/tiles")
        tile_dir = f"static/tiles/img{curr_image_num}"
        
        try:
            os.makedirs(tile_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create tile directory: {e}")
            return jsonify({'error': 'Failed to create tile directory'}), 500

        # Save full image
        full_image_path = f"static/drawing_{curr_image_num}.png"
        try:
            image.save(full_image_path)
            logger.info(f"Saved full image to: {full_image_path}")
        except Exception as e:
            logger.error(f"Failed to save full image: {e}")
            return jsonify({'error': 'Failed to save image'}), 500

        # Tile configuration
        tile_width = 100
        tile_height = 100

        img_w, img_h = image.size
        cols = img_w // tile_width
        rows = img_h // tile_height
        
        # Check if image is large enough for tiling
        if cols == 0 or rows == 0:
            logger.warning(f"Image too small for tiling: {img_w}x{img_h}")
            return jsonify({'error': f'Image is too small ({img_w}x{img_h}). Minimum size is {tile_width}x{tile_height}'}), 400

        logger.info(f"Creating {rows}x{cols} grid ({rows*cols} tiles)")

        # Create tiles
        tile_paths = []
        for row in range(rows):
            for col in range(cols):
                left = col * tile_width
                upper = row * tile_height
                right = left + tile_width
                lower = upper + tile_height
                
                try:
                    tile = image.crop((left, upper, right, lower))
                    save_path = f"{tile_dir}/tile_{row}_{col}.png"
                    tile.save(save_path)
                    tile_paths.append((row, col, save_path))
                except Exception as e:
                    logger.error(f"Failed to create tile ({row},{col}): {e}")
                    return jsonify({'error': f'Failed to create tile at position ({row},{col})'}), 500

        # Compute grayscale averages for tiles
        tile_gray_averages = {}
        for row, col, path in tile_paths:
            try:
                gray_val = average_grayscale_of_image(path)
                tile_gray_averages[f"{row},{col}"] = gray_val
            except Exception as e:
                logger.error(f"Failed to compute grayscale for tile ({row},{col}): {e}")
                # Continue processing other tiles instead of failing completely
                tile_gray_averages[f"{row},{col}"] = 128  # Default middle gray


        logger.info(f"Successfully processed image {curr_image_num} with {len(tile_paths)} tiles")

        return jsonify({
            'message': f"Successfully processed image into {rows * cols} tiles",
            'image_id': curr_image_num,
            'tile_dir': tile_dir,
            'tile_size': {'width': tile_width, 'height': tile_height},
            'image_size': {'width': img_w, 'height': img_h},
            'grid': {'rows': rows, 'cols': cols},
            'tile_gray_averages': tile_gray_averages,
            'full_image_path': full_image_path
        }), 200

    except Exception as e:
        logger.error(f"Unexpected error in process_drawing: {e}")
        return jsonify({'error': 'Internal server error occurred'}), 500


def next_image_id(root_dir: str) -> int:
    """
    Find the next available image ID by scanning existing img directories.
    Returns 0 if no existing directories found.
    """
    max_id = -1
    pat = re.compile(r"^img(\d+)$")
    
    try:
        if os.path.exists(root_dir):
            for name in os.listdir(root_dir):
                if os.path.isdir(os.path.join(root_dir, name)):  # Only check directories
                    m = pat.match(name)
                    if m:
                        curr_id = int(m.group(1))
                        max_id = max(max_id, curr_id)
        else:
            logger.info(f"Root directory {root_dir} doesn't exist yet")
    except OSError as e:
        logger.error(f"Error reading directory {root_dir}: {e}")
    
    return max_id + 1


def average_grayscale_of_image(image_path: str) -> int:
    """
    Convert image to grayscale and return average intensity (0–255).
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Average grayscale value as integer (0-255)
        
    Raises:
        Exception: If image cannot be opened or processed
    """
    try:
        with Image.open(image_path).convert("L") as im:  # "L" = grayscale
            arr = np.asarray(im, dtype=np.float64)  # Use float64 for better precision
            if arr.size == 0:
                logger.warning(f"Empty image array for {image_path}")
                return 0
            mean = arr.mean()
            return int(round(np.clip(mean, 0, 255)))  # Ensure result is in valid range
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {e}")
        raise


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Create static directory if it doesn't exist
    os.makedirs("static", exist_ok=True)
    app.run(debug=True, host='127.0.0.1', port=5000)