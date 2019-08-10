import src
from kubernetes import client, config

class k8s_manager(object):

    def __init__(self):
        try:
            v1 = client.CoreV1Api()
        except:
            raise Exception

        print("Listing pods with their IPs:")
        ret = v1.list_pod_for_all_namespaces(watch=False)
        for i in ret.items:
            print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))







