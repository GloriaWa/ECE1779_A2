import threading
import requests, datetime
import sys, os
import manager.config as conf
from flask import render_template, request, g, jsonify
import hashlib as hl

from manager.Utilities import *
from manager import webapp
from host_map import *

# Max_MR_threshold = 0.5
# Min_MR_threshold = 0.1
# Ratio_expand_pool = 2
# Ratio_shrink_pool = 0.5

def pool_update_validate():
    # Check if at least one of the cache node is full, else, add node request invalid

    for i in range(conf.active_node):
        re = requests.post(conf.cache_pool[i] + '/get_key_list')
        re = re.json()

        count = re["count"]

        if count == conf.capacity:
            return True

    return False

def set_node(num):
    if num < 1 or num > 8:
        return "fail"

    new_pool = num

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


def double_node():
    # Double the node
    print(conf.Ratio_expand_pool)

    new_pool = min(conf.Ratio_expand_pool * conf.active_node, 8)

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
    print(conf.Ratio_shrink_pool)

    new_pool = max(conf.active_node // conf.Ratio_shrink_pool, 1)

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

