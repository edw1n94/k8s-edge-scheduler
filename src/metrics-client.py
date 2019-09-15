import k8s_manager,requests,json


manager = k8s_manager.k8s_manager_obj()

node_list = manager.node_list

data = {'client_ip': '8.8.8.8'}
headers = {'Content-Type': 'application/json; charset=utf-8'}

url = 'http://127.0.0.1:5000/get_latency_from_client'
res = requests.post(url, headers=headers, data=json.dumps(data))
print(res.text)