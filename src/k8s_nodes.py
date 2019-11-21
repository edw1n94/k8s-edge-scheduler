class k8s_nodes():

    def __init__(self, item):

        # Node Info
        self.address = item.status.addresses[0].address
        self.host_name = item.status.addresses[1].address


        self.max_cpu = int(item.status.capacity.get('cpu'))*1000
        self.max_memory = round(int(item.status.capacity.get('memory').split('K')[0])/1000)


        #Scheduler Pod Info
        self.latency_collector_ip = None
        self.latency_collector_status = None
        self.latency_collector_port = '9400'


        # Init Node Status. If Node is Ready status = True, Unknown or NotReady = False

        for condition in item.status.conditions:
            if condition.type == 'Ready':
                if condition.status == 'True':
                    self.status = True
                else:
                    self.status = False


        # set External IP
        if item.status.addresses[1].address in item.status.addresses:
            self.external_ip = item.status.addresses[1].address

        if 'ExternalIP' in item.metadata.labels:
            self.external_ip = item.metadata.labels['ExternalIP']

        else:
            self.external_ip = None

    def __repr__(self):
        return self.host_name

    def __str__(self):
        return self.host_name

    def set_usage(self, cpu, memory):
        self.cpu = cpu
        self.memory = memory

    #return current cpu and memory
    def get_current_usage(self):
        print("{} : cpu = {}%, memory = {}%".format(self.host_name,round(self.cpu/self.max_cpu * 100), round(self.memory/self.max_memory * 100)))

    #return address
    def get_address(self):
        return self.address

    #return host_name
    def get_host_name(self):
        return self.host_name
