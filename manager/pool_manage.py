import threading
import requests, datetime
import sys, os
import manager.config as conf
from flask import render_template, request, g, jsonify

from manager.Utilities import *
from manager import webapp
from host_map import *


def pool_update_validate():
    # Check if at least one of the cache node is full, else, add node request invalid

    for i in range(conf.active_node):
        re = requests.post(userApp + '/get_key_list')
        re.json()
        count = re["count"]

        if count == conf.capacity:
            return True

    return False


def double_node():
    # Double the node
    new_pool = min(2 * conf.active_node, 8)

    id = []
    img = []

    for i in range(conf.active_node):
        re = requests.post(conf.cache_pool[i] + '/get_all')
        re.json()
        id.extend(re["keys"])
        img.extend(re["items"])

        requests.post(conf.cache_pool[i] + '/clear')

    reallocate(id, img, new_pool)
    return

def divide_node():
    # Divide the node num by two
    return

def add_node():
    # Add one node
    return

def minus_node():
    # decrease one node
    return

def reallocate(id, img, new_pool):
    # reallocate the content in the cache system
    conf.active_node = new_pool




    return

