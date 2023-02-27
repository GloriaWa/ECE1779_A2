from flask import Flask
import os

global memcache
IMG_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '\costum_imgs'

webapp = Flask(__name__)
from Frontend import main




