import requests, random, time
import matplotlib.pyplot as plt

user_url = "http://35.153.57.191:5000"
manager_url = "http://35.153.57.191:5001"


def write(key):
    multipart_form_data = {
        'file': open(str(key) + ".png", "rb")
    }
    t = requests.post(user_url + "/api/upload", data={'key': key}, files=multipart_form_data).elapsed.total_seconds()
    return t


def read(key):
    return requests.post(user_url + "/api/key/" + str(key)).elapsed.total_seconds()


def get_nodes():
    r = requests.post(manager_url + "/api/getNumNodes")
    r = r.json()
    return r["numNodes"]


def get_rate(name):
    r = requests.post(manager_url + "/api/getRate?rate=" + name)
    r = r.json()
    return r["value"]


def cache_setting(num):
    # mode=auto&numNodes=5&cacheSize=5&policy=LRU&expRatio=2&shrinkRatio=2&maxMiss=0.5&minMiss=0.5
    r = requests.post(manager_url + "/api/configure_cache?" + "mode=manual&numNodes=" + str(num))
    r = r.json()
    return r


MaxNum = 30
policy = 0.5


# test constant
def plot_latency():
    latency_array = []
    for Num in range(1, MaxNum + 1, 4):
        RandomList = [random.random() for iter in range(Num)]
        latency = 0
        for x in RandomList:
            key = random.randint(1, 24)
            if x <= policy:
                latency += write(key)
            else:
                latency += read(key)
        latency_array.append(latency / Num)
    print(latency_array)
    plt.plot(range(1, MaxNum + 1, 4), latency_array)
    plt.title("50:50 w/r mode: manual, numNodes: 1to8, cacheSize: 3, policy: RR")
    plt.xlabel('number of request')
    plt.ylabel('average latency')
    plt.savefig('1to8_latency.jpg')
    plt.show()


def plot_throughput():
    tputarray = []
    for a in range(20):
        t_record = time.time() + 1
        tput = 0
        while time.time() < t_record:
            x = random.random()
            key = random.randint(1, 24)
            if x <= policy:
                write(key)
            else:
                read(key)
            tput += 1
        tputarray.append(tput)

    for a in range(20):
        if a != 0:
            tputarray[a] = tputarray[a] + tputarray[a - 1]
    print(tputarray)
    plt.plot(range(1, 21), tputarray)
    plt.title("50:50 w/r mode: manual, numNodes:1to8 , cacheSize: 3, policy: RR")
    plt.xlabel('time')
    plt.ylabel('Throughput')
    plt.savefig('1to8_Throughput.jpg')
    plt.show()


def auto_shrink():
    lnodes = []
    lmiss = []
    t_stop = time.time() + 7 * 60
    t_record = time.time() + 60
    while time.time() < t_stop:
        x = random.random()
        key = random.randint(1, 3)
        if x <= 0.2:
            write(key)
        else:
            read(key)
        time.sleep(5)
        if time.time() >= t_record:
            lnodes.append(get_nodes())
            lmiss.append(get_rate("miss"))
            print(lnodes,lmiss)
            t_record = time.time() + 60


def auto_grow():
    lnodes = []
    lmiss = []
    t_stop = time.time() + 10 * 60
    t_record = time.time() + 60
    while time.time() < t_stop:
        x = random.random()
        key = random.randint(1, 24)
        if x <= 0.8:

            write(key)
        else:
            read(key)
        time.sleep(2)
        if time.time() >= t_record:
            lnodes.append(get_nodes())
            lmiss.append(get_rate("miss"))
            print(lnodes, lmiss)
            t_record = time.time() + 60


auto_grow()
