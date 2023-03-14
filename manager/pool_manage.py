import threading
import requests, datetime
import sys, os
import manager.config as conf
from flask import render_template, request, g, jsonify
import hashlib as hl

from manager.Utilities import *
from manager import webapp
from host_map import *


def pool_update_validate():
    # Check if at least one of the cache node is full, else, add node request invalid

    for i in range(conf.active_node):
        re = requests.post(conf.active_node[i] + '/get_key_list')
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
        re = re.json()

        if re != None:
            id.extend(re["keys"])
            img.extend(re["items"])

        requests.post(conf.cache_pool[i] + '/clear')

    reallocate(id, img, new_pool)
    return

def divide_node():
    # Divide the node num by two
    new_pool = max(conf.active_node // 2, 1)

    id = []
    img = []

    for i in range(conf.active_node):
        re = requests.post(conf.cache_pool[i] + '/get_all')
        re = re.json()

        if re != None:
            id.extend(re["keys"])
            img.extend(re["items"])

        requests.post(conf.cache_pool[i] + '/clear')

    reallocate(id, img, new_pool)
    return

def add_node():
    # Add one node
    new_pool = min(conf.active_node + 1, 8)

    id = []
    img = []

    for i in range(conf.active_node):
        re = requests.post(conf.cache_pool[i] + '/get_all')
        re = re.json()

        if re != None:
            id.extend(re["keys"])
            img.extend(re["items"])

        requests.post(conf.cache_pool[i] + '/clear')

    reallocate(id, img, new_pool)
    return

def minus_node():
    # decrease one node
    new_pool = max(conf.active_node - 1, 1)

    id = []
    img = []

    for i in range(conf.active_node):
        re = requests.post(conf.cache_pool[i] + '/get_all')
        re = re.json()

        if re != None:
            id.extend(re["keys"])
            img.extend(re["items"])

        requests.post(conf.cache_pool[i] + '/clear')

    reallocate(id, img, new_pool)
    return

def reallocate(id, img, new_pool):
    # reallocate the content in the cache system
    conf.active_node = new_pool

    i = 0
    while i < len(id):
        hashed = hl.md5()
        hashed.update(bytes(id[i].encode('utf-8')))
        target = int(hashed.hexdigest(), 16) % conf.active_node

        j = {"key": id[i], "img": img[i]}
        requests.post(conf.cache_pool[target] + '/put', json=j)

        i += 1

    return

