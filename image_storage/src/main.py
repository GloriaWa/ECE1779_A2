from flask import jsonify, request
from image_storage.src import storageApp
from image_storage.src.utils import *

awsclient = AwsClient()


@storageApp.route('/test', methods=['POST'])
def test_status():
    status = db_status()
    mes = "db status error"
    if status == "available":
        mes = "success"
    elif status == "stopped":
        start_db()
    elif status == "not created":
        create_db()
    return jsonify({
        "message": mes
    })


@storageApp.route('/read/<string:key>', methods=['POST'])
def read(key):
    status = db_status()
    if status != "available":
        res = "Read db fail, DB Status error, Status is " + status
        jj = {"success": "false", "error": {"code": "servererrorcode", "message": res}}
        return jsonify(jj)
    cnx = get_db()
    cursor = cnx.cursor(buffered=True)
    query = "SELECT ifilename FROM mapping where ikey= %s"
    cursor.execute(query, (key,))

    if cursor._rowcount:
        filename = str(cursor.fetchone()[0])
        cnx.close()

        bfile = awsclient.s3_read(filename)
        if bfile is None:
            res = "file in db but not exist in S3"
            jj = {"success": "false", "error": {"code": "servererrorcode", "message": res}}
            return jsonify(jj)
        else:
            img = base64_img(bfile)

        jj = {"success": "true", "key": key, "content": img}
        return jsonify(jj)

    else:
        jj = {"success": "false", "error": {"code": "servererrorcode", "message": "key not exist"}}
        return jsonify(jj)


@storageApp.route('/write', methods=['POST'])
def write():
    try:
        j = {"success": "true"}
        key = request.form.get('key')
        file = request.files['file']
        filename = file.filename
        re = rds_write(key, filename)
        if re != "success":
            j = {"success": "false", "error": {"code": "servererrorcode", "message": re}}
        else:
            awsclient.s3_write(file, filename)
        return jsonify(j)
    except:
        j = {"success": "false", "error": {"code": "servererrorcode", "message": "image storage write fail"}}
        return jsonify(j)


@storageApp.route('/delete_all', methods=['POST'])
def delete_all():
    try:
        awsclient.s3_clear()
        re=rds_clear()
        j = {"success": "true"}
        if re != "success":
            j = {"success": "false", "error": {"code": "servererrorcode", "message": re}}
        return jsonify(j)
    except:
        j = {"success": "false","error": {"code": "servererrorcode", "message": "image storage delete fail"}}
        return jsonify(j)


@storageApp.route('/list', methods=['POST'])
def list_keys():
    status = db_status()
    if status != "available":
        j={"success": "false", "error": {"code": "servererrorcode", "message": "DB Status error, Status is " + status}}
        return jsonify(j)
    else:
        return jsonify({"success": "true", "keys": rds_list()})