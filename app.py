import os
import torch
import base64
import shutil
import cv2
import mimetypes
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
    is_processed = db.Column(db.Boolean, default=False)

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

            _, buffer = cv2.imencode('.jpg', frame)
            photo_data = buffer.tobytes()
            new_tree = Tree(photo_name=frame_filename, photo=photo_data, state='Health')
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
    uploads_dir = os.path.join(os.path.dirname(__file__), "runs", "uploads")
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    for file in files:
        if file.filename == '':
            return "No selected file", 400
        
        mime_type, _ = mimetypes.guess_type(file.filename)
        if mime_type and mime_type.startswith('video/'):
            video_path = os.path.join(uploads_dir, file.filename)
            file.save(video_path)
            extract_frames(video_path, output_folder, frame_rate=10, db_session=db.session)
        else:
            filename = file.filename
            photo_data = file.read()
            new_tree = Tree(photo_name=filename, photo=photo_data, state='Health')
            db.session.add(new_tree)
            filenames.append(filename)
    
    db.session.commit()
    
    run_yolo_predictions()

    if os.path.exists(uploads_dir):
        shutil.rmtree(uploads_dir)
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)

    return redirect(url_for('index'))

@app.template_filter('b64encode')
def b64encode(data):
    return base64.b64encode(data).decode('utf-8')

def clear_folder(folder_path):
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

    trees = Tree.query.filter_by(is_processed=False).all()
    
    for tree in trees:
        image_path = os.path.join(predicted_folder, f"{tree.photo_name}.jpg")
        with open(image_path, 'wb') as img_file:
            img_file.write(tree.photo)

    results = model.predict(predicted_folder, save=True)
    predicted1_folder = os.path.join(os.path.dirname(__file__), "runs", "detect", "predict")
    detect = os.path.join(os.path.dirname(__file__), "runs", "detect")

    for tree in trees:
        processed_image_path = os.path.join(predicted1_folder, f"{tree.photo_name}.jpg")
        
        if os.path.exists(processed_image_path):
            damage_detected = False
            for result in results:
                if result.path == os.path.join(predicted_folder, f"{tree.photo_name}.jpg"):
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
                db.session.delete(tree)

            tree.is_processed = True
            db.session.commit()

    if os.path.exists(predicted_folder):
        shutil.rmtree(predicted_folder)
    if os.path.exists(detect):
        shutil.rmtree(detect)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)