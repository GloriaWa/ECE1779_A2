import sys, os
import time
import requests
from flask import request, jsonify
from user_app import webapp

from host_map import *

# 1: auto on; 0: auto off
auto = 0

@webapp.route('/toggle_mode', methods=['POST'])
def toggle_mode():
    global auto

    mode = request.form.get('mode')
    auto = mode
    return

def check():
    global auto

    if auto == 1:
        j = {"metric": "miss_rate"}
        res = requests.post(image_storage + '/cw_get', json=j)
        miss = res['values'][-1]

        if miss > 0.5:
            j_add = {"pool_update": "+"}
            res = requests.post(cache_pool_host + '/change_pool', json=j_add)
        elif miss < 0.9:
            j_minus= {"pool_update": "-"}
            res = requests.post(cache_pool_host + '/change_pool', json=j_minus)

    # print("here")
    return

while True:
    check()
    time.sleep(5)




