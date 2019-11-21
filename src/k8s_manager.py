from __future__ import absolute_import, division, print_function
from kubernetes import client, config
import socket, requests as req, json, yaml, re, copy
import k8s_nodes


# 쿠버네티스의 API 서버 및 메트릭 서버와 통신하기 위한 메소드를 정의 한다.

class k8s_manager_obj(object):

    def create_daemonset_with_latel_selector(self,body,namespace='default'):
        return self.apps_api.create_namespaced_daemon_set(namespace=namespace,body=body)

    def __init__(self, k8s_config=None, namespace='default', in_cluster=False):
        if not k8s_config:
            if in_cluster:
                print(" in cluster 환경에서 실행 ")
                config.load_incluster_config()
            else:
                print(" Kubernetes Container 환경에서 실행")
                config.load_kube_config()
            api_client = None
        else:
            api_client = client.api_client.ApiClient(configuration=k8s_config)


        self.k8s_api = client.CoreV1Api(api_client)
        self.k8s_beta_api = client.ExtensionsV1beta1Api(api_client)
        self.apps_api = client.AppsV1Api(api_client)
        self._namespace = namespace

        # init node_list
        self.node_list = []
        items = self.k8s_api.list_node().items

        for item in items:
            node = k8s_nodes.k8s_nodes(item)
            self.node_list.append(node)

        #if latency-collectors is not current running, create new daemonset
        daemonset = self.apps_api.list_namespaced_daemon_set(namespace='default')
        if 'k8s-latency-collector' not in (str(daemonset)):
            print("latency collector is not running")
            latency_collector_daemonset = yaml.load(open('../latency_collector_deployment'))
            self.apps_api.create_namespaced_daemon_set(namespace=namespace,body=latency_collector_daemonset)
        else:
            print("latency collector is running")

        # get latency_collector pod ip
        items = self.k8s_api.list_pod_for_all_namespaces(watch=False).to_dict()
        for item in items.get('items'):
            if item.get('metadata').get('name').find('k8s-latency-collector') == 0:
                for node in self.node_list:
                    if str(item.get('spec').get('node_name')) == node.host_name:
                        node.latency_collector_ip = item.get('status').get('pod_ip')


    # 노드 레이블 업데이트
    def update_node_labels(self, node, labels, reraise=False):
        body = {"metadata": {"labels": labels}}
        return self.k8s_api.patch_node(name=node, body=body)

    # 네트워크 레이턴시로 정렬.
    def sorting_by_latency(self, node_latency):

        sorted_list = node_latency

        for item in sorted_list.keys():
            sorted_list[item] = float(sorted_list[item])

        sorted_list = sorted(node_latency, key=lambda k : node_latency[k])

        return sorted_list

    def get_best_node(self,latency_list,require_latency):

        list = {}
        best_latency = 2000

        for item in latency_list.keys():
            if best_latency > latency_list[item]['latency']:
                best_latency = latency_list[item]['latency']
                best = item

        list[best] = latency_list[best]
        require_latency -= list[best]['latency']
        for node in self.node_list:
            if node.host_name == best:
                best_node = node

        return list,best_node,require_latency

    #스케줄링 실행
    def create_deployment_with_label_selector(self, body, namespace='default'):
        return self.apps_api.create_namespaced_deployment(namespace='default',body=body)

    # 메트릭 정보 출력 (for debug)
    def print_metrics(self):
        self.get_metrics()
        print("name                    MAXCPU    CPU        MAXMEMORY(bytes)  MEMORY(bytes)     CPU(%)      MEM(%)")
        for node in self.node_list:
            print("{}        {}m     {}m         {}Mi             {}Mi          {}%          {}%"
                  .format(node.host_name,node.max_cpu,node.cpu,node.max_memory,node.memory,
                          int(node.cpu/node.max_cpu*100),int(node.memory/node.max_memory*100)))

    def get_currnet_daemonset(self):
        return self.apps_api.list_namespaced_daemon_set(namespace='default')


    # 레이턴시 수집기 정보 출력 (for debug)
    def print_collector_status(self):
        print("name         ip          status")
        for node in self.node_list:
            print("{}        {}          ".format(node.host_name,node.latency_collector_ip))

    # 메트릭 서버를 호출하여 리소스 정보를 업데이트함.
    def update_metrics(self):
        items = self.k8s_api.api_client.call_api('/apis/metrics.k8s.io/v1beta1/nodes', 'GET', response_type=object)[0]
        for item in items.get('items'):
            for node in self.node_list:
                if node.get_host_name() == item.get('metadata').get('name'):
                    if(item.get('usage').get('memory').find('M') == True):
                        node.set_usage(round(int(item.get('usage').get('cpu').split('n')[0]) / 1000000),round(int(item.get('usage').get('memory').split('M')[0])))
                    else:
                        node.set_usage(round(int(item.get('usage').get('cpu').split('n')[0]) / 1000000),
                                    round(int(item.get('usage').get('memory').split('K')[0]) / 1024))

    # 메트릭 서버 자원을 업데이트
    def get_metrics(self):
        available_metrics = {node.host_name:{} for node in self.node_list}
        self.update_metrics()

        for node in self.node_list:
            available_metrics[node.host_name]['cpu'] = int(node.max_cpu - node.cpu)
            available_metrics[node.host_name]['memory'] = int(node.max_memory - node.memory)
            available_metrics[node.host_name]['max_cpu'] = node.max_cpu
            available_metrics[node.host_name]['max_memory'] = node.max_memory

        return available_metrics