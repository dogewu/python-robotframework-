import requests
import json
import os
from clint.textui import progress

class RIMAPI():
    def __init__(self):
        #self.hostAddress=hostAddress
        # self.id=None
        # self.ksp=None
        # self.kernel=None
        self.path=None
        self.data=self.Get_QUEList()

    def Get_QUEList(self):
        '''
        Get test list from RIM
        :return:
        '''
        try:
            resp = requests.get('http://10.21.149.147:443/caseList/condition/QUEUE')
            data = json.loads(resp.content)
            if data[0]:
                print("New test received.")
                # self.id=data[0]["id"]
                # self.ksp=data[0]["pk_name"]
                # self.kernel=data[0]["kernel_name"]
                return data[0]
        except requests.exceptions.HTTPError as e:
            print(e)
        print("There is no new test.")
        return None

    def Come_OnGoing(self):
        '''
        Set test status to OnGoing
        :return:
        '''
        data = {str(self.data["id"]): {'QAer': 'autoksp'}}
        try:
            resp = requests.put("http://10.21.149.147:443/supportKernelInfo", data=json.dumps(data))
            if resp.status_code==202:
                print("Test is ongoing.")
            else:
                print("Fail to start test.")
        except requests.exceptions.HTTPError as e:
            print(e)

    def Get_OnGoingList(self):
        try:
            resp = requests.get('http://10.21.149.147:443/caseList/condition/ONGOING')
            print(resp.content)
            data = json.loads(resp.content)
        except requests.exceptions.HTTPError as e:
            print(e)

    def Download_KSP(self):
        if str(self.data["id"]) and self.path:
            try:
                resp = requests.get("http://10.21.149.147:443/packageFile/id/" + str(self.id), stream=True)
                total_length = int(resp.headers.get('content-length'))
                try:
                    with open(self.path + self.data['pk_name']+".zip", "wb") as f:
                        for chunk in progress.bar(resp.iter_content(chunk_size=1024),
                                                  expected_size=(total_length / 1024) + 1, width=100):
                            if chunk:
                                f.write(chunk)
                except IOError as e:
                    print(e)
            except requests.exceptions.HTTPError as e:
                print(e)
        else:
            print("Download KSP error.")

    def Download_Kernel(self):
        if str(self.id) and self.path:
            try:
                resp = requests.get("http://10.21.149.147:443/resourceFile/id/" + str(self.id), stream=True)
                total_length = int(resp.headers.get('content-length'))
                try:
                    with open(self.path + self.data["kernel_name"] + ".zip", "wb") as f:
                        for chunk in progress.bar(resp.iter_content(chunk_size=1024),
                                                  expected_size=(total_length / 1024) + 1,
                                                  width=100):
                            if chunk:
                                f.write(chunk)
                except IOError as e:
                    print(e)
            except requests.exceptions.HTTPError as e:
                print(e)
        else:
            print("Download kernel error.")

    def CreatDir(self):
        path="C:/Users/Robot/Desktop/test/"+self.data["kernel_name"]+"/"
        os.makedirs(path)
        if os.path.exists(path):
            self.path=path
            return True
        else:
            print("Create directory fail.")
            return False

    def SetPass(self):
        data = {str(self.data["id"]): {"condition": "DONE"}}
        try:
            resp = requests.put("http://10.21.149.147:443/supportKernelInfo", data=json.dumps(data))
            print(resp.status_code)
            print(resp.content)
        except requests.exceptions.HTTPError as e:
            print(e)

    def SetFail(self):
        data = {str(self.data["id"]): {"condition": "FAIL"}}
        try:
            resp = requests.put("http://10.21.149.147:443/supportKernelInfo", data=json.dumps(data))
            print(resp.status_code)
            print(resp.content)
        except requests.exceptions.HTTPError as e:
            print(e)

if __name__=="__main__":
    api=RIMAPI()
    api.Get_QUEList()
    print(api.data[0])