import k8s_manager,json,yaml,copy
import requests as req
import operator

manager = k8s_manager.k8s_manager_obj()

node_list = manager.node_list
replicas = 20
quota_list = [0 for i in range(0,len(node_list))]


latency_list = {'k8s-master-node':5.14,'k8s-worker-node0':3.81,'k8s-worker-node1':3.13,'k8s-worker-node2':6.55,'k8s-worker-node3':2.91}
require_resources = {'cpu':200,'memory':200,'latency':7}

filtered_node = []

for node in node_list:
    filtered_node.append({'host_name':node.host_name,'cpu':node.max_cpu-node.cpu,'memory':node.max_memory-node.memory,'latency':latency_list[node.host_name],'deploy':0})

sorted_list = sorted(filtered_node,key=lambda a:a['latency'])


for i in range(0,20):
    for node in sorted_list:
        if node['latency'] >= require_resources['latency']:
            score = 0
        else:
            score = node['cpu'] / require_resources['cpu']
            score *= node['memory'] / require_resources['memory']

            if sorted_list.index(node) / len(filtered_node) <= 0.2:
                score *= 1.3
            elif sorted_list.index(node) / len(filtered_node) <= 0.5:
                score *= 1.1
            else:
                score *= 0.8

            node['score'] = score

    #Get Best Node
    best_node = sorted_list[0]
    for node in sorted_list:
        if best_node['score'] < node['score']:
            best_node = node

    # Resource Update
    best_node['deploy'] += 1
    best_node['cpu'] -= require_resources['cpu']
    best_node['memory'] -= require_resources['memory']


for node in sorted_list:
    print(node)

