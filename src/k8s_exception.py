class k8s_exception(Exception):

    def __init__(self):
        super().__init__('Kubernetes Error')
