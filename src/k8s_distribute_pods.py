import k8s_manager

#replicas = 20
#node_list = ['k8s-worker-node0','k8s-worker-node3','k8s-worker-node2','k8s-worker-node1','k8s-worker-node4']
#quota_list = [0 for i in range(0,len(node_list))]
#weight_list = [0.3,0.1,0.1]
#require_resources = {'cpu':200,'memory':200}

manager = k8s_manager.k8s_manager_obj()

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


#weight list에 담긴 가중치 만큼 우선 할당
# 0.3 = 30% 우선배치, 나머지는 Round Robin
def distribute_weighted_round_robin(replicas,node_list,quota_list,weight_list):

    index_weight_list = 0

    while index_weight_list < len(weight_list):
        quota_list[index_weight_list] += round(weight_list[index_weight_list] * replicas)
        replicas -= round(weight_list[index_weight_list] * replicas)

        index_weight_list += 1

    #우선 배치 후 Round Robin
    return distribute_round_robin(replicas,node_list,quota_list)


#우선 할당 후 남은 자원이 가장 많은 쪽부터 할당
def distribute_weighted_resource(replicas,node_list,quota_list,weight_list,resources_list):

    index_weight_list = 0
    available_resources = manager.get_metrics()
    del(available_resources['k8s-master-node'])


    req_cpu = resources_list['cpu']
    req_mem = resources_list['memory']

    while index_weight_list < len(weight_list):
        quota_list[index_weight_list] += round(weight_list[index_weight_list] * replicas)

        available_resources[node_list[index_weight_list]]['cpu'] -= req_cpu * round(weight_list[index_weight_list] * replicas)
        available_resources[node_list[index_weight_list]]['memory'] -= req_cpu * round(weight_list[index_weight_list] * replicas)

        if available_resources[node_list[index_weight_list]]['cpu'] < 0 or available_resources[node_list[index_weight_list]]['memory'] < 0:
            return "fail"

        replicas -= round(weight_list[index_weight_list] * replicas)
        index_weight_list += 1

    #우선 배치 후 Available Resouces 비율이 많은 쪽에 배치


    for index_replicas in range(0,replicas):
        available_resources = get_resources_usage_rate(available_resources)
        best_index = node_list.index(rank_by_resources(node_list,available_resources))
        quota_list[best_index] += 1
        available_resources[node_list[best_index]]['cpu'] -= req_cpu
        available_resources[node_list[best_index]]['memory'] -= req_mem


def split_deployment(quota_list, deployment_list, node_list=None):
    if len(quota_list) != len(deployment_list):
        return deployment_list

    for index in range(len(deployment_list)):
        deployment_list[index]['spec']['replicas'] = quota_list[index]
        if node_list:
            deployment_list[index]['metadata']['name'] = deployment_list[index]['metadata']['name']+str(index)
            deployment_list[index]['spec']['template']['spec']['nodeSelector']['kubernetes.io/hostname'] = node_list[
                index]

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



#manager = k8s_manager.k8s_manager_obj()
#quota_list = distribute_round_robin(replicas,node_list,quota_list)
#quota_list = distribute_weighted_round_robin(replicas,node_list,quota_list,weight_list)
#distribute_weighted_resource(replicas,node_list,quota_list,weight_list,require_resources)
