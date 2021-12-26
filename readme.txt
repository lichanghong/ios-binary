脚本依赖库
pip3 install GitPython
yaml


脚本介绍
1, 基础工具脚本
PathUtil.py 主要方法 root_dir(),获取所有代码存放路径，这个路径是在settings.json中设置，打包机和本地开发机路径分别设置

ShellCMD.py 执行shell脚本的工具类

PodfileManager.py
get_podfile_lock_from_git_url  从主工程中获取lock文件,根据主工程的gurl和branch分支（tag）获取





白名单
1，白名单中的组件是已经静态化的framework，这种不需要再次静态化，会放到白名单（比如alipay）
2，全是.h的组件也会放白名单，这种生成不了.a,比如路由
