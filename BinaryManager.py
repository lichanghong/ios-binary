import datetime
import fnmatch
import os
import shutil
import time

import requests

from ComponentManager import downloadComponentSource, get_podspec_file_path, get_component_dir, get_component_subspecs
from DBManager import insert_component_info_data, componentExists
from Helper import exceptionForWecom, clearCache
from PathUtil import white_list, root_dir, zipDir, get_host, is_local
from PodModel import PodModel
from PodfileManager import component_list_for_podfile_lock, podupdate, writeComponentToPodfile, spec_upload, \
    modify_binary_specfile
from ShellCMD import os_system, os_popen

# 为组件创建一个壳工程，用于编译
from XcodebuildTool import xcodebuild


def createEmptyProjectForComponent(component_dir):
    print('component_path:', component_dir)
    proj_dir = os.path.join(component_dir, 'Generator')
    try:
        if os.path.exists(proj_dir):
            shutil.rmtree(proj_dir)
            print('删除已存在的旧代码重新拉取')
        print('拉取代码')
        create_cmd = 'pod lib create Generator --template-url=https://gitlab.com/wireless-architect/architect-ios/pod-template.git'
        print('cd %s;pwd; %s' % (component_dir, create_cmd))
        os_popen('cd %s;pwd; %s' % (component_dir, create_cmd))
        generator_example_dir = os.path.join(component_dir, 'Generator/Example')
        return generator_example_dir
    except Exception as e:
        raise Exception('创建壳工程失败', e)


# 更新组件依赖的依赖版本号，和主工程对齐
def update_component_version_with_project(generator_example_dir, project_podfile_lock):
    # 获取包含依赖的依赖所有组件列表
    podfilelock = podupdate(generator_example_dir)
    component_list = component_list_for_podfile_lock(podfilelock)
    # 开始从主工程对比找版本号
    project_component_list = component_list_for_podfile_lock(project_podfile_lock)
    print('---------------begin check----------------')
    json_components_str = ''
    for key in component_list:
        # 获取组件中的PodModel
        component_item = component_list.get(key)
        component_name = component_item.name
        # 获取组件在主工程中的PodModel
        project_item = project_component_list.get(component_name)
        if not project_item:
            exceptionForWecom("组件在主工程中没找到？%s" % component_name)
            continue

        component_git = project_item.git
        component_git_branch = project_item.branch
        if component_git:
            c_item = 'pod "%s", :git => "%s" \n' % (component_name, component_git)
            if component_git_branch:
                c_item = 'pod "%s", :git => "%s", :branch => "%s" \n' % (
                    component_name, component_git, component_git_branch)

            json_components_str += c_item
            continue
        else:
            if not project_item.tag:
                exceptionForWecom("组件在主工程中没找到git地址和tag号？%s" % component_name)
                continue
            c_item = 'pod "%s", "%s" \n' % (component_name, project_item.tag)

            json_components_str += c_item
            continue
    return json_components_str


# 通过编译，是否编译出了.a
def binary_file_exists(buildPath, component_real_name):
    binary_file_path = os.path.join(buildPath, 'Build/Products/Debug-iphoneos/%s/lib%s.a' % (
        component_real_name, component_real_name))
    if os.path.exists(binary_file_path):
        print('存在静态库: %s' % binary_file_path)
        print('修改二进制文件的podspec文件source地址指向zip')
        return (True, binary_file_path)

    else:
        err = '不存在静态库'
        print(err)
    return (False, '')


# , upload_host, component_name, component_path, podspec_name,
# podspec_version
def generate_binary_zip_to_server(binary_component_dir):
    zip_path = '%s.zip' % binary_component_dir
    print('查看zip是否已经存在，存在则删除。zip文件地址：%s' % zip_path)
    if os.path.exists(zip_path):
        os.remove(zip_path)
    print('开始压缩zip')
    zipDir(binary_component_dir, zip_path)
    if not os.path.exists(zip_path):
        raise Exception("生成zip文件失败")
    print('将压缩文件上传到文件服务器')
    component_name_version = os.path.basename(binary_component_dir)
    name_versions = component_name_version.split('+')
    if len(name_versions) != 2:
        raise Exception("通过binary路径没有获取到组件名称和版本号信息")

    # name = '%s+%s.zip' % (name_versions[0], name_versions[1])
    request_data = {
        'name': name_versions[0]
    }
    upload_host, down_host = get_host()
    r = requests.post(upload_host, data=request_data, files={'file': open(zip_path, 'rb')})
    print('上传结果：%s' % r.text)
    if r.status_code == 200:
        print('删除zip文件和编译产物')
        os.remove(zip_path)
        print('上传二进制的podspec到静态源')
        binary_podspec_path = os.path.join(binary_component_dir, '%s.podspec.json' % name_versions[0])
        spec_upload(binary_podspec_path)
    else:
        exceptionForWecom(component_name_version+" 上传二进制podspec失败")
        raise Exception('上传二进制podspec失败')


def buildComponent(componentName, version, project_podfile_lock, forced_build_all=False):
    # if componentName != 'ZRControlPackage':
    #     return
    # 查找组件是否已经静态化，如果已经静态化则跳过
    podspec_exists, haveStaticed = componentExists('%s+%s' % (componentName, version))
    if not forced_build_all:
        if haveStaticed:
            print("组件已经有静态化版本，跳过执行静态化", componentName)
            return
        else:
            if podspec_exists:
                # 如果静态化的组件是在白名单中的，直接将源码spec上传即可
                if componentName in white_list():
                    print("组件在白名单中，跳过执行静态化", componentName)
                    return
    else:
        if podspec_exists:
            # 如果静态化的组件是在白名单中的，直接将源码spec上传即可
            if componentName in white_list():
                print("组件在白名单中，跳过执行静态化", componentName)
                return

    try:
        # 这个是组件目录，比如 components/YYModel
        component_dir = downloadComponentSource(componentName, version)
        podspec_path = get_podspec_file_path(component_dir)
        print(podspec_path)
    except Exception as e:
        raise e
    subspecs = get_component_subspecs(podspec_path)

    # 如果组件在白名单中，直接传podspec即可
    if componentName in white_list() and os.path.exists(podspec_path):
        spec_upload(podspec_path)
        return 
 
    # 不在白名单中且不存在静态化版本，开始进行静态化流程
    binary_cache = os.path.join(root_dir(), 'binary_cache')
    # 先创建存放二进制内容的根目录
    binary_root_dir = os.path.join(binary_cache, 'binary')
    print('如果二进制文件存放的根目录不存在则创建，否则不处理 %s' % binary_root_dir)
    os.makedirs(binary_root_dir) if not os.path.exists(binary_root_dir) else print('已存在binary根目录，继续')
    binary_component_dir = os.path.join(binary_root_dir, '%s+%s' % (componentName, version))
    # 目录存在则先删除，后面会全新创建
    clearCache(binary_component_dir)

    print('复制源码到静态路径：%s -> %s' % (component_dir, binary_component_dir))
    pods_xcodeproj = os.path.join(component_dir, '_Pods.xcodeproj')
    if os.path.exists(pods_xcodeproj) or os.path.islink(pods_xcodeproj):
        os_system('rm -rf ' + pods_xcodeproj)
    shutil.copytree(component_dir, binary_component_dir, symlinks=True)
    for dir in os.listdir(binary_component_dir):
        filePath = os.path.join(binary_component_dir, dir)
        if dir.startswith('.'):
            os_system('rm -rf ' + filePath)

    generator_example_dir = createEmptyProjectForComponent(component_dir)
    print('demo path:',generator_example_dir)
    try:
        writeComponentToPodfile("pod '%s', '%s'" % (componentName, version), subspecs,
                                generator_example_dir)
        new_podfile_content = update_component_version_with_project(generator_example_dir, project_podfile_lock)
        writeComponentToPodfile('', new_podfile_content, generator_example_dir)
        #  xcodebuild 固定返回true, cachedir如果是打包机不能放移动硬盘，否则有的组件编译失败
        cachedir = '/Users/lichanghong/Cache/binary_cache/%s_%s' % (componentName, version)
        if is_local():
            cachedir = os.path.join(binary_cache, 'buildcache/%s_%s' % (componentName, version))
        if xcodebuild(generator_example_dir, cachedir):
            exists, binary_file_path = binary_file_exists(cachedir, componentName)
            if exists:
                print('将静态库复制到binary文件夹下')
                shutil.copy(binary_file_path, binary_component_dir)
                # 已经静态化成功，修改podspec文件指向zip
                binary_podspec_path = os.path.join(binary_component_dir, '%s.podspec.json' % componentName)
                modify_binary_specfile(binary_podspec_path, componentName, version)
                print('生成和上传二进制zip包到文件服务器')
                generate_binary_zip_to_server(binary_component_dir)
            else:
                exceptionForWecom('%s:%s 静态库编译失败，执行源码上传' % (componentName, version))
                spec_upload(podspec_path)
        # 最后无论成功还是失败，都清理缓存
        clearCache(generator_example_dir)
        clearCache(cachedir)
    except Exception as e:
        raise Exception("发现异常：%s" % e.__str__())


if __name__ == '__main__':
    start_time = time.time()
    print('begin 所有任务开始时间 %s' % datetime.datetime.now())
    # component_dir = downloadComponentSource("YYModel", '1.0.4')
    # buildComponent("SwiftMonkey", 'master')
    try:
        buildComponent("JSONModel", '1.1.4', '/Users/lch/Documents/proj/component/a/Podfile.lock', forced_build_all=True)
    except Exception as e:
        exceptionForWecom(e.__str__())
        print(e.args)
    end_time = time.time()
    print('end 所有任务开始时间 %s' % datetime.datetime.now())
    print('最终总时长：%s' % str(end_time - start_time))
