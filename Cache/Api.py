import flask as f
import OriginalCacheWrapper as Cache

from Cache import backendApp
from flask import jsonify
import mysql.connector
from flask import g
from Cache.Config import db_config

capacity = 12  # Cache initial capacity
# 'LUR' is the initial strategy

cw = Cache.CacheWrapper(capacity)


def connect_to_database():
    """ connect to the database based on the config info given in the config file """

    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])


def get_db():
    """ get the db """

    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db


def get_cache_parameter():
    """ Get the newest cache parameters from the database, return the resulting row from the database """

    try:
        cnx = get_db()
        cursor = cnx.cursor(buffered=True)

        query = '''SELECT * FROM config WHERE ctime = (SELECT MAX(ctime) FROM config LIMIT 1)'''
        cursor.execute(query)

        if (cursor._rowcount):
            cache_para = cursor.fetchone()
            return cache_para
        else:
            return None

    except:
        return None


def set_status(size, item_count, request_count, miss_count):
    """ Update a new set of memcache status data, insert the new data into the database """

    try:
        cnx = get_db()
        cursor = cnx.cursor(buffered=True)

        query_add = ''' INSERT INTO stats (size, item_count, request_count, miss_count) VALUES (%s,%s,%s,%s)'''
        cursor.execute(query_add, (size, item_count, request_count, miss_count))
        cnx.commit()
        return None

    except:
        return None


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
    """ put a new img into the memcache, the CacheWrapper will deal with possible deletes and updates in the memcache
    """

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
