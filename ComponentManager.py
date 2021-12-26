import fnmatch
import json
import os
import shutil
import sys

# 根据组件名称获取组件git地址
from PathUtil import root_dir


def get_component_giturl_with_name(component_name):
    headers = {'PRIVATE-TOKEN': 'xxxxxxx'}
    url = 'https://gitlab.xxxx.com/api/v4/projects?search=%s' % component_name
    print('根据组件名称获取组件git地址的接口是：%s' % url)
    import requests
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print('error %s' % r.text)
    http_response = r.text if r.text else print('没返回结果')
    if http_response:
        json_response = json.loads(http_response)
        for response in json_response:
            if response.get('archived') or response.get('name').upper() != component_name.upper():
                print('已归档，跳过 %s' % response.get('http_url_to_repo'))
                continue
            else:
                http_url_to_repo = response.get('http_url_to_repo')
                if 'wireless_test' not in http_url_to_repo:
                    return http_url_to_repo


# 组件存放的路径
def get_component_dir(component_name):
    source_path = os.path.join(root_dir(), 'binary_cache/components')
    component_path = os.path.join(source_path, component_name)
    try:
        if os.path.exists(component_path):
            shutil.rmtree(component_path, ignore_errors=True)
            print('删除已存在的旧代码重新拉取')
        os.makedirs(component_path)
    except Exception as e:
        print(e)
        print('get_component_dir rmtree失败', component_path)
        exit(-90)
    return component_path


def downloadComponentSource(component_name, podspec_version):
    # 获取组件代码存放目录
    component_dir = get_component_dir(component_name)
    # 获取组件git地址
    gurl = get_component_giturl_with_name(component_name)
    # 拉取组件代码
    os.system('cd %s;git clone %s %s;' % (os.path.dirname(component_dir), gurl, component_name))
    # 代码切换到特定tag下
    os.system('cd %s;git checkout %s > /dev/null 2>&1' % (component_dir, podspec_version))
    return component_dir


def get_podspec_file_path(component_dir):
    try:
        podspec_name = fnmatch.filter(os.listdir(component_dir), '*.podspec.json')[0]
        podspec_path = os.path.join(component_dir, podspec_name)
        if os.path.exists(podspec_path):
            return podspec_path
        else:
            raise FileNotFoundError
    except Exception as e:
        raise Exception("获取podspec文件失败 %s" % component_dir)

# 根据podspec文件，获取subspec 
def get_component_subspecs(podspec_path):
    with open(podspec_path) as f:
        podspec_json = json.load(f)
        podversion = podspec_json.get('source').get('tag')
        podname = podspec_json.get('name')
        subspecs = podspec_json.get('subspecs')
        subspec_names_str = ''
        if podname:
            podspec_name = podname
            if subspecs:
                print(subspecs)
                subpod_names = []
                for subspec in subspecs:
                    name = subspec.get('name')
                    subpod_name = "pod '%s/%s', '%s'" % (podname, name, podversion)
                    subpod_names.append(subpod_name)
                subspec_names_str = '\n'.join(subpod_names)
                print('subspec_names_str:\n %s' % subspec_names_str)
        return subspec_names_str

# 根据podspec文件，获取组件名+版本号+subspec，返回一个tuple
def get_component_real_name(podspec_path):
    with open(podspec_path) as f:
        podspec_json = json.load(f)
        podversion = podspec_json.get('source').get('tag')
        podname = podspec_json.get('name')
        subspecs = podspec_json.get('subspecs')
        subspec_names_str = ''
        if podname:
            podspec_name = podname
            if subspecs:
                print(subspecs)
                subpod_names = []
                for subspec in subspecs:
                    name = subspec.get('name')
                    subpod_name = "pod '%s/%s', '%s'" % (podname, name, podversion)
                    subpod_names.append(subpod_name)
                subspec_names_str = '\n'.join(subpod_names)
                print('subspec_names_str:\n %s' % subspec_names_str)
        return (podspec_name, podversion, subspec_names_str)


if __name__ == '__main__':
    # giturl = get_component_giturl_with_name('YYModel')
    component_dir = downloadComponentSource("SDWebImage", '4.4.11')
    podspec_path = get_podspec_file_path(component_dir)
    print(podspec_path)

    # podspec_tuple = get_component_real_name(podspec_path)
    # print(podspec_tuple)
