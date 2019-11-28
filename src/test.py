import socket
from flask import Flask, request
from flask_restful import Api, Resource
from pythonping import ping
import k8s_manager
import socket, requests, json, yaml, re, copy
import k8s_distribute_pods

data = {'client_ip': '192.168.1.1'}
headers = {'Content-Type': 'application/json; charset=utf-8'}


#url = 'http://10.244.50.227:9400/get_latency'

url = 'http://127.0.0.1:5000/scheduling_by_latency'
res = requests.post(url, headers=headers, data=json.dumps(data))

#print("latency : {}".format(float( re.findall("\d+", res.text)[0] + '.' + re.findall("\d+", res.text)[1])))