import os, requests, base64, time, sys, shutil
from manager.MySQLconnect import get_db
from io import BytesIO
from matplotlib.figure import Figure

# all allowed extensions for the uploaded img
EXT = {'.txt', '.pdf', '.png', '.jpg', '.jpeg', '.gif'}

# This is a local running server
cache_host = "http://localhost:5001"

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

def set_cache_parameter(cap, strategy):
    """ Set cache parameters -> store them into the database, return the time of the inserted cache parameter """

    try:
        cnx = get_db()
        cursor = cnx.cursor(buffered=True)

        # EST time zone, need to deal with offset
        ctime = time.time() - 18000

        query_add = ''' INSERT INTO config (ctime, cap, strategy) VALUES (%s,%s,%s)'''
        cursor.execute(query_add, (ctime, cap, strategy))
        cnx.commit()
        return "success"

    except:
        return None

# def base64_img(filename):
#     """ Get the img and prepare it as base64 for the memcache to store """
#
#     with open(IMG_FOLDER + "/" + filename, "rb") as img_path:
#         img = img_path.read()
#         base64_img = base64.b64encode(img)
#     img = base64_img.decode('utf-8')
#     return img

def plot_graphs(data_x_axis, data_y_axis, y_label):

    # Plot
    fig = Figure()
    ax = fig.subplots()
    ax.plot(data_x_axis, data_y_axis)
    ax.set(xlabel='Time (every 5 seconds)', ylabel=y_label)

    # x-axis overlaps, to solve this problem: https://matplotlib.org/2.0.2/users/recipes.html
    fig.autofmt_xdate()

    # Save the img and put it on the UI: https://matplotlib.org/stable/gallery/user_interfaces/web_application_server_sgskip.html
    buf = BytesIO()
    fig.savefig(buf, format="png")
    plot = base64.b64encode(buf.getbuffer()).decode("ascii")

    return plot

