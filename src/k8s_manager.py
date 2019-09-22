from __future__ import absolute_import, division, print_function
from kubernetes import client, config
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

    #스케줄링 실행
    def create_deployment_with_label_selector(self, body, namespace='default'):
        return self.k8s_beta_api.create_namespaced_deployment(namespace=namespace,body=body)


    # 메트릭 서버를 호출하여 리소스 정보를 업데이트함.
    def get_metrics(self):
        items = self.k8s_api.api_client.call_api('/apis/metrics.k8s.io/v1beta1/nodes', 'GET', response_type=object)[0]
        for item in items.get('items'):
            for node in self.node_list:
                if node.get_host_name() == item.get('metadata').get('name'):
                    node.set_usage(round(int(item.get('usage').get('cpu').split('n')[0]) / 1000000),
                                   round(int(item.get('usage').get('memory').split('K')[0]) / 1024))

