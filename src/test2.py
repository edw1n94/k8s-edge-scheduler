from flask import Flask, request, json
from flask_restful import reqparse, abort, Api, Resource
import k8s_manager
import socket, requests as req, json, yaml, re, copy
import k8s_distribute_pods


latency = {}
latency2 = {}
require_latency = 10 # ms

k8s_manager_obj = k8s_manager.k8s_manager_obj()
headers = {'Content-Type': 'application/json; charset=utf-8'}
require_resources = {'cpu': 100, 'memory': 100,'latency' : require_latency}

content = {'client_ip':'192.168.0.1'}

# {'k8s-worker-node1':{'type':'InternalIP,'ip':ip}}
for node in k8s_manager_obj.node_list:
    if node.status and node.latency_collector_ip is not None:
        url = 'http://' + node.latency_collector_ip + ':' + node.latency_collector_port + '/get_latency'
        res = req.post(url, headers=headers, data=json.dumps(content))
        print("node name : {} latency : {}".format(node.host_name, float(re.findall("\d+",res.text)[0] + '.'+ re.findall("\d+",res.text)[1])))
        if(float(re.findall("\d+",res.text)[0] + '.'+ re.findall("\d+",res.text)[1])):
            latency[node.host_name] = {'type':'InternalIP','latency':float(re.findall("\d+",res.text)[0] + '.'+ re.findall("\d+",res.text)[1])}

latency, best_node,require_latency = k8s_manager_obj.get_best_node(latency,require_latency)

for node in k8s_manager_obj.node_list:
    if node is not best_node and node.host_name != 'k8s-master-node':
        data = {'client_ip':node.address}
        res = req.post('http://' + best_node.latency_collector_ip + ':' + best_node.latency_collector_port + '/get_latency',headers=headers,data=json.dumps(data))
        if (float(re.findall("\d+", res.text)[0] + '.' + re.findall("\d+", res.text)[1]) < require_latency):
            latency[node.host_name] = {'type':'InternalIP','latency':float(re.findall("\d+", res.text)[0] + '.' + re.findall("\d+", res.text)[1]) + latency[best_node.host_name]['latency']}



        if node.external_ip is not None:
            data = {'client_ip':node.external_ip}
            res = req.post('http://' + best_node.latency_collector_ip + ':' + best_node.latency_collector_port + '/get_latency',headers=headers, data=json.dumps(data))
            node_latency = float(re.findall("\d+", res.text)[0] + '.' + re.findall("\d+", res.text)[1])
            if node_latency < require_latency:
                if latency[node.host_name] is None or node_latency < latency[node.host_name]['latency'] :
                    latency[node.host_name]['latency'] = node_latency
                    latency[node.host_name]['type'] = 'ExternalIP'


sorted_list = k8s_distribute_pods.distribute_weighted_scoring(20,require_resources,latency,k8s_manager_obj)


'''
 for node in k8s_manager_obj.node_list:
            if node.host_name == best[0]:
                url = 'http://' + node.latency_collector_ip + ':' + node.latency_collector_port + '/get_latency'
                for node2 in k8s_manager_obj.node_list:
                    if node2.host_name != node.host_name and node2.host_name != 'k8s-master-node':
                        data = {'client_ip':node2.address}
                        res = req.post(url, headers=headers, data=json.dumps(data))
                        if (float(re.findall("\d+", res.text)[0] + '.' + re.findall("\d+", res.text)[1]) + best[1] < require_latency):
                            latency2[node.host_name] = float(re.findall("\d+", res.text)[0] + '.' + re.findall("\d+", res.text)[1])

                    #if has ExternalIP
                    if node2.external_ip is not None and node2.host_name != node.host_name:
                        data = {'client_ip': node2.external_ip}
                        res = req.post(url, headers=headers, data=json.dumps(data))
                        if (float(re.findall("\d+", res.text)[0] + '.' + re.findall("\d+", res.text)[1]) + best[1] < require_latency):
                            latency2[node.host_name] = float(re.findall("\d+", res.text)[0] + '.' + re.findall("\d+", res.text)[1])

        print(latency2)
'''



