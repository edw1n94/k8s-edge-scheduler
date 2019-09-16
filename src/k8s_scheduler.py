import os
from flask import Flask, jsonify, request
from flask_restful import reqparse, abort, Api, Resource
import k8s_manager
import socket, requests, json, re

app = Flask(__name__)
api = Api(app)

API_LIST = {

    '/get_metrics' : {'': 'print usage cpu and memory'}

}

# EXCEPTIONS

def abort_exception(api_id):
    if api_id not in API_LIST:
        abort(404, message="API {} does not exist".format(api_id))



# INIT
parser = reqparse.RequestParser()
parser.add_argument('task')


# k8s-manager-init

host_ip = socket.gethostbyname(socket.gethostname())
k8s_manager_obj = k8s_manager.k8s_manager_obj()

# init node list
k8s_manager_obj.get_node_list()
k8s_manager_obj.get_metrics()

# set post parameters
headers = {'Content-Type': 'application/json; charset=utf-8'}



class get_metrics(Resource):
    def get(self):
        url = 'http://121.162.16.215:9199/metrics'
        response = requests.get(url)
        return eval(response.text)

class client_ip(Resource):
    def get(self):
        return request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

class get_collecter_status(Resource):
    def get(self):
        node_list = k8s_manager_obj.node_list
        for node in node_list:
            if node.status:
                url = 'http://'+ node.latency_collecter_ip + ":"+ node.latency_collecter_port + '/get_collecter_ip'
                response = requests.get(url)
                print(node.host_name ,response)

class get_latency_from_client(Resource):
    def post(self):
        content = request.get_json(silent=True)
        data = {'client_ip' :str(content.get('client_ip'))}

        latency = {}
        for node in k8s_manager_obj.node_list:
            if node.status:
                url = 'http://' + node.latency_collecter_ip + ':' + node.latency_collecter_port + '/get_latency'

                res = requests.post(url, headers=headers, data=json.dumps(content))
                latency[node.host_name] = float(re.findall("\d+",res.text)[0] + '.'+ re.findall("\d+",res.text)[1])

    # Sort by latency
    # code


    # call Scheduling Method









        print(latency)
        return (json.dumps(latency))



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



#Definition GET and POST Methods
class TodoList(Resource):
    def get(self):
            return API_LIST

    def post(self):
            args = parser.parse_args()
            api_id = 'api%d' % (len(API_LIST)+1)
            API_LIST[api_id] = {'task': args['task]']}
            return API_LIST[api_id], 201

#class deploy_pod(Resource)
#    def post(self):

api.add_resource(TodoList, '/apis/')
api.add_resource(Todo, '/apis/<string:api_id>')

api.add_resource(client_ip, '/client_ip')
api.add_resource(get_metrics, '/nodes')
api.add_resource(get_collecter_status, '/get_collecter_status')
api.add_resource(get_latency_from_client, '/get_latency_from_client')



if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug=True, port=5001)

