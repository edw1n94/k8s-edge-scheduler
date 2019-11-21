import k8s_manager,requests,json
import pythonping

data = {'client_ip': '192.168.1.1'}
headers = {'Content-Type': 'application/json; charset=utf-8'}



url = 'http://127.0.0.1:5001/scheduling_by_latency'
res = requests.post(url, headers=headers, data=json.dumps(data))
#res = requests.get(url, headers=headers, data=json.dumps(data))




print(json.dumps(res.text))
