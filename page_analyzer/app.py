import os
from flask import (
    Flask,
    render_template,
)
from dotenv import load_dotenv


load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/urls', methods=['POST', 'GET'])
def urls():
    return 'Work in progress'
