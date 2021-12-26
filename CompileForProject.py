import getopt
import os.path
import sys
import time
import datetime

from BinaryManager import buildComponent
from Helper import exceptionForWecom, clearCache
from PodfileManager import get_podfile_lock_from_git_url, component_list_for_podfile_lock, spec_upload

# 拉取主工程，遍历组件逐个进行检测是否静态化，没有静态化则执行编译
def checkForPorject(gurl, branch, forced_build_all=False):
    # 获取podfile.lock
    # (podfile_lock, current_project_dir) = get_podfile_lock_from_git_url(gurl, branch)
    # if not os.path.exists(podfile_lock):
    #     exceptionForWecom("podfile.lock 生成失败 %s %s" % (gurl, branch))
    #     exit(-99)
    # print(podfile_lock)
    # podfile_lock = '/Volumes/FastSSD/binarycomponent/projects/client/Podfile.lock'
    podfile_lock = '/usr/local/binarycomponent/a/b/c/d/projects/_master/Podfile.lock'

    # exit(0)
    # 测试从lock读取所有工程组件列表，排除path引入方式
    project_component_list = component_list_for_podfile_lock(podfile_lock)

    for key in project_component_list:
        # 获取组件中的PodModel
        component_item = project_component_list.get(key)
        if not component_item:
            exceptionForWecom("主工程中没找到这个组件？ %s" % key)
            continue
        try:
            c_name = component_item.name
            c_version = component_item.tag
            if not c_version:
                # have no version , the component is git ref
                continue
            if '/' in c_name:
                continue

            if component_item.git:
                continue

                # c_version = component_item.branch
            print('%s : %s 开始执行静态化(先检查后执行)' % (c_name, c_version))
            buildComponent(c_name, c_version, podfile_lock, forced_build_all=forced_build_all)
        except Exception as e:
            print(e.args)
    clearCache(current_project_dir)

def main(argv):
    print('begin get params from server')
    gurl = ''
    gbranch = ''
    try:
        opts, args = getopt.getopt(argv, "g:b:h:", ["help=", "git=", "branch="])
    except getopt.GetoptError:
        print('Error: CompileForProject.py -g <git地址> -b <组件分支> -h <help>')
        print('   or: CompileForProject.py --git=<git地址> --branch=<组件分支> --help=<帮助>')
        sys.exit(2)
        # 处理 返回值options是以元组为元素的列表。
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('binary_component.py -g <git地址> -v <组件版本> -c <config>')
            print('or: binary_component.py --git=<git地址> --version=<组件版本> --config=<debug or release>')
            sys.exit()
        elif opt in ("-g", "--git"):
            gurl = arg
        elif opt in ("-b", "--branch"):
            gbranch = arg

    print('git 地址：', gurl)
    print('分支：', gbranch)

    # 打印 返回值args列表，即其中的元素是那些不含'-'或'--'的参数。
    for i in range(0, len(args)):
        print('参数 %s 为：%s' % (i + 1, args[i]))

    if not gbranch or not gurl:
        print('参数传递错误')
        exceptionForWecom("二进制化任务调用参数传递错误分支或git地址缺失")
        sys.exit(404)

    try:
        checkForPorject(gurl, gbranch, forced_build_all=False)
    except Exception as e:
        exceptionForWecom(e.__str__())
        print(e.__str__())

# python3 ./BinaryComponent2/CompileForProject.py --branch master --git https://gitlab.com/wireless/wireless-ios/ios.git
if __name__ == '__main__':
    start_time = time.time()
    print('begin 所有任务开始时间 %s' % datetime.datetime.now())
    main(sys.argv[1:])
    end_time = time.time()
    print('end 所有任务开始时间 %s' % datetime.datetime.now())
    print('最终总时长：%s' % str(end_time - start_time))
    #     gurl = 'https://gitlab.com/wireless/wireless-ios/ios.git'
    #     branch = 'feature_20211108_build_success_static'
    #     checkForPorject(gurl, branch)

    # buildComponent('ZRControlPackage', 'feature_20211108_build_success', '/usr/local/binarycomponent/a/b/c/d/projects/_20211108_build_success/Podfile.lock')
    # 打包机lock路径
    # lockfile = '/Volumes/FastSSD/binarycomponent/projects/Podfile.lock'
    # lockfile = '/usr/local/binarycomponent/a/b/c/d/projects/static/Podfile.lock'
    # if not os.path.exists(lockfile):
    #     exit(-90)
    #
    # buildComponent('ZRIMSDK', '1.1.13', lockfile)