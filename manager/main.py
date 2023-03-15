import threading
import requests, datetime
import sys, os
import manager.config as conf
import flask as f
import hashlib as hl
from flask import render_template, request, g, jsonify
import time

from manager.MySQLconnect import *
from manager.Utilities import *
from manager import webapp
from manager.pool_manage import *
from host_map import *


@webapp.before_first_request
def initial_settings():
    # set_cache_parameter(conf.capacity, conf.strategy)
    t = threading.Thread(target=pollStatus)
    t.start()

def pollStatus():
    """ When the server is up, call backend every 5 seconds. The backend will upload its status information to the db, and this info is used for the statistics """
    clear_count = 0
    while True:
        item_count = 0
        request_count = 0
        miss_count = 0
        size = 0

        for i in range(conf.active_node):
            res = requests.post(conf.cache_pool[i] + '/stats')
            # print(conf.cache_pool[i]+ '/stats')

            res = res.json()

            item_count += res["item_count"]
            request_count += res["request_count"]
            miss_count += res["miss_count"]
            size += res["size"]

        miss_rate = 0
        hit_rate = 1
        if request_count != 0:
            miss_rate = miss_count / request_count
            hit_rate = 1 - miss_rate

        j = {"miss_rate": miss_rate, "hit_rate": hit_rate, "num_items": item_count,"size_of_items": size / (1024 * 1024), "num_requests": request_count}
        re = requests.post(image_storage + '/cw_put', json=j)

        if clear_count < 12:
            clear_count += 1
        else:
            clear_count = 0
            for i in range(conf.active_node):
                res = requests.post(conf.cache_pool[i] + '/clear_record')

        time.sleep(5)

@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@webapp.route('/')
@webapp.route('/home')
def home():
    """ Home page, has the nevigatoin bar to all other functoinalities """
    return render_template("home.html")

@webapp.errorhandler(404)
def not_found(e):
    return render_template("home.html")

@webapp.route('/cache_stats')
def cache_stats():
    """ show the cache statistics page, and graphs that show the parameters of the cache will be shown """

    # get ready for plotting
    # xx = []
    yy = {}

    j = {"metric": "number_of_items_in_cache"}
    res = requests.post(image_storage + '/cw_get', json=j)
    res = res.json()
    yy['item_count'] = res["values"].copy()

    j = {"metric": "number_of_request_per_second"}
    res = requests.post(image_storage + '/cw_get', json=j)
    res = res.json()
    yy['request_count'] = res["values"].copy()

    j = {"metric": "hit_rate"}
    res = requests.post(image_storage + '/cw_get', json=j)
    res = res.json()
    yy['hit_rate'] = res["values"].copy()

    j = {"metric": "miss_rate"}
    res = requests.post(image_storage + '/cw_get', json=j)
    res = res.json()
    yy['miss_rate'] = res["values"].copy()

    j = {"metric": "total_size_of_items_in_cache"}
    res = requests.post(image_storage + '/cw_get', json=j)
    res = res.json()
    yy['cache_size'] = res["values"].copy()

    xx = [i for i in range(len(yy['item_count']))]
    # print(xx)
    # print(yy['item_count'])

    # plot the graphs, the plotted graphs will be shown in the page, and graphs are updated every 5 seconds, since new data will be pushed to the db every 5 seconds
    plots = {}
    for i, values in yy.items():
        plots[i] = plot_graphs(xx, values, i)

    return render_template('cache_stats.html', cache_count_plot=plots['item_count'], cache_size_plot=plots['cache_size'], request_count_plot=plots['request_count'], hit_count_plot=plots['hit_rate'], miss_count_plot=plots['miss_rate'])

@webapp.route('/memcache_config', methods=['GET', 'POST'])
def memcache_config():
    """ take the request from the user to reconfigure the memcache, size and strategy can be changed
     in addition, the user can also clear the memcache, or clear all the data in the file system, database, and memcache
     (not including the history stats data and history config data in the db) """

    global cache_host
    cache_para = get_cache_parameter()

    if cache_para != None:
        capacity = int(cache_para[2])
        stra = cache_para[3]
    else:
        # Cannot query db, set to default initial value
        capacity = 12
        stra = "LRU"

    if request.method == 'GET':
        return render_template('memcache_config.html', capacity=capacity, strategy=stra)

    # POST, need to do some work
    else:
        # if request to clear the cache
        if request.form.get("clear_cache") != None:
            for i in range(conf.active_node):
                requests.post(conf.cache_pool[i] + '/clear')

            return render_template('memcache_config.html', capacity=capacity, strategy=stra, status="mem_clear")

        # else if request to clear ALL
        elif request.form.get("clear_all") != None:
            for i in range(conf.active_node):
                requests.post(conf.cache_pool[i] + '/clear')

            requests.post(image_storage + '/delete_all')
            return render_template('memcache_config.html', capacity=capacity, strategy=stra, status="all_clear")

        # else, take the new cache parameters
        else:
            new_cap = request.form.get('capacity')
            # log ##########################
            # print(new_cap)

            if new_cap.isdigit() and int(new_cap) <= 20:

                strategy_selected = request.form.get('strategy')
                if strategy_selected == "Least Recently Used":
                    new_strategy = "LRU"
                else:
                    new_strategy = "RR"

                status = set_cache_parameter(int(new_cap), new_strategy)

                # if successs
                if status != None:
                    for i in range(conf.active_node):
                        j = {"size": int(new_cap), "strategy": new_strategy}
                        res = requests.post(conf.cache_pool[i] + '/refreshConfiguration', json=j)

                        if res.json()['message'] != 'ok':
                            return render_template('memcache_config.html', capacity=capacity, strategy=stra, status="fail")

                    return render_template('memcache_config.html', capacity=new_cap, strategy=new_strategy, status="suc")

            # Error happen
            return render_template('memcache_config.html', capacity=capacity, strategy=stra, status="fail")


@webapp.route('/get_key_list', methods=['POST'])
def get_key_list():

    keyList = []
    count = 0

    for i in range(conf.active_node):
        re = requests.post(conf.cache_pool[i] + '/get_key_list')
        re = re.json()

        keyList.extend(re["keyList"])
        count += re["count"]

    j = {"keyList": keyList, "count": count}
    return jsonify(j)



@webapp.route('/get', methods=['POST'])
def get():
    js = f.request.get_json(force=True)
    key = js["key"]

    hashed = hl.md5()
    hashed.update(bytes(key.encode('utf-8')))
    target = int(hashed.hexdigest(), 16) % conf.active_node

    j = {"key": key}
    res = requests.post(conf.cache_pool[target] + '/get', json=j)
    res = res.json()

    return res

@webapp.route('/put', methods=['POST'])
def put():
    js = f.request.get_json(force=True)
    key = js["key"]
    img = js["img"]

    hashed = hl.md5()
    hashed.update(bytes(key.encode('utf-8')))
    target = int(hashed.hexdigest(), 16) % conf.active_node

    j = {"key": key, "img": img}
    res = requests.post(conf.cache_pool[target] + '/put', json=j)
    res = res.json()

    return res


@webapp.route('/invalidate', methods=['POST'])
def invalidate():
    ############ need optimization
    js = f.request.get_json(force=True)
    for i in range(conf.active_node):
        requests.post(conf.cache_pool[i] + '/invalidate', json=js)
    return jsonify({
                    "message": "success"
                    })


@webapp.route('/change_pool', methods=['GET', 'POST'])
def change_pool():
    update = f.request.get_json(force=True)["pool_update"]

    if update == '+':
        # if pool_update_validate():
        double_node()
    else:
        divide_node()

    j = {"node_num": conf.active_node}
    requests.post(userApp + '/cache_pool_change', json=j)

    return jsonify({
        "message": "success"
    })

@webapp.route('/pool_config', methods=['GET', 'POST'])
def pool_config():

    if request.method == 'GET':
        return render_template('pool_config.html', node_num=conf.active_node, mode=str(conf.mode))

    if request.form.get("option") != None:
        mode = request.form.get("option")
        if mode == "1":
            j = {"mode": 1}
            conf.mode = 1
            res = requests.post(autoscaler + '/toggle_mode', json=j)

            res = res.json()
            print(res)

            return render_template('pool_config.html', node_num=conf.active_node, mode=str(conf.mode), mode_mes="suc")
        elif mode == "0":
            j = {"mode": 0}
            conf.mode = 0
            res = requests.post(autoscaler + '/toggle_mode', json=j)
            return render_template('pool_config.html', node_num=conf.active_node, mode=str(conf.mode), mode_mes="suc")
        return render_template('pool_config.html', node_num=conf.active_node, mode=str(conf.mode), mode_mes="fail")

    if request.form.get("increase_node") != None:
        add_node()
    elif request.form.get("decrease_node") != None:
        minus_node()

    j = {"node_num": conf.active_node}
    requests.post(userApp + '/cache_pool_change', json=j)

    return render_template('pool_config.html', node_num=conf.active_node, mode=str(conf.mode), mes="suc")

# ########### add buttons
@webapp.route('/set_paras', methods=['GET', 'POST'])
def set_paras():
    conf.Max_MR_threshold = request.form.get("Max_MR_threshold")
    conf.Min_MR_threshold = request.form.get("Min_MR_threshold")
    conf.Ratio_expand_pool = request.form.get("Ratio_expand_pool")
    conf.Ratio_shrink_pool = request.form.get("Ratio_shrink_pool")

    j = {"Max_MR_threshold": conf.Max_MR_threshold, "Min_MR_threshold": conf.Min_MR_threshold}
    res = requests.post(autoscaler + '/set_thresh', json=j)

    return jsonify({
        "message": "success"
    })


# ---------------- Test Apis-------------------
@webapp.route('/api/getNumNodes', methods=['POST'])
def getNumNodes():
    return jsonify({
            "success": "true",
            "numNodes": conf.active_node
        })

@webapp.route('/api/getRate', methods=['POST'])
def getRate():
    args = request.args
    rate = args.get('rate')
    print(rate)

    if rate == "miss":
        j = {"metric": "miss_rate"}
        res = requests.post(image_storage + '/cw_get', json=j)
        res = res.json()

        return jsonify({
                "success": "true",
                "rate":rate,
                "value": res["values"][-1]
            })

    elif rate == "hit":
        j = {"metric": "hit_rate"}
        res = requests.post(image_storage + '/cw_get', json=j)
        res = res.json()

        return jsonify({
            "success": "true",
            "rate": rate,
            "value": res["values"][-1]
        })

@webapp.route('/api/configure_cache', methods=['POST'])
def configCache():
    args = request.args
    print(args)

    mode = args.get('mode')
    numNodes = args.get('numNodes')
    cacheSize = args.get('cacheSize')
    policy = args.get('policy')
    expRatio = args.get('expRatio')
    shrinkRatio = args.get('shrinkRatio')
    maxMiss = args.get('maxMiss')
    minMiss = args.get('minMiss')
    all_json = {"success": "true"}

    if mode != None:
        if mode == "manual":
            j = {"mode": 0}
            conf.mode = 0
            res = requests.post(autoscaler + '/toggle_mode', json=j)
        elif mode == "auto":
            j = {"mode": 1}
            conf.mode = 1
            res = requests.post(autoscaler + '/toggle_mode', json=j)
        all_json["mode"] = mode

    if numNodes != None:
        set_node(int(numNodes))
        all_json["numNodes"] = int(numNodes)

    cache_para = get_cache_parameter()
    if cache_para != None:
        capacity = int(cache_para[2])
        stra = cache_para[3]
    else:
        # Cannot query db, set to default initial value
        capacity = 12
        stra = "LRU"

    if cacheSize != None:
        # Due to we use number of items in the mencache, get the average value based on the memory size
        capacity = int(cacheSize)
        all_json["cacheSize"] = int(cacheSize)

    if policy != None:
        stra = policy
        all_json["policy"] = policy

    status = set_cache_parameter(capacity, stra)
    for i in range(conf.active_node):
        j = {"size": capacity, "strategy": stra}
        res = requests.post(conf.cache_pool[i] + '/refreshConfiguration', json=j)

    if expRatio != None:
        conf.Ratio_expand_pool = float(expRatio)
        print("EEEEEEEEEEEEEEEEEEEEEEE" + str(conf.Ratio_expand_pool))
        all_json["expRatio"] = expRatio

    if shrinkRatio != None:
        conf.Ratio_shrink_pool = float(shrinkRatio)
        print("SSSSSSSSSSSSSSSSSSSS" + str(conf.Ratio_shrink_pool))
        all_json["shrinkRatio"] = shrinkRatio

    if maxMiss != None:
        conf.Max_MR_threshold = float(maxMiss)
        all_json["maxMiss"] = maxMiss

    if minMiss != None:
        conf.Min_MR_threshold = float(minMiss)
        all_json["minMiss"] = minMiss

    j = {"Max_MR_threshold": conf.Max_MR_threshold, "Min_MR_threshold": conf.Min_MR_threshold}
    res = requests.post(autoscaler + '/set_thresh', json=j)

    print(all_json)
    return jsonify(all_json)

@webapp.route('/api/delete_all', methods=['POST'])
def deleteAll():

    for i in range(conf.active_node):
        requests.post(conf.cache_pool[i] + '/clear')

    requests.post(image_storage + '/delete_all')

    return jsonify({
            "success": "true",
        })





# @webapp.route('/toggle_auto_mode', methods=['GET', 'POST'])
# def toggle_auto_mode():
#     if request.form.get("manual_mode") != None:
#         j = {"mode": 0}
#         conf.mode = 0
#         requests.post(autoscaler + '/toggle_mode', json=j)
#
#     elif request.form.get("auto_mode") != None:
#         j = {"mode": 1}
#         conf.mode = 1
#         requests.post(autoscaler + '/toggle_mode', json=j)
#
# @webapp.route('/clear_cache', methods=['GET', 'POST'])
# def clear_cache():
#     for i in range(conf.active_node):
#         requests.post(conf.cache_pool[i] + '/clear')
#     return # render page
#
# @webapp.route('/clear_all', methods=['GET', 'POST'])
# def clear_all():
#     requests.post(image_storage + '/delete_all')
#     for i in range(conf.active_node):
#         requests.post(conf.cache_pool[i] + '/clear')
#     return # render page
#














######### auto test api #########
""" The following are apis that only used in auto testing, they are NOT used when normally running the application on the browser """
#
# @webapp.route('/api/delete_all', methods=['POST'])
# def api_delete_all():
#     requests.post(cache_host + '/clear')
#     cfolder = clear_folder()
#     cdb = clear_db()
#
#     j = {"success": "true"}
#     return (jsonify(j))
#
# @webapp.route('/api/upload', methods=['POST'])
# def upload():
#     try:
#         key = request.form.get('key')
#         status = save_image(request, key)
#
#         if status == "invalid" or status == "fail":
#             j = {"success": "false", "error": {"code": "servererrorcode", "message": "Failed to upload the image"}}
#             return (jsonify(j))
#
#         j = {"success": "true", "key": key}
#         return jsonify(j)
#
#     except Exception as e:
#         j = {"success": "false", "error": {"code": "servererrorcode", "message": e}}
#         return (jsonify(j))
#
# @webapp.route('/api/list_keys', methods=['POST'])
# def list_keys():
#     try:
#         cnx = get_db()
#         cursor = cnx.cursor()
#         query = "SELECT ikey FROM img"
#         cursor.execute(query)
#
#         keys = []
#         for key in cursor:
#             keys.append(key[0])
#         cnx.close()
#
#         j = {"success": "true", "keys": keys}
#         return jsonify(j)
#
#     except Exception as e:
#         j = {"success": "false", "error": {"code": "servererrorcode", "message": e}}
#         return (jsonify(j))
#
# @webapp.route('/api/key/<string:key_value>', methods=['POST'])
# def single_key(key_value):
#     try:
#         if key_value == "":
#             jj = {"success": "false", "error": {"code": "servererrorcode", "message": "No such key"}}
#             return (jsonify(jj))
#
#         j = {"key": key_value}
#         res = requests.post('http://localhost:5001/get', json=j)
#         res = res.json()
#
#         # if not in the cache -> cache miss!
#         if (res['message'] == 'miss'):
#             cnx = get_db()
#             cursor = cnx.cursor(buffered=True)
#             query = "SELECT ipath FROM img where ikey= %s"
#             cursor.execute(query, (key_value,))
#
#             # if the required img is in the db, get it / or else, error
#             if (cursor._rowcount):
#                 img_ = str(cursor.fetchone()[0])
#
#                 # Need to close the db connection sooner!!! ********
#                 cnx.close()
#
#                 img = base64_img(img_)
#                 j = {"key": key_value, "img": img}
#                 res = requests.post(cache_host + '/put', json=j)
#
#                 jj = {"success": "true", "key": key_value, "content": img}
#                 return (jsonify(jj))
#
#             # the required img is not in the db
#             else:
#                 jj = {"success": "false", "error": {"code": "servererrorcode", "message": "No such key"}}
#                 return (jsonify(jj))
#
#         # cache hit
#         else:
#             j = {"success": "true", "key": key_value, "content": res['img']}
#             return jsonify(j)
#
#     except Exception as e:
#         f = {"success": "false", "error": {"code": "servererrorcode", "message": e}}
#         return (jsonify(f))
#

