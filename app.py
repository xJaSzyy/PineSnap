import os
import torch
import base64
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from ultralytics import YOLO

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure the MySQL database connection
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the model with BLOB and ENUM fields
class Tree(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo_name = db.Column(db.String(255), nullable=False)  # New field for the name of the tree
    photo = db.Column(db.LargeBinary, nullable=False)  # BLOB field for storing images
    processed_photo = db.Column(db.LargeBinary, nullable=True)
    state = db.Column(db.Enum('Disease', 'Health'), nullable=False, default='Health')  # ENUM field

# Create the database and tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    trees = Tree.query.all()  # Fetch all images from the database
    return render_template('index.html', trees=trees)

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return "No file part", 400  # Return a 400 Bad Request response
    
    files = request.files.getlist('files[]')
    filenames = []  # List to store filenames

    for file in files:
        if file.filename == '':
            return "No selected file", 400  # Return a 400 Bad Request response
        
        # Get the filename
        filename = file.filename
        filenames.append(filename)  # Store the filename in the list

        # Read the image file as binary
        photo_data = file.read()
        
        # Create a new Tree instance with default state 'Health'
        new_tree = Tree(photo_name=filename ,photo=photo_data, state='Health')
        
        # Add and commit the new record to the database
        db.session.add(new_tree)
    
    db.session.commit()  # Commit all at once after the loop
    
    # Run predictions after uploading images
    run_yolo_predictions()

    return redirect(url_for('index'))  # Redirect to the index after successful upload

@app.template_filter('b64encode')
def b64encode(data):
    return base64.b64encode(data).decode('utf-8')

def run_yolo_predictions():
    model = YOLO("D:\\_diplom\\code\\static\\best.pt")
    
    # Create a temporary folder for predictions
    predicted_folder = "D:\\_diplom\\code\\runs\\predict"
    os.makedirs(predicted_folder, exist_ok=True)

    # Extract images from the database
    trees = Tree.query.all()
    for tree in trees:
        # Save the image to the temporary folder
        image_path = os.path.join(predicted_folder, f"{tree.photo_name}.jpg")
        with open(image_path, 'wb') as img_file:
            img_file.write(tree.photo)

    # Run predictions
    results = model.predict(predicted_folder, save=True)

    predicted1_folder = "D:\\_diplom\\code\\runs\\detect\\predict"
    # Process the results and save the processed images back to the database
    for tree in trees:
        # Assuming the processed image is saved with the same name as the original
        processed_image_path = os.path.join(predicted1_folder, f"{tree.photo_name}.jpg")  # Adjust if necessary
        if os.path.exists(processed_image_path):
            with open(processed_image_path, 'rb') as processed_img_file:
                processed_image_data = processed_img_file.read()
                # Update the processed_photo field in the database
                tree.processed_photo = processed_image_data
                db.session.commit()  # Commit the changes for each tree

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they do not exist
    app.run(debug=True)