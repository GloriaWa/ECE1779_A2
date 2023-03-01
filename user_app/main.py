import sys, os
import requests
from flask import render_template, request, jsonify
from user_app import webapp
from host_map import *

EXT = {'.png', '.jpg', '.jpeg', '.gif', '.ico'}


@webapp.before_first_request
def initial_settings():
    try:
        re = requests.post(image_storage + "/test")
        re = re.json()
        if re["message"] != "success":
            print(re["message"])
            sys.exit()
    except requests.ConnectionError as e:
        print(e)


@webapp.route('/')
@webapp.route('/home')
def home():
    return render_template("home.html")


@webapp.errorhandler(404)
def not_found(e):
    return render_template("home.html")


@webapp.route('/add_img', methods=['GET', 'POST'])
def add_img():
    if request.method == 'POST':
        key = request.form.get('key')
        file = request.files['file']
        if key == "" or key is None:
            return render_template("add_img.html", result="Missing key")

        name, ex = os.path.splitext(file.filename)
        if ex.lower() in EXT:
            try:
                re = requests.post(image_storage + "/write", data={'key': key}, files={'file': file})
            except requests.ConnectionError:
                return render_template("add_img.html", result="error connecting image storage")
            re = re.json()
            if re["success"] != "true":
                return render_template("add_img.html", result=re["error"]["message"])
            j = {"key": key}
            try:
                requests.post(cache_pool_host + '/invalidate', json=j)
            except requests.ConnectionError:
                return render_template("add_img.html", result="error connecting cache pool")

            return render_template("add_img.html", result="success")
        else:
            return render_template("add_img.html", result="Missing file or file with unsupported extension")
    return render_template("add_img.html")


@webapp.route('/show_image', methods=['GET', 'POST'])
def show_image():
    if request.method == 'GET':
        return render_template('show_image.html')

    else:
        key = request.form.get('key')
        j = {"key": key}
        try:
            res = requests.post(cache_pool_host + '/get', json=j)
        except requests.ConnectionError:
            return render_template('show_image.html', exists=False, img="error connecting cache pool")
        res = res.json()

        if res['message'] == 'miss':
            try:
                re = requests.post(image_storage + "/read/" + key)
            except requests.ConnectionError:
                return render_template('show_image.html', exists=False, img="error connecting image storage")
            re = re.json()
            if re["success"] != "true":
                return render_template('show_image.html', exists=False, img=re["error"]["message"])
            else:
                img = re["content"]
                j = {"key": key, "img": img}
                try:
                    requests.post(cache_pool_host + '/put', json=j)
                except requests.ConnectionError:
                    return render_template('show_image.html', exists=False, img="error connecting cache pool")

                return render_template('show_image.html', exists=True, img=img)
        else:
            return render_template('show_image.html', exists=True, img=res['img'])


@webapp.route('/key_list', methods=['GET', 'POST'])
def key_list():
    if request.method == 'POST':
        try:
            requests.post(cache_pool_host + '/clear')
        except requests.ConnectionError:
            return
        if request.form.get("clear_all") is not None:
            try:
                requests.post(image_storage + "/delete_all")
            except requests.ConnectionError:
                return

    try:
        re = requests.post(image_storage + "/list")
        re = re.json()
        db_keys = re["keys"]
        db_key_no = len(db_keys)
    except requests.ConnectionError:
        return

    try:
        j = {}
        res = requests.post(cache_pool_host + '/get_key_list', json=j)
        res = res.json()
        c_key_no = res['count']
        c_keys = res['keyList']
    except requests.ConnectionError:
        return

    if db_keys or c_keys:
        return render_template('key_list.html', db_keys=db_keys, db_key_no=db_key_no, c_keys=c_keys, c_key_no=c_key_no)
    else:
        return render_template('key_list.html')


# ________________________auto test api _________________________
@webapp.route('/api/delete_all', methods=['POST'])
def api_delete_all():
    try:
        requests.post(cache_pool_host + '/clear')
    except requests.ConnectionError as e:
        return jsonify(
            {"success": "false", "error": {"code": "servererrorcode", "message": "error connecting cache pool"}})
    try:
        re = requests.post(image_storage + "/delete_all")
        j = re.json()
        return jsonify(j)
    except requests.ConnectionError as e:
        return jsonify(
            {"success": "false", "error": {"code": "servererrorcode", "message": "error connecting image storage"}})


@webapp.route('/api/upload', methods=['POST'])
def upload():
    key = request.form.get('key')
    file = request.files['file']
    if key == "" or key is None:
        j = {"success": "false", "error": {"code": "servererrorcode", "message": "missing key"}}
        return jsonify(j)
    name, ex = os.path.splitext(file.filename)

    if ex.lower() in EXT:
        try:
            re = requests.post(image_storage + "/write", data={'key': key}, files={'file': file})
        except requests.ConnectionError:
            return jsonify(
                {"success": "false", "error": {"code": "servererrorcode", "message": "error connecting image storage"}})

        re = re.json()
        if re["success"] != "true":
            return jsonify(re)
        j = {"key": key}
        try:
            requests.post(cache_pool_host + '/invalidate', json=j)
            return jsonify({"success": "true", "key": key})
        except requests.ConnectionError:
            return jsonify(
                {"success": "false", "error": {"code": "servererrorcode", "message": "error connecting cache pool"}})

    else:
        return jsonify({"success": "false",
                        "error": {"code": "servererrorcode", "message": "Invalid file extension or missing file"}})


@webapp.route('/api/list_keys', methods=['POST'])
def list_keys():
    try:
        re = requests.post(image_storage + "/list")
        return jsonify(re.json())
    except requests.ConnectionError:
        return jsonify(
            {"success": "false", "error": {"code": "servererrorcode", "message": "error connecting image storage"}})


@webapp.route('/api/key/', methods=['POST'])
def key_not_given():
    jj = {"success": "false", "error": {"code": "servererrorcode", "message": "No key is given"}}
    return jsonify(jj)


@webapp.route('/api/key/<string:key>', methods=['POST'])
def single_key(key):
    j = {"key": key}
    try:
        res = requests.post(cache_pool_host + '/get', json=j)
    except requests.ConnectionError:
        return jsonify(
            {"success": "false", "error": {"code": "servererrorcode", "message": "error connecting cache pool"}})
    res = res.json()

    if res['message'] == 'miss':
        try:
            re = requests.post(image_storage + "/read/" + key)
        except requests.ConnectionError:
            return jsonify(
                {"success": "false", "error": {"code": "servererrorcode", "message": "error connecting image storage"}})
        re = re.json()
        if re["success"] != "true":
            return jsonify(re)
        else:
            img = re["content"]
            j = {"key": key, "img": img}
            try:
                requests.post(cache_pool_host + '/put', json=j)
            except requests.ConnectionError:
                return jsonify(
                    {"success": "false",
                     "error": {"code": "servererrorcode", "message": "error connecting icache pool"}})

            jj = {"success": "true", "key": key, "content": img}
            return jsonify(jj)

    else:
        j = {"success": "true", "key": key, "content": res['img']}
        return jsonify(j)
