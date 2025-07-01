from flask import Flask, render_template, request, jsonify
import os
import datetime

app = Flask(__name__,template_folder=r"C:\Users\Sahanar\Desktop\VScode")
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('Structure.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        ext = os.path.splitext(file.filename)[1]
        date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        new_filename = f"upload_{date_str}{ext}"
        save_path = os.path.join(UPLOAD_FOLDER, new_filename)
        file.save(save_path)
        return jsonify({'message': f"File saved as {new_filename}"})
    return jsonify({'error': 'No file received'}), 400

if __name__ == '__main__':
    app.run(debug=True)
