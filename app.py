import os
import torch
import shutil
import cv2
import mimetypes
from datetime import datetime
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
    photo = db.Column(db.String(255), nullable=False) 
    processed_photo = db.Column(db.String(255), nullable=True)
    class_name = db.Column(db.Enum('Disease', 'Health'), nullable=False, default='Health')
    photo_date = db.Column(db.DateTime, nullable=False)

with app.app_context():
    db.create_all()

# @app.route('/delete/<int:item_id>', methods=['POST'])
# def delete(item_id):
#     tree = Tree.query.get_or_404(item_id)
#     db.session.delete(tree)
#     db.session.commit()
#     return redirect(url_for('index'))

def get_video_filename(video_path):
    return os.path.basename(video_path)

def extract_frames(video_path, output_folder, frame_rate=10, db_session=None):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    video_capture = cv2.VideoCapture(video_path)
    video_filename = get_video_filename(video_path)
    
    if not video_capture.isOpened():
        print("Ошибка: Не удалось открыть видео.")
        return

    fps = video_capture.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * frame_rate) # для кадра надо делить
    current_frame = 0
    frame_count = 0

    while True:
        ret, frame = video_capture.read()
        
        if not ret:
            break

        if current_frame % frame_interval == 0:
            frame_filename = f"{video_filename}_{frame_count:04d}.jpg"
            frame_path = os.path.join(output_folder, frame_filename)
            cv2.imwrite(frame_path, frame)
            relative_path = os.path.relpath(frame_path, start=os.path.join(os.path.dirname(__file__), "static"))
            relative_path = relative_path.replace("\\", "/")
            file_creation_date = datetime.fromtimestamp(os.path.getctime(video_path))
            new_tree = Tree(photo=relative_path, class_name='Health', photo_date=file_creation_date)
            db_session.add(new_tree)
            frame_count += 1
        
        current_frame += 1

    video_capture.release()
    print(f"Извлечено {frame_count} кадров в папку '{output_folder}'.")

@app.route('/')
def index():
    trees = Tree.query.order_by(Tree.id.desc()).all()
    return render_template('index.html', trees=trees)

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return "No file part", 400
    
    files = request.files.getlist('files')
    filenames = []
    output_folder = os.path.join(os.path.dirname(__file__), "runs", "predict")
    base_images_dir = os.path.join(os.path.dirname(__file__), "static", "base_images")
    if not os.path.exists(base_images_dir):
        os.makedirs(base_images_dir)

    for file in files:
        if file.filename == '':
            return "No selected file", 400
        
        mime_type, _ = mimetypes.guess_type(file.filename)
        if mime_type and mime_type.startswith('video/'):
            video_path = os.path.join(base_images_dir, file.filename)
            file.save(video_path)
            extract_frames(video_path, output_folder, frame_rate=10, db_session=db.session)
        else:
            filename = file.filename
            photo = os.path.join(base_images_dir, filename)
            file.save(photo)
            relative_path = os.path.relpath(photo, start=os.path.join(os.path.dirname(__file__), "static")) 
            relative_path = relative_path.replace("\\", "/")
            file_creation_date = datetime.fromtimestamp(os.path.getctime(photo)) 
            new_tree = Tree(photo=relative_path, class_name='Health', photo_date=file_creation_date)
            db.session.add(new_tree)
            filenames.append(filename)

    db.session.commit()
    run_yolo_predictions()

    return redirect(url_for('index'))

def run_yolo_predictions():
    model_path = os.path.join(os.path.dirname(__file__), "static", "best.pt")
    model = YOLO(model_path)

    predicted_folder = os.path.join(os.path.dirname(__file__), "runs", "predict")
    os.makedirs(predicted_folder, exist_ok=True)

    trees = Tree.query.filter(Tree.processed_photo.is_(None)).all()
    for tree in trees:
        image_path = os.path.join(os.path.dirname(__file__), "static", tree.photo)
        destination_path = os.path.join(predicted_folder, os.path.basename(tree.photo))

        if os.path.exists(image_path):
            if os.path.abspath(image_path) == os.path.abspath(destination_path):
                print(f"Skipping copy for {image_path}, as it is the same file as {destination_path}.")
            else:
                try:
                    shutil.copy(image_path, destination_path)
                    print(f"Copied {image_path} to {destination_path}.")
                except Exception as e:
                    print(f"Failed to copy {image_path} to {destination_path}: {e}")
        else:
            print(f"Error: The image path {image_path} does not exist.")

    results = model.predict(predicted_folder, save=True)
    predicted_model_folder = os.path.join(os.path.dirname(__file__), "runs", "detect", "predict")
    run = os.path.join(os.path.dirname(__file__), "runs")
    destination_folder = os.path.join(os.path.dirname(__file__), "static", "images")
    destination_base_folder = os.path.join(os.path.dirname(__file__), "static", "base_images")
    os.makedirs(destination_folder, exist_ok=True)

    for item in os.listdir(predicted_folder):
        source = os.path.join(predicted_folder, item)
        destination = os.path.join(destination_base_folder, item)
        shutil.copy2(source, destination)

    for item in os.listdir(predicted_model_folder):
        source = os.path.join(predicted_model_folder, item)
        destination = os.path.join(destination_folder, item)
        shutil.copy2(source, destination)

    for tree in trees:
        processed_image_path = os.path.join(destination_folder, os.path.basename(tree.photo))
        
        if os.path.exists(processed_image_path):
            damage_detected = False
            for result in results:
                if result.path == os.path.join(predicted_folder, os.path.basename(tree.photo)):
                    if result.boxes is not None and len(result.boxes) > 0:
                        for box in result.boxes:
                            class_id = int(box.cls)
                            class_name = result.names[class_id]
                            if class_name == 'BadTree':
                                damage_detected = True
                                break
                    break 

            if damage_detected:
                tree.class_name = 'Disease'
                relative_processed_path = os.path.relpath(processed_image_path, start=os.path.join(os.path.dirname(__file__), "static"))
                relative_processed_path = relative_processed_path.replace("\\", "/")
                tree.processed_photo = relative_processed_path
            else:
                tree.class_name = 'Health'
                db.session.delete(tree)

            db.session.commit()

    if os.path.exists(run):
        shutil.rmtree(run)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)