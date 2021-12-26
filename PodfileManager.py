import datetime
import os
import shutil
import yaml
from git import Repo
import PathUtil
from PodModel import PodModel
from ShellCMD import os_system, os_popen


#  获取podfile.lock，根据git地址和分支来获取工程代码并pod update,返回（podfile_lock,current_project_dir）
def get_podfile_lock_from_git_url(gurl, branch):
    root_dir = PathUtil.root_dir()
    print("工程代码存放路径", root_dir)
    print('pod update 中...')
    project_root_dir = os.path.join(root_dir, 'projects')
    if not os.path.exists(project_root_dir):
        print('创建工程存放代码的目录', project_root_dir)
        os.makedirs(project_root_dir)

    component_name = os.path.basename(gurl).split(".")[0]
    current_project_dir = os.path.join(project_root_dir, '%s_%s' % (component_name, branch))
    if os.path.exists(current_project_dir):
        shutil.rmtree(current_project_dir, ignore_errors=True)
    try:
        Repo.clone_from(gurl, to_path=current_project_dir, branch=branch)
        podfile_lock = podupdate(current_project_dir)
        if os.path.exists(podfile_lock):
            print('成功获取最新podfile.lock', podfile_lock)
            return (podfile_lock,current_project_dir)
        raise Exception('pod update 失败')
    except Exception as e:
        raise e


def get_component_from_podfile_lock(podfile_lock: str, keys: [str]) -> []:
    with open(podfile_lock, 'r', encoding='utf-8') as f:
        yaml_content = yaml.load(f.read(), Loader=yaml.Loader)
        results = []
        for key in keys:
            value = yaml_content.get(key)
            results.append(value)
        return results

def detail_pod_string_to_dict(podstr: str) -> {str:PodModel}:
    model = PodModel()
    nameItem = podstr.split(' (')
    name = nameItem[0]
    tag = nameItem[1][:-1]
    model.name = name
    model.tag = tag
    return {name: model}

# 根据podfile.lock 获取所有的组件列表
def component_list_for_podfile_lock(podfile_lock):
    print('从podfile.lock中获取组件名和版本号')
    results = get_component_from_podfile_lock(podfile_lock, ['PODS', 'DEPENDENCIES'])
    PODS = results[0]
    DEPENDENCIES = results[1]
    componentsDict = {}
    for pod in PODS:
        # print(pod)
        if isinstance(pod, dict):
            key = list(pod.keys())[0]
            # if '/' not in key:
                # print('podfile.lock1:%s' % key)
            dict1 = detail_pod_string_to_dict(key)
            componentsDict.update(dict1)
        else:
            # if '/' not in pod:
                # print('podfile.lock2:%s' % pod)
            dict2 = detail_pod_string_to_dict(pod)
            componentsDict.update(dict2)

    print('遍历组件列表PODS，将组件名和版本号解析出来')

    dependenciesDict = { }
    for pod in DEPENDENCIES:
        if "(from" in pod:
            model = PodModel()
            splitList = pod.split(',')
            for item in splitList:
                if "(from" in item:
                    index = item.find(" (from")
                    model.name = item[0:index]
                    url = item[index + 8:-1]
                    model.git = url
                    print("podfile.lock url:%s" % url)
                elif "branch" in item:
                    index = item.find("branch")
                    branch = item[index + 8:-2]
                    model.branch = branch
                    print("podfile.lock branch:%s" % branch)
            if model.name is not None:
                dependenciesDict[model.name] = model
    print('遍历组件列表DEPENDENCIES，将组件名和版本号解析出来')

    for key in dependenciesDict.keys():
        if key in componentsDict.keys():
            componentsDict[key] = dependenciesDict[key]

    return componentsDict



# 工程中执行pod update,返回podfile lock文件路径
def podupdate(project_dir):
    try:
        update_cmd = 'cd %s; pod update > /dev/null 2>&1' % project_dir
        os_system(update_cmd)
        return os.path.join(project_dir, 'Podfile.lock')
    except Exception as e:
        raise e

def create_if_source_not_exists():
    code_source_url, binary_source_url, binary_source_url_t = PathUtil.get_source_url()
    repo_name = PathUtil.get_repo_name()
    print('begin 检测静态仓库是否已经存在，不存在则添加')
    cmd_check_static_repo = 'pod repo list | grep ^%s' % repo_name
    print(cmd_check_static_repo)
    process = os.popen(cmd_check_static_repo)  # return file
    output = process.read()
    if not output:
        print("不存在!!添加%s -> %s" % (repo_name, binary_source_url))
        os.system('pod repo add %s %s' % (repo_name, binary_source_url))
    process.close()
    return (repo_name, code_source_url)


# 直接执行podspec上传到私有库中
def spec_upload(podspec_path):
    print('begin spec文件上传到私有服务器 %s' % datetime.datetime.now())
    repo_name, code_source_url = create_if_source_not_exists()
    common_cmd = ' --allow-warnings --use-libraries --verbose --skip-import-validation --skip-tests '
    cmd = 'pod repo push %s %s %s --sources=%s' % (
        repo_name, podspec_path, common_cmd, code_source_url)
    print(cmd)
    output = os_popen(cmd)
    print(output)


# 组件名+版本号+subspec 写入demo工程podfile中
def writeComponentToPodfile(main_component, subspec_names_str, generator_example_dir):
    print('修改demo工程的podfile', main_component)
    Podfile = '''
    source '源码源地址，使用源码源地址编译二进制文件'
    platform :ios, '9.0'
    target 'Generator_Example' do
      %s
      %s
    end
        ''' % (main_component, subspec_names_str)
    print(Podfile)
    local_podfile_path = os.path.join(generator_example_dir, 'Podfile')
    with open(local_podfile_path, 'w') as podfile_path:
        podfile_path.write(Podfile)


# 为已经静态化成功的组件修改podspec
def modify_binary_specfile(binary_podspec_path, component_name, version):
    upload_host, down_host = PathUtil.get_host()
    zip_remote_url = '%s/%s/%s+%s.zip' % (down_host, component_name, component_name, version)
    print('远程zip下载地址是：%s' % zip_remote_url)
    current_realpath = os.path.split(os.path.realpath(__file__))[0]
    static_library_manager_file = os.path.join(current_realpath, 'main.swift')
    cmd = 'swift %s %s %s %s' % (
        static_library_manager_file, binary_podspec_path, zip_remote_url, binary_podspec_path)
    os_system(cmd)
    print(cmd)


# python3 PodfileManager.py 'https://gitlab.com/ios.git' 'develop'
# 根据组件名称获取组件git地址
if __name__ == '__main__':
    # args = sys.argv[1:]
    # # gurl git地址
    # # branch 分支
    # # 获取podfile.lock
    # podfile_lock = get_podfile_lock_from_git_url(args[0], args[1])
    # print(podfile_lock)
    # 测试从lock读取所有工程组件列表，排除path和git引入方式
    # podfile_lock = '/usr/local/binarycomponent/a/b/c/d/projects/ios_master/Podfile.lock'
    podfile_lock = '/Users/lichanghong/Documents/git_ios/develop/Podfile.lock'
    project_component_list = component_list_for_podfile_lock(podfile_lock)
    print(project_component_list)
