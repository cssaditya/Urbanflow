from flask import Flask, request, jsonify, render_template
from flask_cors import CORS  # Import CORS
import cv2
import numpy as np
import easyocr
from ultralytics import YOLO
import os

app = Flask(__name__, template_folder="templates")  # Set the templates folder
CORS(app)  # Enable CORS for all routes

# Load YOLOv8 model
model = YOLO("yolov8n.pt")
reader = easyocr.Reader(['en'])

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/", methods=["GET"])
def index():
    """Render the index.html page"""
    return render_template("index.html", license_plate=None)


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return render_template("index.html", license_plate="No file uploaded")

    file = request.files["file"]
    if file.filename == "":
        return render_template("index.html", license_plate="No selected file")

    # Save uploaded image
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)

    # Process image
    detected_text = process_image(file_path)

    # Return the result in index.html
    return render_template("index.html", license_plate=detected_text)


def process_image(image_path):
    """Detects license plate & applies OCR"""
    img = cv2.imread(image_path)

    # Detect objects with YOLO
    results = model(img)[0]  # Get the first detection result

    for result in results.boxes.data:  # Use `boxes.data`
        x1, y1, x2, y2, conf, cls = map(int, result[:6])

        # Check if detected class is a license plate
        if cls in [0]:  # Change 0 to the correct class index if needed
            plate_img = img[y1:y2, x1:x2]  # Crop license plate region

            # Convert to grayscale
            gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)

            # Improve contrast
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # Apply thresholding
            thresh = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

            # Run OCR
            text = reader.readtext(thresh, detail=0)
            return text if text else "No text detected"

    return "No license plate found"


if __name__ == "__main__":
    app.run(debug=True)
