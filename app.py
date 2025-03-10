from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
import matplotlib.pyplot as plt
import ollama
import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pyttsx3  # Text-to-Speech
import random
import os
from dalle import generate_story_image   # AI-generated images
from database import db
from models import User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'supersecretkey'

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

convo = []

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please login.', 'danger')
            return redirect(url_for('login'))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('story'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/story', methods=['GET', 'POST'])
@login_required
def story():
    if request.method == 'POST':
        story_prompt = request.form['story_prompt']
        response = stream_response(story_prompt)

        # Generate Cover Image (DALL·E)
        image_url = generate_story_image(story_prompt)

        # Generate Audio (TTS)
        audio_filename = generate_audio(response)

        return render_template('story.html', story=response, plot_url=None, image_url=image_url, audio_file=audio_filename)

    return render_template('story.html', story=None, plot_url=None, image_url=None, audio_file=None)

@app.route('/download_pdf', methods=['POST'])
@login_required
def download_pdf():
    story = request.form['story']
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    text = c.beginText(40, 750)
    text.setFont("Helvetica", 12)
    for line in story.split('\n'):
        text.textLine(line)
    c.drawText(text)
    c.save()
    pdf_buffer.seek(0)

    return send_file(pdf_buffer, as_attachment=True, download_name='generated_story.pdf', mimetype='application/pdf')

def stream_response(prompt):
    convo.append({'role': 'user', 'content': prompt})
    response = ''
    stream = ollama.chat(model='llama3.1:8b', messages=convo, stream=True)
    for chunk in stream:
        response += chunk['message']['content']
    convo.append({'role': 'assistant', 'content': response})
    return response

def generate_audio(text):
    """Converts text to speech and saves as an audio file."""
    engine = pyttsx3.init()
    audio_filename = f"static/audio/story_{random.randint(1000, 9999)}.mp3"
    engine.save_to_file(text, audio_filename)
    engine.runAndWait()
    return audio_filename

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
