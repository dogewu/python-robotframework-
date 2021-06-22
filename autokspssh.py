#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 5/17/20 9:23 PM
# @Author : qinyong
# @Site :
# @File : autoKsp_ssh.py

import os
import time
from stat import S_ISDIR
from scp import SCPClient
import paramiko

class ssh_manager(object):
    def __init__(self, host, username, password):
        self.host = host
        self.port = 22
        self.username = username
        self.password = password

    def __str__(self):
        return '\n'.join(['%s:\n    %s' % item for item in self.__dict__.items()])

    def ssh_renew_ip(self, host):
        self.host = host

    # def ssh_execute_command(self, cmd):
    #     global reterrstr
    #     trycnt = 0
    #     while trycnt < 5:
    #         try:
    #             ssh = paramiko.SSHClient()
    #             ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #             ssh.connect(self.host, self.port, self.username, self.password, timeout=300)
    #             stdin, stdout, stderr = ssh.exec_command(command=cmd, timeout=3600)
    #             retstr = stdout.read().decode()
    #             reterrstr = stderr.read().decode()
    #             self.logger.debug("ssh execute cmd(%s) stdout(%s) stderr(%s)" % (cmd, retstr, reterrstr))
    #             ssh.close()
    #             break
    #         except Exception as e:
    #             # print("ssh exe failed, retry %s, error %s" % (str(trycnt), e))
    #             retstr = ""
    #             reterrstr = ("ssh exe failed, retry %s, error %s" % (str(trycnt), e))
    #             trycnt = trycnt + 1

    #     return retstr, reterrstr

    def ssh_execute_command(self, cmd, time_out=3600):
        trycnt = 0
        retstr = ""
        reterrstr = ""
        ssh = None
        while trycnt < 20:
            try:
                ssh = paramiko.SSHClient()  # paramiko模块是基于用户名密码登录的sshclient方式登录
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(self.host, self.port, self.username, self.password, timeout=time_out)
                break
            except Exception as e:
                retstr = ""
                reterrstr = ("ssh connerct failed, NoResponse, retry %s, error %s" % (str(trycnt), e))
                time.sleep(5)
                trycnt = trycnt + 1
        if trycnt < 20:
            # if None != ssh:
            stdin, stdout, stderr = ssh.exec_command(command=cmd, timeout=time_out, get_pty=True)
            retstr = stdout.read().decode()
            reterrstr = stderr.read().decode()
            #self.logger.debug("ssh execute cmd(%s) stdout(%s) stderr(%s)" % (cmd, retstr, reterrstr))
            ssh.close()

        return retstr, reterrstr

    '''
    def ssh_execute_command(self, cmd):
        global reterrstr
        trycnt = 0
        while trycnt < 5:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(self.host, self.port, self.username, self.password, timeout=300)
                stdin, stdout, stderr = ssh.exec_command(command=cmd, timeout=600)
                retstr = stdout.read()
                reterrstr = stderr.read()
                self.logger.debug("ssh execute cmd(%s) stdout(%s) stderr(%s)" % (cmd, retstr, reterrstr))
                ssh.close()
                break
            except Exception as e:
                # print("ssh exe failed, retry %s, error %s" % (str(trycnt), e))
                retstr = ""
                reterrstr = ("ssh connerct failed, NoResponse, retry %s, error %s" % (str(trycnt), e))
                time.sleep(5)
                trycnt = trycnt + 1

        return retstr.decode(), reterrstr.decode()
    '''

    def scp_transport_file(self, sourcefile, destinationfile):
        scp = paramiko.Transport((self.host, self.port))
        scp.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(scp)
        sftp.put(sourcefile, destinationfile)
        scp.close()

    def scp_get_remote_file(self, sourcefile, destinationfile):
        scp = paramiko.Transport((self.host, self.port))
        scp.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(scp)
        sftp.get(sourcefile, destinationfile)
        scp.close()

    def scp_get_remote_allfile(self, remote_path, local_path):
        scp = paramiko.Transport((self.host, self.port))
        scp.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(scp)
        try:
            remote_files = sftp.listdir(remote_path)
            for file in remote_files:  # 遍历读取远程目录里的所有文件

                local_file = local_path + '/' + file
                #self.logger.info("local_file: %s", local_file)
                remote_file = remote_path + '/' + file
                #self.logger.info("remote_file: %s", remote_file)
                sftp.get(remote_file, local_file)
        except IOError:  # 如果目录不存在则抛出异常
            return ("remote_path or local_path is not exist, error %s", IOError)
        scp.close()

    def __get_all_files_in_remote_dir(self, sftp, remote_dir, local_dir):
        # 保存所有文件的列表
        all_remote_files = list()
        all_local_files = list()
        # 去掉路径字符串最后的字符'/'，如果有的话
        if remote_dir[-1] == '/':
            remote_dir = remote_dir[0:-1]
        if local_dir[-1] == '/':
            local_dir = local_dir[0:-1]
        # 获取当前指定目录下的所有目录及文件，包含属性值
        files = sftp.listdir_attr(remote_dir)
        for file in files:
            # remote_dir目录中每一个文件或目录的完整路径
            remote_filename = remote_dir + '/' + file.filename
            local_filename = local_dir + '/' + file.filename
            # 如果是目录，则递归处理该目录，这里用到了stat库中的S_ISDIR方法，与linux中的宏的名字完全一致
            if S_ISDIR(file.st_mode):
                if not os.path.exists(local_filename):
                    os.makedirs(local_filename)

                tmp_all_remote_file, tmp_all_local_files = self.__get_all_files_in_remote_dir(sftp, remote_filename,
                                                                                              local_filename)
                all_remote_files.extend(tmp_all_remote_file)
                all_local_files.extend(tmp_all_local_files)
            else:
                all_remote_files.append(remote_filename)
                all_local_files.append(local_filename)

        return all_remote_files, all_local_files

    def sftp_get_dir(self, remote_dir, local_dir):
        scp = paramiko.Transport((self.host, self.port))
        scp.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(scp)
        try:
            # 获取远端linux主机上指定目录及其子目录下的所有文件
            all_remote_files, all_local_files = self.__get_all_files_in_remote_dir(sftp, remote_dir, local_dir)
            # 依次get每一个文件
            for remote_file, local_file in zip(all_remote_files, all_local_files):
                sftp.get(remote_file, local_file)
            return ''
        except Exception as e:
            return "sftp get dir failed %s" % e

    def scp_put_local_allfile(self, local_path, remote_path):
        scp = paramiko.Transport((self.host, self.port))
        scp.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(scp)
        try:
            local_files = os.listdir(local_path)
            for file in local_files:  # 遍历读取local目录里的所有文件
                local_file = local_path + file
                remote_file = remote_path + file
                sftp.put(local_file, remote_file)  # 将 local_file 上传到远端
        except IOError as e:  # 如果目录不存在则抛出异常
            return ("remote_path or local_path is not exist err %s" % e)
        scp.close()

    # def scp_transport_pathfile(self, sourcefile, destinationfile):
    #     # create path
    #     cmd = 'mkdir -p ' + os.path.dirname(destinationfile)
    #     self.logger.info(cmd)
    #     retstr, reterrstr = self.ssh_execute_command(cmd)
    #     self.logger.info("scp_transport_pathfile mkdir: retstr is (%s), reterrstr is (%s)" % (retstr,reterrstr))
    #     # transport file
    #     scp = paramiko.Transport((self.host, self.port))
    #     scp.connect(username=self.username, password=self.password)
    #     sftp = paramiko.SFTPClient.from_transport(scp)
    #     sftp.put(sourcefile, destinationfile)
    #     scp.close()

    def scp_transport_pathfile(self, sourcefile, destinationfile):
        cmd = 'mkdir -p ' + os.path.dirname(destinationfile) + ' && sync'
        time.sleep(20)
        retstr, reterrstr = self.ssh_execute_command(cmd)
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=str(self.host), port=22, username=self.username, password=self.password)
        scp = SCPClient(ssh.get_transport())
        scp.put(sourcefile, recursive=True, remote_path=os.path.dirname(destinationfile))
        scp.close()


class ssh_mgr():
    def __init__(self,testuser,testpasswd,serveruser,serverpasswd,server_host="", test_host=""):
        self.test_host = test_host
        self.server_host = server_host
        self.testuser=testuser
        self.testpasswd=testpasswd
        self.serveruser=serveruser
        self.serverpasswd=serverpasswd
        self.test_ssh = ssh_manager(self.test_host, self.testuser, self.testpasswd)
        self.server_ssh = ssh_manager(self.server_host, self.serveruser, self.serverpasswd)

    # def __parse_ssh_cfg(self, file_path):
    #     autoKsp_fileParse.parse_file.__init__(self, file_path)
    #     self.testuser = self.get_value_by_selection_key("ssh", "testuser")
    #     self.testpasswd = self.get_value_by_selection_key("ssh", "testpasswd")
    #     self.serveruser = self.get_value_by_selection_key("ssh", "autokspuser")
    #     self.serverpasswd = self.get_value_by_selection_key("ssh", "autoksppasswd")

    def __str__(self):
        return '\n'.join(['%s:\n    %s' % item for item in self.__dict__.items()])


if __name__ == '__main__':
    print("-------------------------1--------------------------------------")
    # sshMgr = ssh_manager('10.21.149.44', 'root', 'd3aut0k3p')
    sshMgr = ssh_manager('10.21.149.124', 'root', 'd3aut0k3p')

    print("-------------------------2--------------------------------------")
    # releaseFilePath = '/etc/aaa'
    aa = sshMgr.ssh_execute_command('ls')
    print(aa)
    print("-------------------------3--------------------------------------")

    bb = sshMgr.scp_transport_pathfile("/home/tmp/1.txt", '/home/tmp2')
    print(bb)
    print("-------------------------3--------------------------------------")



