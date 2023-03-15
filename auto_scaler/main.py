import sys, os
import threading
import time
import requests
from flask import request, jsonify
import flask as f
from auto_scaler import webapp

from host_map import *

# 1: auto on; 0: auto off
auto = 0
Max_MR_threshold = 0.5
Min_MR_threshold = 0.1

@webapp.before_first_request
def initial_settings():
    t = threading.Thread(target=check)
    t.start()

@webapp.route('/toggle_mode', methods=['POST', 'GET'])
def toggle_mode():
    global auto

    js = f.request.get_json(force=True)
    mode = js["mode"]
    # print(mode)

    auto = mode
    return jsonify({
        "message": "success",
    })

@webapp.route('/set_thresh', methods=['POST', 'GET'])
def set_thresh():
    global Max_MR_threshold
    global Min_MR_threshold

    js = f.request.get_json(force=True)
    Max_MR_threshold = js["Max_MR_threshold"]
    Min_MR_threshold = js["Min_MR_threshold"]

    print(Max_MR_threshold)
    print(Min_MR_threshold)

    return jsonify({
        "message": "success"
    })

def check():
    global auto
    global Max_MR_threshold
    global Min_MR_threshold

    while True:
        if auto == 1:
            j = {"metric": "miss_rate"}
            res = requests.post(image_storage + '/cw_get', json=j)
            res = res.json()

            miss = res['values'][-1]

            if miss > Max_MR_threshold:
                print("add node request")
                j_add = {"pool_update": "+"}
                res = requests.post(cache_pool_host + '/change_pool', json=j_add)
            elif miss < Min_MR_threshold:
                print("decrease node request")
                j_minus = {"pool_update": "-"}
                res = requests.post(cache_pool_host + '/change_pool', json=j_minus)

        time.sleep(60)

# while True:
#     check()
#     time.sleep(5)




