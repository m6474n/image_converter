from flask import Flask, request, render_template, send_file, jsonify
from PIL import Image
import os
import uuid

# Initialize Flask app
app = Flask(__name__)

# Define upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Make sure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home route (render HTML form)
@app.route('/')
def index():
    return render_template('index.html')

# Upload and convert route
@app.route('/upload', methods=['POST'])
def upload_files():
    # Check if files are part of the request
    if 'files' not in request.files:
        return 'No files part', 400
    
    files = request.files.getlist('files')
    
    if not files:
        return 'No files selected', 400

    # List to hold the paths of the converted WebP files
    webp_files = []

    for file in files:
        if file.filename == '':
            continue  # Skip if file has no name

        if file and allowed_file(file.filename):
            # Generate a unique filename for the uploaded image
            original_filename = file.filename
            filename = str(uuid.uuid4()) + os.path.splitext(original_filename)[1]
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            try:
                # Open image using Pillow
                with Image.open(file_path) as img:
                    # Convert to WebP format
                    webp_filename = str(uuid.uuid4()) + ".webp"
                    webp_path = os.path.join(UPLOAD_FOLDER, webp_filename)
                    img.save(webp_path, "WEBP")
                    webp_files.append(webp_path)
            except Exception as e:
                return f"Error processing image {original_filename}: {e}", 500

    # If there are multiple WebP files, return them as a zip archive
    if len(webp_files) > 1:
        from zipfile import ZipFile
        zip_filename = str(uuid.uuid4()) + '.zip'
        zip_path = os.path.join(UPLOAD_FOLDER, zip_filename)

        # Create a zip file
        with ZipFile(zip_path, 'w') as zipf:
            for file in webp_files:
                zipf.write(file, os.path.basename(file))

        # Cleanup: Remove original WebP files after zipping
        for file in webp_files:
            os.remove(file)

        return send_file(zip_path, as_attachment=True)

    # If only one file, send it directly
    return send_file(webp_files[0], as_attachment=True)

# Run the app on localhost
if __name__ == '__main__':
    app.run(debug=True)
