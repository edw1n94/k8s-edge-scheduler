import requests,json
import time


data = {'client_ip': '121.162.16.215'}
headers = {'Content-Type': 'application/json; charset=utf-8'}



#url = 'http://127.0.0.1:5001/scheduling_by_latency'
#res = requests.post(url, headers=headers, data=json.dumps(data))
#res = requests.get(url)




start = time.time()

url = 'http://10.99.244.160:80/get_hit'
for i in range(1,1000):
    res = requests.get(url)

print("time : ",time.time() - start)


