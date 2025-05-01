import os
import requests
import json
from flask import Flask, request, render_template
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import piexif
import piexif.helper
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Create an upload folder
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# SightEngine API Credentials from environment variables
API_USER = os.getenv("SIGHTENGINE_API_USER")
API_SECRET = os.getenv("SIGHTENGINE_API_SECRET")

def check_image(image_path):
    """Check if an image is AI-generated using SightEngine API."""
    params = {
        'models': 'genai',
        'api_user': API_USER,
        'api_secret': API_SECRET
    }

    with open(image_path, 'rb') as img_file:
        files = {'media': img_file}
        response = requests.post('https://api.sightengine.com/1.0/check.json', files=files, data=params)
        output = json.loads(response.text)

        ai_score = output.get("type", {}).get("ai_generated", 0)

        if ai_score > 0.5:
            return "🔴 The image is AI-Generated (Fake)."
        else:
            return "🟢 The image is Real (Not AI-Generated)."

def get_image_age(image_path):
    """Extracts creation date from EXIF metadata and calculates image age."""
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        
        # Try getting EXIF date
        if exif_data:
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name == "DateTimeOriginal":  # Date when the image was originally taken
                    image_date = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    age_days = (datetime.now() - image_date).days
                    return f"📅 Image Age: {age_days} days old (from EXIF metadata)"

        # If EXIF metadata is missing, fallback to file modification time
        mod_time = os.path.getmtime(image_path)
        image_date = datetime.fromtimestamp(mod_time)
        age_days = (datetime.now() - image_date).days
        return f"📅 Image Age: {age_days} days old (from file metadata)"
    
    except Exception as e:
        return "📅 Image Age: Error reading metadata"

def is_newer_than_one_day(image_path):
    """Checks if the image is newer than one day."""
    try:
        img = Image.open(image_path)
        exif_data = img.info.get("exif")
        
        if exif_data:
            exif_dict = piexif.load(exif_data)
            datetime_original = exif_dict.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal)
            
            if datetime_original:
                image_date = datetime.strptime(datetime_original.decode(), "%Y:%m:%d %H:%M:%S")
                return (datetime.now() - image_date).days < 1
        
        # Fallback: Use file modification time
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(image_path))
        return (datetime.now() - file_mod_time).days < 1
    except Exception as e:
        print(f"Error reading image date metadata: {e}")
        return False

def is_image_from_google(image_path):
    """Checks if an image was taken from Google or downloaded from the internet."""
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()

        if exif_data:
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name == "Software":
                    software_used = value.lower()
                    if "google" in software_used or "chrome" in software_used:
                        return "🟡 The image was downloaded from Google."
        
        return "🟢 The image does not appear to be from Google."
    
    except Exception as e:
        return "🟡 Unable to determine if the image is from Google."

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        if "image" not in request.files:
            return "No file uploaded", 400
        
        file = request.files["image"]
        if file.filename == "":
            return "No selected file", 400
        
        # Save the uploaded file
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)

        # Check if the image is AI-generated
        result = check_image(file_path)

        # Check if the image is newer than one day
        if is_newer_than_one_day(file_path):
            image_status = "🟢 The image is newer than 1 day."
        else:
            image_status = "🔴 The image is older than 1 day."

        # Check if the image is from Google
        google_status = is_image_from_google(file_path)

        return render_template("index.html", uploaded_image=file.filename, result=result, image_status=image_status, google_status=google_status)

    return render_template("index.html", uploaded_image=None, result=None, image_status=None, google_status=None)

if __name__ == "__main__":
    app.run(debug=True) 