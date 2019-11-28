

def distribute_round_robin(replicas,node_list,quota_list):

    index_replicas = 0
    index_quota_list = 0

    while index_replicas < replicas:
        quota_list[index_quota_list] += 1
        index_replicas += 1
        index_quota_list += 1

        if index_replicas % len(quota_list) == 0:
            index_quota_list = 0


    return quota_list



def distribute_weighted_scoring(replicas,require_resources,latency_list,k8s_manager):

    # 초기화
    filtered_node = []

    k8s_manager.update_metrics()
    node_list = k8s_manager.node_list

    #

    for node in node_list:
        if node.host_name != 'k8s-master-node' and node.host_name in latency_list.keys():
            filtered_node.append({'host_name': node.host_name, 'cpu': node.max_cpu - node.cpu, 'memory': node.max_memory - node.memory,
                'latency': latency_list[node.host_name]['latency'], 'deploy': 0})

    sorted_list = sorted(filtered_node, key=lambda a: a['latency'])
    for i in range(0, replicas):
        for node in sorted_list:
            if node['latency'] >= require_resources['latency']:
                score = 0
            else:
                score = node['cpu'] / require_resources['cpu']
                score *= node['memory'] / require_resources['memory']

                if sorted_list.index(node) / len(filtered_node) <= 0.2:
                    score *= 2.0
                elif sorted_list.index(node) / len(filtered_node) <= 0.5:
                    score *= 1.2

                node['score'] = score

        # Get Best Node
        best_node = sorted_list[0]
        for node in sorted_list:
            if best_node['score'] < node['score']:
                best_node = node

        # Resource Update
        best_node['deploy'] += 1
        best_node['cpu'] -= require_resources['cpu']
        best_node['memory'] -= require_resources['memory']

    return sorted_list

def split_deployment(quota_list, deployment_list, ):
    if len(quota_list) != len(deployment_list):
        return deployment_list

    index = 0
    for item in quota_list:
        deployment_list[index]['spec']['replicas'] = item['deploy']
        deployment_list[index]['metadata']['name'] = deployment_list[index]['metadata']['name'] + str(index)
        deployment_list[index]['spec']['template']['spec']['nodeSelector']['kubernetes.io/hostname'] = item['host_name']
        #de5ployment_list[index]['spec']['selector']['matchLabels']['app.kubernetes.io/name'] = deployment_list[index]['spec']['selector']['matchLabels']['app.kubernetes.io/name'] + str(index)
        #deployment_list[index]['spec']['template']['metadata']['labels']['app.kubernetes.io/name'] =  deployment_list[index]['spec']['template']['metadata']['labels']['app.kubernetes.io/name']  + str(index)
        index += 1

    return deployment_list

def rank_by_resources(node_list,available_resources):

    best = node_list[0]
    for node in node_list:
        if available_resources[node]['resources_usage_rate'] > available_resources[best]['resources_usage_rate']:
            best = node

    return best

def get_resources_usage_rate(available_resources):

    for item in available_resources.values():
        item['resources_usage_rate'] = round((item['cpu'] / item['max_cpu']) * (item['memory'] / item['max_memory']),2)

    return available_resources


