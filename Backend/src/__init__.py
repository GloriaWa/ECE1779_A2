import flask
from flask import Flask

UPLOAD_FOLDER = ''

backendApp = Flask(__name__)
backendApp.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


from Backend.src import Backend