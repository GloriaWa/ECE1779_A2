import requests, random, time
import matplotlib.pyplot as plt

user_url = "http://35.153.57.191:5000"
manager_url = "http://35.153.57.191:5001"

r= requests.post(manager_url + '/api/configure_cache',
                             params={'mode': 'manual', 'numNodes': 2, 'cacheSize': 3, 'policy': 'RR'})
print(r)
r=r.json()
print(r)