import json
import os
import zipfile

from ShellCMD import os_popen

'''
从settings.json文件中读取root目录，如果是打包机则使用package_root_dir
'''


def root_dir():
    current_realpath = os.path.split(os.path.realpath(__file__))[0]
    with open(os.path.join(current_realpath, 'settings.json'), 'r+') as settingfile:
        settings = json.loads(settingfile.read())
    root_dir = settings.get("root_dir")
    #  如果是打包机，路径放到移动固态硬盘里
    if not is_local():
        root_dir = settings.get("package_root_dir")
    return root_dir

def is_local():
    if get_system_serial().rstrip() == 'F5KXP051J3RY' or get_system_serial().rstrip() == 'C02C20LDK7GF':
        return False
    return True


# 获取上传下载用的域名（上传域名、下载域名）
def get_host():
    current_realpath = os.path.split(os.path.realpath(__file__))[0]
    with open(os.path.join(current_realpath, 'settings.json'), 'r+') as settingfile:
        settings = json.loads(settingfile.read())
    upload_host = settings.get("upload_host")
    down_host = settings.get("down_host")
    return (upload_host, down_host)


# 获取静态库源地址（源码源，静态源，测试静态源）
def get_source_url():
    current_realpath = os.path.split(os.path.realpath(__file__))[0]
    with open(os.path.join(current_realpath, 'settings.json'), 'r+') as settingfile:
        settings = json.loads(settingfile.read())
    code_source_url = settings.get("code_source_url")
    binary_source_url = settings.get("binary_source_url")
    binary_source_url_t = settings.get("binary_source_url_t")
    return (code_source_url, binary_source_url, binary_source_url_t)

def get_repo_name():
    current_realpath = os.path.split(os.path.realpath(__file__))[0]
    with open(os.path.join(current_realpath, 'settings.json'), 'r+') as settingfile:
        settings = json.loads(settingfile.read())
    return settings.get("repo_name")

# 将dirpath文件夹压缩为outFullName
def zipDir(dirpath, outFullName):
    zip = zipfile.ZipFile(outFullName, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dirpath):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dirpath, '')
        for filename in filenames:
            file_path = os.path.join(path, filename)
            if not os.path.islink(file_path):
                zip.write(file_path, os.path.join(fpath, filename))
    zip.close()


# 组件白名单
def white_list():
    current_realpath = os.path.split(os.path.realpath(__file__))[0]
    with open(os.path.join(current_realpath, 'settings.json'), 'r+') as settingfile:
        settings = json.loads(settingfile.read())
    return settings.get("white_list")


def get_system_serial():
    return os_popen("system_profiler SPHardwareDataType | grep Serial | sed 's/ //g' | cut -d':' -f2")


if __name__ == '__main__':
    print(root_dir())
