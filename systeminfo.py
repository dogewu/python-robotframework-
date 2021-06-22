import collections
import re

class linuxSystemInfo():
    def __init__(self, sshmgr,linuxVendor,linuxRelease,linuxArch,server_kernel_path,kernel):
        self.sshmgr=sshmgr
        self.ksp_ssh=sshmgr.server_ssh
        self.test_ssh=sshmgr.test_ssh
        self.linuxVendor=linuxVendor
        self.linuxRelease=linuxRelease
        self.linuxArch=linuxArch
        self.server_kernel_path=server_kernel_path
        self.kernel=kernel


    def __getRedhatVersion(self):
        """
            get Redhat vendor, release system info
        :return: vendor info, release info
        """
        result, resultErr = self.ksp_ssh.ssh_execute_command('cat /etc/redhat-release')
        if "Red" in result:
            linuxVendor = "RedHat"
            linuxRelease, resultErr = self.ksp_ssh.ssh_execute_command(
                "cat /etc/redhat-release | sed 's/^Red Hat Enterprise Linux.* release /EL/' | sed 's/[ .].*//'")
        elif "CentOS" in result:
            linuxVendor = "CentOS"
            linuxRelease, resultErr = self.ksp_ssh.ssh_execute_command(
                "cat /etc/os-release | grep -w \"VERSION\"| sed 's/VERSION=\"/EL/' | sed 's/[ .].*//'")
        elif "Cloud" in result:
            linuxVendor = "CloudLinux"
            linuxRelease, resultErr = self.ksp_ssh.ssh_execute_command(
                "cat /etc/redhat-release | sed 's/^CloudLinux.*release //' | sed 's/[ .].*//'")
        else:
            linuxVendor = "unknownVendor"
            linuxRelease = "unknownRelease"
        return linuxVendor.strip(), linuxRelease.strip()

    def __getOracleVersion(self):
        """
            get Oracle vendor, release system info
        :return: vendor info, release info
        """
        linuxVendor = "Oracle"
        linuxRelease, resultErr = self.ksp_ssh.ssh_execute_command(
            "cat /etc/oracle-release | sed 's/^Oracle Linux Server release /OL/' | sed 's/[ .].*//' ")  # El8
        return linuxVendor.strip(), linuxRelease.strip()    # strip()删除开头结尾的空格

    def __getDebianVersion(self):
        """
            get Debian vendor, release system info
        :return: vendor info, release info
        """
        ret, resultErr = self.ksp_ssh.ssh_execute_command(
            '[[ -f /etc/lsb-release ]] && echo "exist" || echo "not exist"')
        if 'not' in ret:
            linuxVendor = "Debian"
            linuxRelease, resultErr = self.ksp_ssh.ssh_execute_command("awk -F. '{print $1}' /etc/debian_version")
        else:
            linuxVendor, resultErr = self.ksp_ssh.ssh_execute_command(
                "grep 'DISTRIB_ID' /etc/lsb-release | cut -d= -f2 | tr -d ' \n'")
            linuxRelease, resultErr = self.ksp_ssh.ssh_execute_command(
                "grep 'DISTRIB_RELEASE' /etc/lsb-release | cut -d= -f2 | tr -d ' \n'")

        return linuxVendor.strip(), linuxRelease.strip()

    def __getAamazonVersion(self):
        """
            get Debian vendor, release system info
        :return: vendor info, release info
        """
        ret, resultErr = self.ksp_ssh.ssh_execute_command('cat /etc/system-release')
        linuxVendor = "amzn"
        # print(ret)
        if 'AMI' in ret:
            linuxRelease = '1'
        else:
            linuxRelease = '2'

        return linuxVendor.strip(), linuxRelease.strip()

    def __getSuSEVersion(self):
        """
            get SuSE vendor, release system info
        :return: vendor info, release info
        """
        linuxVendor = "SuSE"
        linuxRelease, resultErr = self.ksp_ssh.ssh_execute_command(
            "grep 'VERSION' /etc/SuSE-release | cut -d= -f2 | tr -d ' \n'")
        return linuxVendor.strip(), linuxRelease.strip()

    def __getNullVersion(self):
        """
            Defult vendor, release system info
        :return: vendor info, release info
        """
        print("Can't get version")
        return "unknownVendor", "unknownRelease"

    def init_linuxVersion(self):
        """
            init vendor, release system info
        :return: vendor info, release info
        """
        releaseDic = collections.OrderedDict()      # 排序的字典
        releaseDic['/etc/oracle-release'] = self.__getOracleVersion
        releaseDic['/etc/redhat-release'] = self.__getRedhatVersion
        releaseDic['/etc/debian_version'] = self.__getDebianVersion
        releaseDic['/etc/SuSE-release'] = self.__getSuSEVersion
        # for releaseFilePath in releaseDic.keys():
        #     print(releaseFilePath)
        #
        # releaseDic = {'/etc/oracle-release': self.__getOracleVersion,
        #               '/etc/redhat-release': self.__getRedhatVersion,
        #               '/etc/debian_version': self.__getDebianVersion,
        #               '/etc/SuSE-release': self.__getSuSEVersion}
        for releaseFilePath in releaseDic.keys():
            ret, resultErr = self.ksp_ssh.ssh_execute_command(
                '[[ -f %s ]] && echo "exist" || echo "not exist"' % releaseFilePath)
            if 'not' in ret:
                continue
            else:
                return releaseDic.get(releaseFilePath, self.__getNullVersion)()
        return "unknownVendor", "unknownRelease"

    def init_linuxArch(self):
        """
            init arch system info
        :return: arch info
        """
        archDic = {'i386': 'i386', 'i686': 'i386', 'i586': 'i386', 'amd64': 'x86_64', 'x86_64': 'x86_64',
                   'i86pc': 'x86_64'}
        result, resultErr = self.ksp_ssh.ssh_execute_command('uname -m')
        #self.logger.info("arch info %s" % (result.strip()))
        self.realArch = result.strip()
        linuxArch = archDic.get(result.strip(), "unknownArch")  # 判断计算机是多少位
        #self.logger.info("linux arch info %s" % linuxArch)
        return linuxArch

    def get_install_kernel_cmd(self, kernel_path):
        # default for Oracle, RedHat, CentOS, SuSE
        cmd = "rpm -ivh --force %s/* --nodeps" % kernel_path
        # renew by linux vendor
        if ("Ubuntu" in self.linuxVendor) or ("Debian" in self.linuxVendor):
            cmd = "dpkg --force-all -i %s/* " % kernel_path
        elif "CloudLinux" in self.linuxVendor:
            if '6' in self.linuxRelease:
                cmd = "rpm -ivh --force %s/* --nodeps" % kernel_path
        elif "SuSE" in self.linuxVendor:
            if '12' in self.linuxRelease:
                cmd = "rpm -ivh --force %s/* --nodeps" % kernel_path
        return cmd

    def get_grub_kernel_list_cmd(self):
        cmd = ''
        if ("RedHat" in self.linuxVendor) or ("CentOS" in self.linuxVendor):
            if 'EL8' in self.linuxRelease:
                cmd = 'grubby --info=ALL | awk -F \'=\' \'$1=="title" {print i++ " : " $2}\''
            elif 'EL7' in self.linuxRelease:
                cmd = 'awk -F\\\' \'$1=="menuentry " {print i++ " : " $2}\' /etc/grub2.cfg'
            elif ('EL6' in self.linuxRelease) or ('EL5' in self.linuxRelease):
                cmd = 'awk \'$1=="title" {print i++ " : " $7}\' /boot/grub/grub.conf'

        elif ("Ubuntu" in self.linuxVendor) or ("Debian" in self.linuxVendor):
            cmd = 'awk -F\\\' \'/menuentry / { print i++, $2}\' /boot/grub/grub.cfg'
        elif "SuSE" in self.linuxVendor:
            if '15' in self.linuxRelease:
                cmd = "grub2-once --list"
            elif '12' in self.linuxRelease:
                cmd = 'awk -F\\\' \'/menuentry / { print i++, $2}\' /boot/grub2/grub.cfg'
            elif '11' in self.linuxRelease:
                cmd = 'grep -rw "/boot/initrd" /boot/grub/menu.lst | cat -n'
        elif "Oracle" in self.linuxVendor:
            if 'OL5' in self.linuxRelease:
                cmd = 'awk \'$1=="title" {print i++ " : " $5}\' /boot/grub/grub.conf'
            elif 'OL6' in self.linuxRelease:
                cmd = 'awk \'$1=="title" {print i++ " : " $0}\' /boot/grub/grub.conf'
            elif 'OL7' in self.linuxRelease:
                cmd = 'awk -F\\\' \'$1=="menuentry " {print i++ " : " $2}\' /etc/grub2.cfg'
        elif "CloudLinux" in  self.linuxVendor:
            if '7' in self.linuxRelease:
                cmd = 'awk -F\\\' \'/menuentry / { print i++, $2}\' /boot/grub2/grub.cfg'
            elif '6' in self.linuxRelease:
                cmd = 'awk \'$1=="title" {print i++ " : " $4}\' /boot/grub/grub.conf'

        return cmd

    def adjust_kernel_name(self, kernelName):
        if "Oracle" in self.linuxVendor:
            if 'el' in kernelName:
                kernelName = kernelName[:kernelName.index('el') + 2]
            return kernelName
        return kernelName

    def get_set_grub_boot_kernel_cmd(self, reboot_num):
        cmd = ''
        if ("RedHat" in self.linuxVendor) or ("CentOS" in self.linuxVendor):
            if 'EL7' in self.linuxRelease or 'EL8' in self.linuxRelease:
                cmd = "grub2-set-default " + reboot_num + " && reboot"
            elif ('EL6' in self.linuxRelease) or ('EL5' in self.linuxRelease):
                cmd = "sed -i \'/default=/cdefault=" + reboot_num + "\' /boot/grub/grub.conf && reboot"
        elif "Ubuntu" in self.linuxVendor:
            # exclude Ubuntu
            cmd = "grub-set-default \'Advanced options for Ubuntu>" + str(int(reboot_num) - 1) + "\' && reboot"
            # cmd = "grub-set-default \'Advanced options for Ubuntu>" + str(int(reboot_num) - 1) + "\' && reboot"
        elif "Debian" in self.linuxVendor:
            # linuxRelease : 9 or 10
            cmd = "grub-set-default \'Advanced options for Debian GNU/Linux>" + str(int(reboot_num) - 1) + "\' && reboot"
            if '8' in self.linuxRelease:
                cmd = "grub-set-default \'Advanced options for GNU/Linux>" + str(int(reboot_num) - 1) + "\' && reboot &"
            elif '7' in self.linuxRelease:
                cmd = "grub-set-default " + reboot_num + " && reboot"

        elif "SuSE" in self.linuxVendor:
            if '15' in self.linuxRelease:
                # cmd = "grub2-set-default \'Advanced options for SLES 15>" + str(int(reboot_num) - 1) + "\' && reboot"
                cmd = "grub2-once " + reboot_num + " && reboot"
            elif '12' in self.linuxRelease:
                # exclude SLED12 and snapper rollback
                cmd = "grub2-set-default \'Advanced options for SLED12>" + str(int(reboot_num) - 2) + "\' && reboot"
            elif '11' in self.linuxRelease:
                cmd = "sed -i \'/^default /cdefault " + str(int(reboot_num) - 1) + "\' /boot/grub/menu.lst && reboot"
        elif "Oracle" in self.linuxVendor:
            if ('OL5' in self.linuxRelease) or ('OL6' in self.linuxRelease):
                cmd = "sed -i \'/default=/cdefault=" + reboot_num + "\' /boot/grub/grub.conf && reboot"
            elif 'OL7' in self.linuxRelease:
                cmd = "grub2-set-default " + reboot_num + " && reboot"
        elif "CloudLinux" in self.linuxVendor:
            if '7' in self.linuxRelease:
                cmd = "grub2-set-default " + reboot_num + " && reboot"
            elif '6' in self.linuxRelease:
                cmd = "sed -i \'/default=/cdefault=%s\' /boot/grub/grub.conf && reboot" % reboot_num

        return cmd