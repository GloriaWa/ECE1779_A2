from flask import Flask

storageApp = Flask(__name__)
from image_storage.src import main
