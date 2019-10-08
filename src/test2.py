import k8s_manager,json,yaml,copy
import k8s_distribute_pods

manager = k8s_manager.k8s_manager_obj()

deployment = open('../hello.yaml')
deployment = yaml.load(deployment)


deployment_list = []

replicas = int(deployment['spec']['replicas'])
node_list = ['k8s-worker-node0','k8s-worker-node3','k8s-worker-node2','k8s-worker-node1','k8s-worker-node4']
quota_list = [0 for i in range(0,len(node_list))]
weight_list = [0.3,0.1,0.1]

requests = deployment['spec']['template']['spec']['containers'][0]['resources']['requests']
limits = deployment['spec']['template']['spec']['containers'][0]['resources']['limits']
require_cpu = int(requests['cpu'].split('m')[0]) + int(limits['cpu'].split('m')[0])
require_memory = int(requests['memory'].split('M')[0]) + int(limits['memory'].split('M')[0])

require_resources = {'cpu':require_cpu,'memory':require_memory}

quota_list = k8s_distribute_pods.distribute_round_robin(replicas,node_list,quota_list)

for i in range(0,len(node_list)):
    deployment_list.append(copy.deepcopy(deployment))



    print()
