from image_storage.src.MySQLconnect import *
from image_storage.src.awsclient import *
import base64


def db_status():
    try:
        client = boto3.client('rds')
        response = client.describe_db_instances()
        instance_status = {}
        for resp in response['DBInstances']:
            instance_status[resp['DBInstanceIdentifier']] = resp['DBInstanceStatus']
        if db_name in instance_status:
            return instance_status[db_name]
        else:
            return "not created"
    except ClientError as e:
        raise e


def create_db():
    status = db_status()
    if status != "not created":
        return "DB already exit, Status is " + status

    client = boto3.client('rds')
    response = client.create_db_instance(
        AllocatedStorage=5,
        DBInstanceClass='db.t2.micro',
        DBInstanceIdentifier=db_name,
        Engine='MySQL',
        MasterUserPassword=pswd,
        MasterUsername=user,
        AvailabilityZone='us-east-1a',
    )
    return response


def stop_db():
    status = db_status()
    if status != "available":
        return "DB Status error, Status is " + status
    client = boto3.client('rds')
    response = client.stop_db_instance(
        DBInstanceIdentifier=db_name,
    )
    return response


def start_db():
    status = db_status()
    if status != "stopped":
        return "DB Status error, Status is " + status

    client = boto3.client('rds')
    response = client.start_db_instance(
        DBInstanceIdentifier=db_name
    )
    return response


def delete_db():
    status = db_status()
    if status == "not created" or "deleting":
        return "DB Status error, Status is " + status
    client = boto3.client('rds')
    response = client.delete_db_instance(
        DBInstanceIdentifier=db_name,
        SkipFinalSnapshot=True,
    )
    return response


def rds_write(key, filename):
    """ Write img to the database """
    status = db_status()
    if status != "available":
        return "DB Status error, Status is " + status

    # check if already exist in the database, if so, need to delete the old one
    try:
        cnx = get_db()
        cursor = cnx.cursor(buffered=True)
        q_exist = "SELECT EXISTS(SELECT ikey FROM mapping WHERE ikey=(%s))"
        cursor.execute(q_exist, (key,))

        for i in cursor:
            if i[0] == 1:
                q_delete = '''DELETE FROM mapping WHERE ikey=%s'''
                cursor.execute(q_delete, (key,))
                break

        # Insert the new img to the database
        q_add = ''' INSERT INTO mapping (ikey, ifilename) VALUES (%s, %s)'''
        cursor.execute(q_add, (key, filename))
        cnx.commit()
        cnx.close()
        return "success"
    except:
        return "db write fail"


def rds_read(key):
    status = db_status()
    if status != "available":
        print("Read db fail, DB Status error, Status is " + status)
        return
    cnx = get_db()
    cursor = cnx.cursor(buffered=True)
    query = "SELECT ifilename FROM mapping where ikey= %s"
    cursor.execute(query, (key,))

    if cursor._rowcount:
        filename = str(cursor.fetchone()[0])

        # Need to close the db connection sooner!!! ********
        cnx.close()
        return filename
    else:
        print("Read db fail,No such key")
        return


def rds_list():
    status = db_status()
    if status != "available":
        return "DB Status error, Status is " + status
    cnx = get_db()
    cursor = cnx.cursor()
    query = "SELECT ikey FROM mapping"
    cursor.execute(query)
    db_keys = []

    for i in cursor:
        db_keys.append(i[0])
    cnx.close()
    return db_keys


def rds_clear():
    status = db_status()
    if status != "available":
        return "DB Status error, Status is " + status
    try:
        cnx = get_db()
        cursor = cnx.cursor(buffered=True)

        query_delete = '''DELETE FROM mapping'''
        cursor.execute(query_delete)
        cnx.commit()
        return "success"

    except:
        return "db clear fail"


def base64_img(bfile):
    """Accept byte like object and encode to base64"""
    b64_img = base64.b64encode(bfile)
    img = b64_img.decode('utf-8')
    return img
