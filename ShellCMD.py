import io
import os


def os_system(cmd):
    try:
        n = os.system(cmd) >> 8
        if n != 0:
            print('shell执行失败：%d %s' % (n, cmd))
            raise Exception(cmd)
    except Exception as e:
        raise e


def os_popen(cmd):
    try:
        process = os.popen(cmd)
        output = process.read()
        process.close()
        return output
    except Exception as e:
        raise e


#  ShellCMD.py 执行shell脚本的工具类
if __name__ == '__main__':
    print(os_popen('pwd'))
