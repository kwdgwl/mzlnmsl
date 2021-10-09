import os
import sys
import socket
import json
import time
import hashlib


reqcommand = "py -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt"
startcommand = "start py main.py"


def checkUpdate():
    basepath = os.path.dirname(os.path.abspath(sys.argv[0])) + '\\'
    address = ("mzlnmsl.xyldomain.top", 23805)
    indexname = "mzlnmsl"
    print("检查更新: 获取索引")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(address)
    sock.send(indexname.encode('utf-8'))
    dictdata = json.loads(sock.recv(1024))
    sock.close()

    print("检查更新: 检查文件差分")
    dldlist = []
    for filename in dictdata:
        if os.path.exists(basepath + filename):
            if dictdata[filename] != '0':
                with open(basepath + filename, 'rb') as rf:
                    if hashlib.md5(rf.read()).hexdigest() != dictdata[filename]:
                        dldlist.append(filename)
        else:
            dldlist.append(filename)

    if len(dldlist) == 0:
        return False

    # download
    for filename in dldlist:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"获取文件: {filename}")
        sock.connect(address)
        sock.send(f"{indexname}:{filename}".encode('utf-8'))
        with open(basepath + filename, 'wb') as wf:
            while True:
                data = sock.recv(1024)
                if not data :
                    break
                wf.write(data)
        sock.close()
    return True

if __name__ == '__main__':
    try:
        if checkUpdate():
            print("重新启动...")
            time.sleep(2)
            os.system(f"start py {sys.argv[0]}")
            sys.exit()
    except Exception as e:
        print(f"更新时发生错误: {e}")

    print("检查requirements...")
    time.sleep(1)
    os.system(reqcommand)
    print("\n启动主程序...")
    time.sleep(2)
    os.system(startcommand)