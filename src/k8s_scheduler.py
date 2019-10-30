from flask import Flask, request, json
from flask_restful import reqparse, abort, Api, Resource
import k8s_manager
import socket, requests as req, json, yaml, re, copy
import k8s_distribute_pods

app = Flask(__name__)
api = Api(app)

API_LIST = {

    '/get_metrics' : {'': 'print usage cpu and memory'}
    '/get_collector_status': {'': 'get latency-collector status'}
    '/scheduling_by_latency': {'': 'do scheduling'}

}

# EXCEPTIONS
def abort_exception(api_id):
    if api_id not in API_LIST:
        abort(404, message="API {} does not exist".format(api_id))





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
            if node.status:
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
        #### 네트워크 레이턴시로 정렬 ####
        latency = {}
        for node in k8s_manager_obj.node_list:
            if node.status and node.latency_collector_ip is not None:
                url = 'http://' + node.latency_collector_ip + ':' + node.latency_collector_port + '/get_latency'
                res = req.post(url, headers=headers, data=json.dumps(content))
                print("node name : {} latency : {}".format(node.host_name, float(re.findall("\d+",res.text)[0] + '.'+ re.findall("\d+",res.text)[1])))
                if(float(re.findall("\d+",res.text)[0] + '.'+ re.findall("\d+",res.text)[1]) < require_latency):
                    latency[node.host_name] = float(re.findall("\d+",res.text)[0] + '.'+ re.findall("\d+",res.text)[1])


        sorted_node_list = k8s_manager_obj.sorting_by_latency(latency)
        print(sorted_node_list)


        # Pod 분배 #


        deployment_list = []

        replicas = int(deployment['spec']['replicas'])
        quota_list = [0 for i in range(0, len(sorted_node_list))]

        for i in range(0, len(sorted_node_list)):
            deployment_list.append(copy.deepcopy(deployment))

        weight_list = [0.3, 0.1]

        requests = deployment['spec']['template']['spec']['containers'][0]['resources']['requests']
        limits = deployment['spec']['template']['spec']['containers'][0]['resources']['limits']
        require_cpu = int(requests['cpu'].split('m')[0]) + int(limits['cpu'].split('m')[0])
        require_memory = int(requests['memory'].split('M')[0]) + int(limits['memory'].split('M')[0])

        require_resources = {'cpu': require_cpu, 'memory': require_memory}

        #3가지 method

        #round robin
        #quota_list = k8s_distribute_pods.distribute_round_robin(replicas, sorted_node_list, quota_list)

        #weighted Round Robin
        #quota_list = k8s_distribute_pods.distribute_weighted_round_robin(replicas,sorted_node_list,quota_list,weight_list)

        #Weighted + Minimum Resource Usage
        quota_list = k8s_distribute_pods.distribute_weighted_resource(replicas, sorted_node_list, quota_list, weight_list, require_resources)

        deployment_list = k8s_distribute_pods.split_deployment(quota_list,deployment_list,sorted_node_list)

        for item in deployment_list:
            #print(item)
            k8s_manager_obj.create_deployment_with_label_selector(item)




# TO BE MODIFIED
class Todo(Resource):
    def get(self, api_id):
        abort_exception(api_id)
        return API_LIST(api_id)

    def delete(self, api_id):
        abort_exception(api_id)
        return '',204

    def put(self, api_id):
        args = parser.parse_args()
        task = {'task': args['task']}
        API_LIST[api_id] = task
        return task, 201



# TO BE DELETED
class TodoList(Resource):
    def get(self):
            return API_LIST

    def post(self):
            args = parser.parse_args()
            api_id = 'api%d' % (len(API_LIST)+1)
            API_LIST[api_id] = {'task': args['task]']}
            return API_LIST[api_id], 201


# API 주소 정의
api.add_resource(TodoList, '/apis/')
api.add_resource(Todo, '/apis/<string:api_id>')
api.add_resource(get_collector_status, '/get_collector_status')
api.add_resource(scheduling_by_latency, '/scheduling_by_latency')


# 포트 5001
if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug=True, port=5001)

