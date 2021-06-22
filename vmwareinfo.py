from pysphere import VIServer

class vminfo():
    def __init__(self,host,username,passwd,server_name,test_name):
        self.host=host
        self.username=username
        self.passwd=passwd
        self.server_name=server_name
        self.test_name=test_name

    def get_server_host(self):
        server_obj=VIServer()
        server_obj.connect(host=self.host,user=self.username,password=self.passwd)
        vm1=server_obj.get_vm_by_name(self.server_name)
        return vm1.get_properties["ip_address"]

    def get_test_host(self):
        server_obj = VIServer()
        server_obj.connect(host=self.host, user=self.username, password=self.passwd)
        vm1 = server_obj.get_vm_by_name(self.test_name)
        return vm1.get_properties["ip_address"]

    def check_test_status(self):
        server_obj=VIServer()
        server_obj.connect(host=self.host, user=self.username, password=self.passwd)
        vm1=server_obj.get_vm_by_name(self.test_name)
        status=vm1.get_status()
        if status=="POWERED ON":
            print("%s is not free." % self.test_name)
            return False
        else:
            print("%s is free." % self.test_name)
            return True