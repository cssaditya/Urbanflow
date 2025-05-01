from flask import Flask, request, render_template, jsonify
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import os

# Initialize Flask app
app = Flask(__name__)

# Path to save uploaded images
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Define device (CPU or GPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load the same ResNet18 architecture
model = models.resnet18(pretrained=False)
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, 2)  # Two classes: Accident, Not Accident

# Load the trained weights
model_path = "accident_detection.pth"  # Ensure the model file is in the project directory
state_dict = torch.load(model_path, map_location=device)
model.load_state_dict(state_dict)

# Move model to the correct device
model.to(device)
model.eval()

# Define image transformations (must match the training pipeline)
transform = transforms.Compose([
    transforms.Resize((224, 224)),  # Resize to ResNet input size
    transforms.ToTensor(),  # Convert to tensor
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])  # Normalize like ImageNet
])

def predict(image_path):
    """Predict accident or non-accident from an image."""
    image = Image.open(image_path).convert("RGB")  # Open image
    image = transform(image).unsqueeze(0).to(device)  # Preprocess image
    
    with torch.no_grad():
        output = model(image)
        _, predicted = torch.max(output, 1)

    return "Accident" if predicted.item() == 0 else "Not Accident"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "image" not in request.files:
            return jsonify({"error": "No file uploaded!"})

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"error": "No file selected!"})

        # Save image to the uploads folder
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(image_path)

        # Get prediction
        result = predict(image_path)

        return jsonify({"prediction": result})

    return render_template("index.html")  # Serve HTML form

if __name__ == "__main__":
    app.run(debug=True)  # Run locally
