import datetime
import functools
import os
import subprocess
import sys
import time
import zipfile
from multiprocessing import Lock, Queue

import RIMAPI
import systeminfo
import autokspssh
import vmwareinfo

class kernel_bulid():
    def __init__(self,linux_info,api_info):
        self.test_ssh=linux_info.test_ssh
        self.ksp_ssh=linux_info.ksp_ssh
        self.server_kernel_path=linux_info.server_kernel_path
        self.linux_info=linux_info
        self.server_path=api_info.path
        self.api_info=api_info
        self.kernellist=self.__extract_from_zipfile(self.linux_info.kernel,self.api_info.data["pk_name"],self.server_path)

    def __extract_from_zipfile(self,kernel,ksp,path):
        if not os.path.exists(path+kernel+".zip"):
            print("Kernel archive not downloads.")
            return False
        if not os.path.exists(path+ksp+".zip"):
            print("KSP archive not downloads.")
            return False
        kernellist=""
        zip1=zipfile.ZipFile(path+kernel+".zip")
        zip2=zipfile.ZipFile(path+ksp+".zip")
        zip1.extractall(path)
        zip2.extractall(path)
        if os.path.exists(path+"environment.zip"):
            zip3=zipfile.ZipFile(path+"environment.zip")
            kernellist=zip3.namelist()
            zip3.extractall()
            zip3.close()
        zip1.close()
        zip2.close()
        return kernellist

    def __install_kernel_on_test_machine(self, kernel):
        cmd = "uname -r"
        ret, ret_err = self.test_ssh.ssh_execute_command(cmd)
        #self.logger.debug("Get current running kernel ret %s, by cmd: %s" % (ret, cmd))
        cur_kernel = ret.strip()
        #self.logger.info("Current running %s kernel need running kernel %s" % (cur_kernel, kernel))
        if kernel == cur_kernel:
            #self.logger.info("%s is running..." % cur_kernel)
            return

        # install kernel
        #self.logger.info("Start install kernel %s on test machine" % kernel)
        self.test_ssh.ssh_execute_command("killall -9 rpm")
        self.test_ssh.ssh_execute_command("killall -9 apt-get")
        self.test_ssh.ssh_execute_command("rm /var/lib/dpkg/lock-frontend")
        self.test_ssh.ssh_execute_command("rm /var/lib/dpkg/lock")
        self.test_ssh.ssh_execute_command("rm /var/cache/apt/archives/lock")
        time.sleep(10)

        dst_file_path = "autoksp/kernel/" + kernel + "/"
        install_kernel_cmd = self.linux_info.get_install_kernel_cmd(dst_file_path)
        install_kernel_ret, install_kernel_ret_err = self.test_ssh.ssh_execute_command(install_kernel_cmd)
        #self.logger.info("Install remote kernel ret %s, by cmd: %s" % (install_kernel_ret, install_kernel_cmd))
        if "error" in str(install_kernel_ret_err):
            #self.logger.error("install remote kernel fail,ret %s, need RD" % install_kernel_ret_err)
            #log_path = self.linux_info.path.local.kernel_log_for_Rd
            #filename = datetime.datetime.now().strftime('_%Y%m%d_%H%M%S.log')
            # kernel_log_file = log_path + '/' + "installKernelFail" + filename
            # with open(kernel_log_file, 'w+') as f:
            #     f.write(str(install_kernel_ret))
            #     f.write(str(install_kernel_ret_err))
            #     f.close()
            # sendto mail and exit
            # mail = autoKsp_mail.autoMail()
            # mail.addmsg("Install %s kernel fail, need R&D" % kernel)
            # mail.addfile(kernel_log_file)
            # mail.send_mail()
            print("Install kernel fail.")
            sys.exit(-1)

        self.__select_kernel_on_test_environment(kernel)

        return
    def __select_kernel_on_test_environment(self, test_kernel):
        # print(self.test_ssh)
        grub_cmd = self.linux_info.get_grub_kernel_list_cmd()
        grub_ret, grub_ret_err = self.test_ssh.ssh_execute_command(grub_cmd)    # 调整启动顺序
        #self.logger.info("grub ret %s, by cmd %s" % (grub_ret, grub_cmd))
        testkernel = self.linux_info.adjust_kernel_name(test_kernel)
        #self.logger.info("Change %s kernel reboot by grub on test machine" % testkernel)
        testgrub = grub_ret.splitlines()
        #self.logger.info("Change --->  %s   ==>  %s" % (grub_ret, str(testgrub)))
        # find_flag = False
        for bootstr in testgrub:
            #self.logger.info("bootstr %s, testkernel %s" % (bootstr, testkernel))
            if testkernel in bootstr:
                reboot_num = bootstr.split()[0]
                cmd = self.linux_info.get_set_grub_boot_kernel_cmd(reboot_num)
                #self.logger.info("find grub reboot_num %s, by cmd %s" % (reboot_num, cmd))
                ret, reterr = self.test_ssh.ssh_execute_command(cmd)
                #self.logger.info("find bootstr and set grub ret %s, by cmd: %s" % (ret, cmd))
                return

        # not find kernel in grub
        #self.logger.warning("Can not find kernel %s by grub on test machine, need R&D" % testkernel)
        # mail = autoKsp_mail.autoMail()
        # mail.addmsg("Can not find kernel %s by grub on test machine, need R&D" % testkernel)
        # mail.send_mail()
        sys.exit(-1)

    def __send_kernel_to_test_environment(self, kernel):
        kernel_path = self.server_kernel_path
        #self.logger.info("send kernel %s file to test machine" % kernel_path)
        if not os.path.isdir(kernel_path):
            return False

        file_list = os.listdir(kernel_path)
        for file_name in file_list:
            file_path = os.path.join(kernel_path, file_name)
            #self.logger.debug("Find file: %s" % file_path)
            if os.path.isfile(file_path) and (file_name.endswith('.rpm') or file_name.endswith('.deb')):
                dst_path = "autoksp/kernel/" + kernel + "/" + file_name
                #self.logger.debug("Send %s To %s" % (file_path, dst_path))
                self.test_ssh.scp_transport_pathfile(file_path, dst_path)
        self.test_ssh.ssh_execute_command("sync")
        return True

    def __prepare_test_environment(self, kernel):
        # send build kernel to test environment
        if not self.__send_kernel_to_test_environment(kernel):
            return False
        return True

    def install(self):
        is_ok = self.__prepare_test_environment(self.linux_info.kernel)
        if not is_ok:
            print("Fail to tansport kernel.")
            return False
        self.__install_kernel_on_test_machine(self.linux_info.kernel)
        self.__select_kernel_on_test_environment(self.linux_info.kernel)

if __name__=="__main__":
    api=RIMAPI.RIMAPI()
    kernel="4.4-154-geneics"
    if api.data:
        api.CreatDir()
        kernel = api.data["kernel_name"]
        KSP = api.data["pk_name"]
        linuxVendor = api.data["version"]
    api.Download_Kernel()
    api.Download_KSP()
    vm_mgr = vmwareinfo.vminfo("10.22.2.196","qa","qaP@ssword","WU-RF","KSP-CentOS7.8")
    server_host = vm_mgr.get_server_host()
    test_host = vm_mgr.get_test_host()
    ssh_mgr = autokspssh.ssh_mgr("root","P@ssw0rd","root","P@ssw0rd",server_host,test_host)
    linux_info = systeminfo.linuxSystemInfo(ssh_mgr,"CentOS","7","x86_64","s",api.path,kernel)
    build = kernel_bulid(linux_info,api)
    build.install()
