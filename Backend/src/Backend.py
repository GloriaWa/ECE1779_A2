import flask as f
import Backend.src.CacheWrapper as Cache

from Backend.src import backendApp
from flask import jsonify
from Frontend.Utilities import get_cache_parameter, set_status

capacity = 12  # Cache initial capacity
# 'LUR' is the initial strategy

cw = Cache.CacheWrapper(capacity)

# @backendApp.route('/api/')
# def main():
#     return f.render_template("main.html")

@backendApp.route('/get', methods=['POST'])
def get():
    """ get an img based on a key, might cache hit or miss, if miss, the frontend will initialized a memcache update """

    js = f.request.get_json(force=True)
    key = js["key"]
    value = cw.get(key)

    if value != -1:
        message = "hit"
        return jsonify({"ikey": key,
                        "img": value,
                        "message": message
                        })
    else:
        message = "miss"
        return jsonify({"ikey": "",
                        "img": "",
                        "message": message
                        })

@backendApp.route('/put', methods=['POST'])
def put():
    """ put a new img into the memcache, the CacheWrapper will deal with possible deletes and updates in the memcache """

    js = f.request.get_json(force=True)
    key = js["key"]
    img = js["img"]
    cw.put(key, img)

    message = "ok"
    return jsonify({
                    "message": message
                    })

@backendApp.route('/clear', methods=['POST'])
def clear():
    """ clear the cache """

    cw.clear()

    message = "ok"
    return jsonify({
        "message": message
    })

@backendApp.route('/invalidate', methods=['POST'])
def invalidateKey():
    """ delete a specific key from the memcache if exist """

    js = f.request.get_json(force=True)
    cw.invalidate(js["key"])

    message = "ok"
    return jsonify({
        "message": message
    })

@backendApp.route('/get_key_list', methods=['POST'])
def getKeyList():
    """ return all keys stored in the memcache """

    count = len(cw.memcache)

    li = []
    for key in cw.memcache:
        li.append(key)

    message = "success"
    return jsonify({"count": count,
                    "keyList": li,
                    "message": message
                    })

@backendApp.route('/refreshConfiguration', methods=['POST'])
def refreshConfiguration():
    """ based on the user request, reset the memcache parameters (size and strategy) """

    cache_params = get_cache_parameter()

    cap = cache_params[2]
    replace = cache_params[3]

    cw.refreshConfigurations(cap, replace)
    message = "ok"
    return jsonify({
        "message": message
    })

@backendApp.route('/stats', methods=['POST'])
def heartBeatStatus():
    """ method that return the current memcache statistics information (will be stored in the db every 5 seconds) """

    item_count = len(cw.memcache)
    request_count = cw.accessCount
    miss_count = cw.accessCount - cw.hit
    size = cw.getSize()

    set_status(size, item_count, request_count, miss_count)
    message = "ok"
    return jsonify({
        "message": message
    })



# @backendApp.route('/api/stats', methods=['GET'])
# def currentStats():
#     return backendApp.response_class(
#         response=f.json.dumps(cw.displayStats()),
#         status=200,
#         mimetype='application/json'
#     )
#
#
# @backendApp.route('/api/cacheKeys', methods=['GET'])
# def cacheKeys():
#     return backendApp.response_class(
#         response=f.json.dumps(cw.displayAllKeys()),
#         status=200,
#         mimetype='application/json'
#     )
