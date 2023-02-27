from Backend.src import backendApp

# @backendApp.route('/index')
# def index():  # put application's code here
#     return 'Index Page'

if __name__ == '__main__':
    backendApp.run('0.0.0.0',5001,debug=False,threaded=True)