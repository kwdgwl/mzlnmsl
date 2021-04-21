import configparser
import logging


config = {}
conf = configparser.ConfigParser()

confpath = "C:\\Users\\xyl\\Desktop\\dev2.0\\config.ini"

def init(path):
    global conf
    global confpath
    logging.debug("配置路径:" + path)
    confpath = path

def getConfig(name):
    global conf
    global confpath
    #logging.debug("读取配置")
    conf.read(confpath)
    config[name] = conf.get("nmsl", name)
    return config[name]

def setConfig(name, val):
    global conf
    global confpath
    #logging.debug("保存配置")
    config[name]=val
    conf.set("nmsl", name, config[name])
    conf.write(open(confpath,'w'))
    return True
