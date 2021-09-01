import os
import sys
import socket
import json
import hashlib
import time

address = ("mzlnmsl.xyldomain.top", 23805)
reqcommand = "py -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt"
startcommand = "start py main.py"

def getIndex():
    print("检查更新: 获取索引")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(address)
    sock.send('index'.encode('utf-8'))
    dictdata = json.loads(sock.recv(1024))
    sock.close()
    return dictdata

def getDiffList(index):
    global basepath
    print("检查更新: 检查文件差分")
    dldlist = []
    for filename in index:
        if os.path.exists(basepath + filename):
            if index[filename] != '0':
                with open(basepath + filename, 'rb') as rf:
                    if hashlib.md5(rf.read()).hexdigest() != index[filename]:
                        dldlist.append(filename)
        else:
            dldlist.append(filename)
    return dldlist

def dldFiles(dldlist):
    for filename in dldlist:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"获取文件: {filename}")
        sock.connect(address)
        sock.send(filename.encode('utf-8'))
        with open(basepath + filename, 'wb') as wf:
            pass
        while True:
            data = sock.recv(1024)
            if not data :
                break
            with open(basepath + filename, 'ab') as wf:
                wf.write(data)
        sock.close()


basepath = os.path.dirname(os.path.abspath(sys.argv[0])) + '\\'

try:
    index = getIndex()
    dldlist = getDiffList(index)
    dldFiles(dldlist)
except Exception as e:
    print(f"更新时发生错误: {e}")

print("检查requirements...")
time.sleep(1)
os.system(reqcommand)
print("\n启动主程序...")
time.sleep(2)
os.system(startcommand)