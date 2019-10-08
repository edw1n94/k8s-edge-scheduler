class k8s_nodes():

    def __init__(self, item):

        # Node Info
        self.address = item.status.addresses[0].address
        self.host_name = item.status.addresses[1].address
        self.max_cpu = int(item.status.capacity.get('cpu'))*1000

        self.max_memory = round(int(item.status.capacity.get('memory').split('K')[0])/1000)

        #레이턴시 수집기 정보
        self.latency_collector_ip = None
        self.latency_collector_status = None
        self.latency_collector_port = '9400'



        # 노드 상태 얻어오기
        for condition in item.status.conditions:
            if condition.type == 'Ready':
                if condition.status == 'True':
                    self.status = True
                else:
                    self.status = False



    def set_usage(self, cpu, memory):
        self.cpu = cpu
        self.memory = memory

    # 현재 cpu, memory량 가져옴.
    def get_current_usage(self):
        print("{} : cpu = {}%, memory = {}%".format(self.host_name,round(self.cpu/self.max_cpu * 100), round(self.memory/self.max_memory * 100)))

    #return address
    def get_address(self):
        return self.address

    #return host_name
    def get_host_name(self):
        return self.host_name
