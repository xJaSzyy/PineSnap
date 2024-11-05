import os
import torch
import base64
import shutil
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from ultralytics import YOLO

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Tree(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo_name = db.Column(db.String(255), nullable=False)
    photo = db.Column(db.LargeBinary, nullable=False)
    processed_photo = db.Column(db.LargeBinary, nullable=True)
    state = db.Column(db.Enum('Disease', 'Health'), nullable=False, default='Health')

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    trees = Tree.query.all()
    return render_template('index.html', trees=trees)

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return "No file part", 400
    
    files = request.files.getlist('files[]')
    filenames = []

    for file in files:
        if file.filename == '':
            return "No selected file", 400
        
        filename = file.filename
        filenames.append(filename)
        photo_data = file.read()
        new_tree = Tree(photo_name=filename ,photo=photo_data, state='Health')
        db.session.add(new_tree)
    
    db.session.commit()
    run_yolo_predictions()

    return redirect(url_for('index'))

@app.template_filter('b64encode')
def b64encode(data):
    return base64.b64encode(data).decode('utf-8')

def clear_folder(folder_path):
    """Remove all files and subdirectories in the specified folder."""
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

def run_yolo_predictions():
    model_path = os.path.join(os.path.dirname(__file__), "static", "best.pt")
    model = YOLO(model_path)

    predicted_folder = os.path.join(os.path.dirname(__file__), "runs", "predict")
    os.makedirs(predicted_folder, exist_ok=True)

    trees = Tree.query.all()
    for tree in trees:
        image_path = os.path.join(predicted_folder, f"{tree.photo_name}.jpg")
        with open(image_path, 'wb') as img_file:
            img_file.write(tree.photo)

    results = model.predict(predicted_folder, save=True)
    predicted1_folder = os.path.join(os.path.dirname(__file__), "runs", "detect", "predict")

    for tree in trees:
        processed_image_path = os.path.join(predicted1_folder, f"{tree.photo_name}.jpg")
        
        if os.path.exists(processed_image_path):
            damage_detected = False
            for result in results:
                if result.path == image_path:
                    if result.boxes is not None and len(result.boxes) > 0:
                        for box in result.boxes:
                            class_id = int(box.cls)
                            class_name = result.names[class_id]
                            if class_name == 'BadTree':
                                damage_detected = True
                                break
                    break

            if damage_detected:
                tree.state = 'Disease'
                with open(processed_image_path, 'rb') as processed_img_file:
                    tree.processed_photo = processed_img_file.read()
            else:
                tree.state = 'Health'

            db.session.commit()
    
    clear_folder(predicted_folder)
    if os.path.exists(predicted1_folder):
        shutil.rmtree(predicted1_folder)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)