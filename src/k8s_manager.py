from __future__ import absolute_import, division, print_function

from kubernetes import client, config
from src import k8s_exception
from src import k8s_constants

class k8s_manager(object):

    def __init__(self, k8s_config=None, namespace='default', in_cluster=False):
        if not k8s_config:
            if in_cluster:
                print("in cluster")
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


    def get_version(self,reraise=False):
            return self.k8s_version_api.get_code().to_dict()

    def list_services(self, labels, reraise=False):
        return self._list_namespace_resource(labels=labels,
                                             resource_api=self.k8s_api.list_namespaced_service,
                                             reraise=reraise)