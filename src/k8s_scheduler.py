from flask import Flask, request, json
from flask_restful import reqparse, abort, Api, Resource
import k8s_manager
import socket, requests as req, json, yaml, re, copy
import k8s_distribute_pods

app = Flask(__name__)
api = Api(app)

# parset init
parser = reqparse.RequestParser()
parser.add_argument('task')

# k8s-manager init and update node resources
host_ip = socket.gethostbyname(socket.gethostname())
k8s_manager_obj = k8s_manager.k8s_manager_obj()
k8s_manager_obj.update_metrics()

# set post parameters
headers = {'Content-Type': 'application/json; charset=utf-8'}

# 레이턴시 수집기가 동작중인지 확인
# TO BE DELETED
class get_collector_status(Resource):
    def get(self):
        node_list = k8s_manager_obj.node_list
        for node in node_list:
            if node.status and node.host_name != 'k8s-master-node':
                url = 'http://'+ node.latency_collector_ip + ":"+ node.latency_collector_port + '/get_collector_ip'
                response = req.get(url)
                print(node.host_name ,response)

class scheduling_by_latency(Resource):

# API를 호출한 클라이언트를 기준으로 함
    def get(self):
        client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        latency = {}
        return "not implemeted"

# 특정 클라이언트의 주소 기준으로 함
    def post(self):

        content = request.get_json(silent=True)
        data = {'client_ip' :str(content.get('client_ip'))}
        deployment = open('../hello.yaml')
        deployment = yaml.load(deployment)
        require_latency = int(deployment['spec']['template']['spec']['nodeSelector']['maxlatency'])
        del(deployment['spec']['template']['spec']['nodeSelector']['maxlatency'])

        limits = deployment['spec']['template']['spec']['containers'][0]['resources']['limits']
        require_cpu = int(limits['cpu'].split('m')[0])
        require_memory = int(limits['memory'].split('M')[0])

        require_resources = {'cpu': require_cpu, 'memory': require_memory,'latency' : require_latency}
        replicas = int(deployment['spec']['replicas'])

#### 네트워크 레이턴시 수집 ####

        latency = {}
        latency2 = {}

        for node in k8s_manager_obj.node_list:
            if node.status and node.latency_collector_ip is not None:
                url = 'http://' + node.latency_collector_ip + ':' + node.latency_collector_port + '/get_latency'
                res = req.post(url, headers=headers, data=json.dumps(content))
                print("node name : {} latency : {}".format(node.host_name, float(
                    re.findall("\d+", res.text)[0] + '.' + re.findall("\d+", res.text)[1])))
                if (float(re.findall("\d+", res.text)[0] + '.' + re.findall("\d+", res.text)[1])):
                    latency[node.host_name] = {'type': 'InternalIP', 'latency': float(
                        re.findall("\d+", res.text)[0] + '.' + re.findall("\d+", res.text)[1])}

        latency, best_node, require_latency = k8s_manager_obj.get_best_node(latency, require_latency)

        for node in k8s_manager_obj.node_list:
            if node is not best_node and node.host_name != 'k8s-master-node':
                data = {'client_ip': node.address}
                res = req.post(
                    'http://' + best_node.latency_collector_ip + ':' + best_node.latency_collector_port + '/get_latency',
                    headers=headers, data=json.dumps(data))
                if (float(re.findall("\d+", res.text)[0] + '.' + re.findall("\d+", res.text)[1]) < require_latency):
                    latency[node.host_name] = {'type': 'InternalIP', 'latency': float(
                        re.findall("\d+", res.text)[0] + '.' + re.findall("\d+", res.text)[1]) +
                                                                                latency[best_node.host_name]['latency']}

                if node.external_ip is not None:
                    data = {'client_ip': node.external_ip}
                    res = req.post(
                        'http://' + best_node.latency_collector_ip + ':' + best_node.latency_collector_port + '/get_latency',
                        headers=headers, data=json.dumps(data))
                    node_latency = float(re.findall("\d+", res.text)[0] + '.' + re.findall("\d+", res.text)[1])
                    if node_latency < require_latency:
                        if latency[node.host_name] is None or node_latency < latency[node.host_name]['latency']:
                            latency[node.host_name]['latency'] = node_latency
                            latency[node.host_name]['type'] = 'ExternalIP'

        sorted_list = k8s_distribute_pods.distribute_weighted_scoring(replicas,require_resources,latency,k8s_manager_obj)

        # Pod 분배 #
        deployment_list = []

        for i in range(0, len(sorted_list)):
            deployment_list.append(copy.deepcopy(deployment))

        deployment_list = k8s_distribute_pods.split_deployment(sorted_list,deployment_list,)

        for item in deployment_list:
            print(item)
        #    k8s_manager_obj.create_deployment_with_label_selector(item)

api.add_resource(get_collector_status, '/get_collector_status')
api.add_resource(scheduling_by_latency, '/scheduling_by_latency')


# 포트 5001
if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug=True, port=5001)

