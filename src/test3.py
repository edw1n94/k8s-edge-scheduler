import requests,json,time


data = {'client_ip': '192.168.1.110'}
headers = {'Content-Type': 'application/json; charset=utf-8'}



url = 'http://192.168.1.12:31271/count_hit'
res = requests.post(url, headers=headers, data=json.dumps(data))
#res = requests.get(url, headers=headers, data=json.dumps(data))
print(json.dumps(res.text))


start = time.time()
for i in range(0,1):
    res = requests.get(url, headers=headers, data=json.dumps(data))

end = time.time() - start

print(end)