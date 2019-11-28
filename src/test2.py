from flask import Flask, request, json
from flask_restful import reqparse, abort, Api, Resource
import k8s_manager
import socket, requests as req, json, yaml, re, copy
import k8s_distribute_pods

sorted_list2 = [{'host_name': 'k8s-worker-node5', 'deploy': 7}, {'host_name': 'k8s-worker-node6', 'deploy': 8},
                {'host_name': 'k8s-worker-node7', 'deploy': 7},{'host_name': 'k8s-worker-node8', 'deploy': 8}]

deployment = open('../hello.yaml')
deployment = yaml.load(deployment)
del (deployment['spec']['template']['spec']['nodeSelector']['maxlatency'])

k8s_manager_obj = k8s_manager.k8s_manager_obj()
# Pod 분배 #
deployment_list = []

for i in range(0, len(sorted_list2)):
    deployment_list.append(copy.deepcopy(deployment))

deployment_list = k8s_distribute_pods.split_deployment(sorted_list2, deployment_list, )

for item in deployment_list:
    print(item)
    if item['spec']['replicas'] > 0:
        k8s_manager_obj.create_deployment_with_label_selector(item)