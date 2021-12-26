import os

from ShellCMD import os_popen, os_system


def xcodebuild_log(example_dir, log):
    output_log_file = os.path.join(example_dir, 'xcodebuild_binary.log')
    print('xcodebuild log file path ', output_log_file)
    if os.path.exists(output_log_file):
        os.remove(output_log_file)
    with open(output_log_file, 'a+', encoding='utf-8') as f:
        f.write(log)


def xcodebuild(example_dir, cacheDir):
    print('xcodebuild build demo工程，生成出组件二进制文件 %s' % example_dir)
    xcodebuild_cmd = 'cd %s;pod update; security unlock-keychain -p 打包机密码 $HOME/Library/Keychains/login.keychain; \
    xcodebuild build -configuration Debug \
    -workspace Generator.xcworkspace -scheme Generator-Example -arch arm64 -parallelizeTargets -UseModernBuildSystem=NO ONLY_ACTIVE_ARCH=YES \
     -derivedDataPath %s' % (example_dir, cacheDir)

    output = os_popen(xcodebuild_cmd)
    xcodebuild_log(example_dir, output)
    return True


# 修改工程podfile源为二进制源
def changeSourceToBinary(podfile, binary_url, source_url):
    with open(podfile, "r", encoding="utf-8") as f:
        # readlines以列表的形式将文件读出
        lines = f.readlines()

    with open(podfile, "w", encoding="utf-8") as f_w:
        n = 0
        changed = 0
        for line in lines:
            if binary_url in line:
                binary_url_cmt =  "source '" + binary_url + "'\n"
                f_w.write(binary_url_cmt)
                n += 1
                print(line + " binary break")
                changed += 1
            elif source_url in line:
                source_url_cmt = "# source '" + source_url + "'\n"
                line = line.replace(line, source_url_cmt)
                f_w.write(line)
                n += 1
                changed += 1
                print(line + " source break")
            else:
                f_w.write(line)
                n += 1
            if changed == 2:
                break

        for i in range(n, len(lines)):
            f_w.write(lines[i])


if __name__ == '__main__':
    podfile = '/Users/lch/Documents/Podfile'
    binary_url = 'https://gitlab.com/architect-ios/StaticModuleSpec.git'
    source_url = 'https://gitlab.com/architect-ios/ModuleSpec.git'
    changeSourceToBinary(podfile, binary_url, source_url)
