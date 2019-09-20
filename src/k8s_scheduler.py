import os
from flask import Flask, jsonify, request, json
from flask_restful import reqparse, abort, Api, Resource
import k8s_manager
import socket, requests as req, json, yaml, re

app = Flask(__name__)
api = Api(app)

API_LIST = {

    '/get_metrics' : {'': 'print usage cpu and memory'}

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
k8s_manager_obj.get_node_list()
k8s_manager_obj.get_metrics()

# set post parameters
headers = {'Content-Type': 'application/json; charset=utf-8'}

# get Metrics OS Shell Command(kubectl top node)
# Will be Modified
class get_metrics(Resource):
    def get(self):
        url = 'http://121.162.16.215:9199/metrics'
        response = req.get(url)
        return eval(response.text)

# TO BE DELETED
class client_ip(Resource):
    def get(self):
        return request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

# Check is latency_collecter is Running.
#TO BE DELETED
class get_collecter_status(Resource):
    def get(self):
        node_list = k8s_manager_obj.node_list
        for node in node_list:
            if node.status:
                url = 'http://'+ node.latency_collecter_ip + ":"+ node.latency_collecter_port + '/get_collecter_ip'
                response = req.get(url)
                print(node.host_name ,response)

class scheduling_by_latency(Resource):

    # Scheduling For client which called Scheduling API
    def get(self):
        client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        latency = {}
        return "not implemeted"

    # client_ip is given by POST
    def post(self):
        content = request.get_json(silent=True)
        data = {'client_ip' :str(content.get('client_ip'))}


        #### 1. Sorting By Network Latency ####
        latency = {}
        for node in k8s_manager_obj.node_list:
            if node.status:
                url = 'http://' + node.latency_collecter_ip + ':' + node.latency_collecter_port + '/get_latency'
                res = req.post(url, headers=headers, data=json.dumps(content))
                latency[node.host_name] = float(re.findall("\d+",res.text)[0] + '.'+ re.findall("\d+",res.text)[1])

        sorted_node_list = k8s_manager_obj.sorting_by_latency(latency)


        #### Scheduling By NodeSelector ####

        # Test File, Should be Modified
        # Add nodeSelector
        hello = open('../hello.yaml')
        hello = yaml.load(hello)
        hello['spec']['template']['spec']['nodeSelector'] = {'kubernetes.io/hostname': sorted_node_list[0]}

        # 1. Update Resource Usages
        replicas = int(hello['spec']['replicas'])
        requests = hello['spec']['template']['spec']['containers'][0]['resources']['requests']
        limits = hello['spec']['template']['spec']['containers'][0]['resources']['limits']

        require_cpu = int(requests['cpu'].split('m')[0]) + int(limits['cpu'].split('m')[0])
        require_memory = int(requests['memory'].split('M')[0]) + int(limits['memory'].split('M')[0])


        # Check is Node has sufficient resources
        k8s_manager_obj.get_metrics()


        for node in k8s_manager_obj.get_node_list():
            if node.host_name == sorted_node_list[0]:
                if (node.max_cpu-node.cpu) - (require_cpu * replicas) > 0 and (node.max_memory-node.memory) - (require_memory * replicas) > 0:
                    print("scheduling available")

                    # exec scheduling
                    k8s_manager_obj.create_deployment_with_label_selector(hello)

                else:
                    print("not enough resources")
                    print("{} {} ".format((node.max_cpu-node.cpu) - (require_cpu * replicas),(node.max_memory-node.memory) - (require_memory * replicas) ))


        # else then split replicas


        # Call Scheduling Deployment Method
        #k8s_manager_obj.create_deployment_with_label_selector(hello)


        # TO BE IMPLEMENTED






    # If Scheduling has Succeded, Return Message
        return "success"

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


# Definition of API Address
api.add_resource(TodoList, '/apis/')
api.add_resource(Todo, '/apis/<string:api_id>')
api.add_resource(client_ip, '/client_ip')
api.add_resource(get_metrics, '/nodes')
api.add_resource(get_collecter_status, '/get_collecter_status')
api.add_resource(scheduling_by_latency, '/scheduling_by_latency')



if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug=True, port=5001)

