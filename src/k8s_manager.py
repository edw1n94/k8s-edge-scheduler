from __future__ import absolute_import, division, print_function

from kubernetes import client, config
from kubernetes.client import CustomObjectsApi
from kubernetes.client.rest import ApiException


import requests
import k8s_nodes

class k8s_manager_obj(object):

    def __init__(self, k8s_config=None, namespace='default', in_cluster=False):
        if not k8s_config:
            if in_cluster:
                print("in cluster ")
                config.load_incluster_config()
            else:
                print("not in cluster")
                config.load_kube_config()
            api_client = None
        else:
            api_client = client.api_client.ApiClient(configuration=k8s_config)


        self.k8s_api = client.CoreV1Api(api_client)
        self.k8s_batch_api = client.BatchV1Api(api_client)
        self.k8s_beta_api = client.ExtensionsV1beta1Api(api_client)
        self.k8s_custom_object_api = client.CustomObjectsApi()
        self.k8s_version_api = client.VersionApi(api_client)
        self._namespace = namespace



        # init node_list


        self.node_list = []
        items = self.k8s_api.list_node().items




        for item in items:
            node = k8s_nodes.k8s_nodes(item)
            self.node_list.append(node)


        # get latency_collecter pod ip

        items = self.k8s_api.list_pod_for_all_namespaces(watch=False).to_dict()
        for item in items.get('items'):
            if item.get('metadata').get('name').find('k8s-latency-collecter') == 0:
                for node in self.node_list:
                    if str(item.get('spec').get('node_name')) == node.host_name:
                        node.latency_collecter_ip = item.get('status').get('pod_ip')



    def list_services(self, labels, reraise=False):
        return self._list_namespace_resource(labels=labels,
                                             resource_api=self.k8s_api.list_namespaced_service,
                                             reraise=reraise)
    def get_node_list(self):
        return self.node_list


    def get_metrics(self):
        url = 'http://121.162.16.215:9199/metrics'
        response = requests.get(url)
        items = eval(response.text)

        for item in items.get('items'):
            #print("{} : {}".format(item.get('metadata').get('name'),item.get('usage')))

            for node in self.node_list:
                if node.get_host_name() == item.get('metadata').get('name'):
                    node.set_usage(round(int(item.get('usage').get('cpu').split('n')[0]) / 1000000),
                                   round(int(item.get('usage').get('memory').split('K')[0]) / 1024))


