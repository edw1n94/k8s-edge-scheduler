import k8s_manager,requests,json,yaml
import os

manager = k8s_manager.k8s_manager_obj()

node_list = manager.node_list

hello = open('../hello.yaml')
hello = yaml.load(hello)

#
print(hello['spec']['template']['spec'])
hello2 = open('../hello2.yaml')
hello2 = yaml.load(hello2)

print(hello2['spec']['template']['spec'])
#manager.create_pod_with_label_selector(body=hello)
data = {'client_ip': '8.8.8.8'}
headers = {'Content-Type': 'application/json; charset=utf-8'}
url = 'http://127.0.0.1:5001/scheduling_by_latency'
res = requests.post(url, headers=headers, data=json.dumps(data))
print(json.dumps(res.text))
