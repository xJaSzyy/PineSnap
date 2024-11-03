import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import base64

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
    photo = db.Column(db.LargeBinary, nullable=False)  # BLOB field for storing images
    state = db.Column(db.Enum('Disease', 'Health'), nullable=False, default='Health')  # ENUM field

# Create the database and tables
with app.app_context():
    db.create_all()

# def insert_images_from_folder(folder_path, state='Health'):
#     with app.app_context():
#         for filename in os.listdir(folder_path):
#             if filename.endswith(('.jpg', '.jpeg')):  # Добавьте другие расширения, если необходимо
#                 file_path = os.path.join(folder_path, filename)
                
#                 # Чтение файла изображения как бинарного
#                 with open(file_path, 'rb') as file:
#                     photo_data = file.read()
                
#                 # Создание нового экземпляра Tree
#                 new_tree = Tree(photo=photo_data, state=state)
                
#                 # Добавление и коммит нового рекорда в базу данных
#                 db.session.add(new_tree)
        
#         db.session.commit()  # Коммит после добавления всех изображений
#         print(f"Images from {folder_path} inserted successfully.")

# def insert_tree(photo_path, state):
#     with app.app_context():
#         # Read the image file as binary
#         with open(photo_path, 'rb') as file:
#             photo_data = file.read()
        
#         # Create a new ChristmasTree instance
#         new_tree = Tree(photo=photo_data, state=state)
        
#         # Add and commit the new record to the database
#         db.session.add(new_tree)
#         db.session.commit()
#         print("New tree inserted successfully.")

# Example usage
# insert_tree('D:\_diplom\code\images\IMG20241011174134.jpg', 'Health')

# def insert_images_from_folder(folder_path, state):
#     for filename in os.listdir(folder_path):
#         if filename.endswith(('.jpg', '.jpeg')):  # Add more extensions if needed
#             file_path = os.path.join(folder_path, filename)
#             with open(file_path, 'rb') as file:
#                 img_data = file.read()
#                 new_tree = Tree(photo=img_data, state=state)  # You can set state based on your logic
#                 db.session.add(new_tree)
#     db.session.commit()

# insert_images_from_folder('D:\_diplom\code\images', 'Health')

# @app.route('/upload_images', methods=['POST'])
# def upload_images():
#     folder_path = r'D:\_diplom\code\images'  # Raw string  # Path to your images folder
#     try:
#         insert_images_from_folder(folder_path)
#         return "Images uploaded successfully!", 200
#     except Exception as e:
#         return f"An error occurred: {str(e)}", 500

@app.route('/gallery')
def gallery():
    # Fetch all images from the database
    trees = Tree.query.all()
    return render_template('gallery.html', trees=trees)

@app.template_filter('b64encode')
def b64encode(data):
    return base64.b64encode(data).decode('utf-8')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создание таблиц, если они не существуют
        # insert_images_from_folder(r'D:\_diplom\code\images', 'Health')
    app.run(debug=True)