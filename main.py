import sys
import os
import time
import logging
import random
import uuid
import base64
import json 
import ctypes
import dns.resolver
from datetime import datetime, timedelta

from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot, QUrl, QThread, pyqtSignal, QCoreApplication ,Qt
# from PyQt5.QtGui import *
from PyQt5.QtWidgets import QMainWindow, QApplication
from qtui import Ui_MainWindow

import config
import network
import mapapi
import utils
import const

mapRespStat = 0
route_routes = []
route_pnts = []
route_epnts = []
route_rawpnts = []
route_distance = []


def main():
    config.init(sys.argv[1])
    # init config read
    if config.getConfig("type")=="android":
        qtwindow.radioButton_A_android.setChecked(True)
    else:
        qtwindow.radioButton_A_ios.setChecked(True)
    qtwindow.lineEdit_A_uuid.setText(config.getConfig("uuid"))
    qtwindow.lineEdit_A_model.setText(config.getConfig("model"))
    qtwindow.lineEdit_B_username.setText(config.getConfig("account"))
    if qtwindow.lineEdit_B_username.text()=="":
        qtwindow.checkBox_B_saveaccount.setChecked(False)
    else:
        qtwindow.checkBox_B_saveaccount.setChecked(True)
    qtwindow.lineEdit_B_password.setText(config.getConfig("password"))
    if qtwindow.lineEdit_B_password.text()=="":
        qtwindow.checkBox_B_savepassword.setChecked(False)
    else:
        qtwindow.checkBox_B_savepassword.setChecked(True)
    qtwindow.lineEdit_B_utoken.setText(config.getConfig("utoken"))
    qtwindow.lineEdit_B_userid.setText(config.getConfig("userid"))
    qtwindow.label_Z_status.setText("等待操作: 设置设备信息")

def routeInit():
    global rpResp
    global runinfo
    global route_routes
    global route_pnts
    global route_rawpnts
    global route_epnts
    global route_distance
    global final_bNodes
    global final_tNodes
    route_routes.clear()
    route_pnts.clear()
    route_rawpnts.clear()
    route_epnts.clear()
    route_distance.clear()
    route_rawpnts.append("st")
    route_pnts.append(rpResp['initloc'])
    route_routes.append([])
    route_distance.append(0.0)
    qtwindow.checkBox_F_hidepoints.setChecked(False)
    qtwindow.label_F_dist.setText(str(format(route_distance[0], '.4f')) + "km")
    qtwindow.lineEdit_F_route.setText(','.join(route_rawpnts))
    runinfo = rpResp['data']
    map_addp("0", rpResp['initloc'], "blue", "起点 st", "st", True, fZoom="16")
    final_bNodes = [item for item in runinfo['ibeacon'] if utils.haversine(item['position'], utils.prasePositionObj(rpResp['initloc']))['km'] < 60]
    final_tNodes = [item for item in runinfo['gpsinfo'] if utils.haversine(item, utils.prasePositionObj(rpResp['initloc']))['km'] < 60]
    for i,node in enumerate(final_bNodes):
        map_addp(1+i, node['position'], "red", "必经点 b" + str(i), "b" + str(i), False)
    for i,node in enumerate(final_tNodes):
        map_addp(3+i, node, "green", "途经点 t" + str(i), "t" + str(i), False)

# Map Operations
def mapInit(path):
    qtwindow.browser.setUrl(QUrl(path))
def mapScript(jscript):
    qtwindow.browser.page().runJavaScript(jscript)
def map_addp(idx, pos, color, tooltip, resp, follow, fZoom="-1", icon="info-sign"):
    pos = utils.prasePositionStr(pos, invert=True)
    # logging.debug('addmarker(' + str(idx) + ',[' + pos + '],"' + color + '",`<div>' + tooltip + '</div>`,"' + resp + '");')
    mapScript('addmarker(' + str(idx) + ',[' + pos + '],"' + color + '",`<div>' + tooltip + '</div>`,"' + resp + '","'+icon+'");')
    if follow:
        mapScript('setview([' + pos + '], ' + fZoom + ')')
def map_delp(idx):
    mapScript('delmarker(' + str(idx) + ');')
def map_addl(idx, posx, color):
    posx = ','.join(str([utils.prasePositionStr(pos, invert=True)]).replace("'", "") for pos in posx)
    # logging.debug('addline(' + str(idx) + ',[' + posx + '],"' + color + '");')
    mapScript('addline(' + str(idx) + ',[' + posx + '],"' + color + '");')
def map_dell(idx):
    mapScript('delline(' + str(idx) + ');')
def map_clear():
    mapScript('dellinesall();')
    mapScript('delmarkersall();')
def mapResponse(msg):
    global mapRespStat
    global route_routes
    global route_pnts
    global route_rawpnts
    global route_epnts
    global route_distance
    if msg=="NULL":
        return
    logging.debug("地图点击反馈:" + msg)
    if mapRespStat==1:
        try:
            qtwindow.lineEdit_D_initloc.setText(utils.prasePositionStr(msg))
        except:
            pass
    elif mapRespStat==2:
        point, ploc = prasePoint(msg)
        logging.debug("坐标处理:" + point + " " + ploc)
        idx = len(route_pnts)
        route_rawpnts.append(point)
        route_pnts.append(ploc)
        if qtwindow.radioButton_F_map.isChecked():
            troute = mapapi.get_route(route_pnts[idx-1], route_pnts[idx])
        else:
            troute = [route_pnts[idx-1], route_pnts[idx]]
        route_routes.append(troute)
        map_addl(idx, route_routes[idx], "cyan")
        qtwindow.lineEdit_F_route.setText(','.join(route_rawpnts))
        route_distance.append(mapapi.calculate_distance(route_routes[idx]))
        route_distance[0]+=route_distance[idx]
        qtwindow.label_F_dist.setText(str(format(route_distance[0], '.4f')) + "km")
        if len(troute)==0:
            logging.warning("路径获取为空, 不添加至路径")
            qsUndo()
def prasePoint(msg):
    global rpResp
    global runinfo
    global route_epnts
    if msg=="st":
        return msg, rpResp['initloc']
    elif msg[0]=="b":
        return msg, utils.prasePositionStr(runinfo['ibeacon'][int(msg[1])]['position'])
    elif msg[0]=="t":
        return msg, utils.prasePositionStr(runinfo['gpsinfo'][int(msg[1])])
    elif msg[0]=="e":
        msg = route_epnts[int(msg[1:])]
    route_epnts.append(utils.prasePositionStr(msg))
    if not qtwindow.checkBox_F_hidepoints.isChecked():
        map_addp(10+len(route_epnts), route_epnts[len(route_epnts)-1], "orange", "额外点 e" + str(len(route_epnts)-1), "e" + str(len(route_epnts)-1), False)
    return "e"+str(len(route_epnts)-1), route_epnts[len(route_epnts)-1]

# Qt Signal
def qsLogin():
    stat, utoken, userid = network.login(qtwindow.lineEdit_B_username.text(), qtwindow.lineEdit_B_password.text(), qtwindow.lineEdit_A_model.text())
    qtwindow.lineEdit_B_utoken.setText(utoken)
    qtwindow.lineEdit_B_userid.setText(userid)
    qe_utoken()
    qe_userid()
    if stat:
        config.setConfig("resumedata","")
        qsSesLogin()
def qsSesLogin():
    global mapRespStat
    global rpResp
    global schoolpos
    if len(qtwindow.lineEdit_B_utoken.text()) != 32:
        logging.error("utoken填写不正确")
        return
    stat, name, school, completed, target = network.userinfo(qtwindow.lineEdit_B_utoken.text(), qtwindow.lineEdit_B_userid.text())
    if stat:
        qtwindow.label_C_name.setText(name)
        qtwindow.label_C_school.setText(school)
        qtwindow.label_C_completed.setText(completed)
        qtwindow.label_C_target.setText(target)
        qtwindow.pushButton_Z_logout.setEnabled(True)
        qtwindow.groupBox_B.setEnabled(False)
        qtwindow.groupBox_C.setEnabled(True)
        qtwindow.groupBox_D.setEnabled(True)
        mapRespStat = 1
        schoolpos = mapapi.get_school_location(school)
        mapScript("init([" + utils.prasePositionStr(schoolpos,invert=True) + "],16)")
        qtwindow.label_Z_status.setText("等待操作: 点击地图选择起点")
        try:
            rpResp = json.loads(base64.b64decode(config.getConfig("resumedata").encode()).decode())
            qtwindow.label_E_dist.setText(rpResp['data']['length'])
            qtwindow.label_E_reqtime.setText(rpResp['requesttime'])
            qtwindow.label_E_initloc.setText(rpResp['initloc'])
            qtwindow.label_E_runid.setText(str(rpResp['data']['runPageId']))
            qtwindow.clabel_E_resume.setVisible(True)
            qtwindow.groupBox_D.setEnabled(False)
            qtwindow.pushButton_D_send.setEnabled(False)
            qtwindow.groupBox_E.setEnabled(True)
            qtwindow.groupBox_F.setEnabled(True)
            mapRespStat = 2
            qtwindow.label_Z_status.setText("等待操作: 点击地图选择途径点[缓存数据]")
            routeInit()
        except:
            pass
    else:
        qtwindow.lineEdit_B_utoken.setText("")
        qtwindow.lineEdit_B_userid.setText("")
        qe_utoken()
        qe_userid()
def qsLogout():
    global mapRespStat
    stat = network.logout(qtwindow.lineEdit_B_userid.text())
    if stat:
        qsTrash()
        mapRespStat = 0
        qtwindow.label_Z_status.setText("等待操作: 登录")
        qtwindow.pushButton_Z_logout.setEnabled(False)
        qtwindow.groupBox_B.setEnabled(True)
        qtwindow.groupBox_C.setEnabled(False)
        qtwindow.groupBox_D.setEnabled(False)
        qtwindow.lineEdit_B_utoken.setText("")
        qtwindow.lineEdit_B_userid.setText("")
        qe_utoken()
        qe_userid()
def qsuuidRandom():
    if qtwindow.radioButton_A_ios.isChecked():
        modellist=["7,1","7,2","8,1","8,2","8,4","9,1","9,3","9,2","9,4","10,1","10,4","10,2","10,5","10,3","10,6","11,2","11,4","11,6","11,8","12,1","12,3","12,5","13,1","13,2","13,3","13,4"]
        qtwindow.lineEdit_A_model.setText("iPhone"+random.choice(modellist))
        qtwindow.lineEdit_A_uuid.setText(str(uuid.uuid4()).upper()+'-'+''.join(str(random.choice(range(10))) for _ in range(10))+'-'+''.join(str(random.choice(range(6))) for _ in range(6)))
    else:
        qtwindow.lineEdit_A_model.setText("OPPOR11Plus")
        qtwindow.lineEdit_A_uuid.setText(uuid.uuid4().hex.upper())
    qe_uuid()
    qe_model()
def qsOaStart():
    if qtwindow.radioButton_A_ios.isChecked():
        if len(qtwindow.lineEdit_A_uuid.text()) != 54:
            logging.error("uuid填写不正确")
            return
        network.init("iOS", qtwindow.lineEdit_A_uuid.text())
    else:
        if len(qtwindow.lineEdit_A_uuid.text()) != 32:
            logging.error("uuid填写不正确")
            return
        network.init("android", qtwindow.lineEdit_A_uuid.text())
    qtwindow.groupBox_A.setEnabled(False)
    qtwindow.pushButton_Z_start.setEnabled(False)
    qtwindow.groupBox_B.setEnabled(True)
    qtwindow.label_Z_status.setText("等待操作: 登录")
def qsInitlocRandom():
    global schoolpos
    rndloc={}
    rndloc['lat']=schoolpos['lat']
    rndloc['lng']=schoolpos['lng']
    rndloc['lat'] += random.uniform(-0.003, 0.003)
    rndloc['lng'] += random.uniform(-0.003, 0.003)
    qtwindow.lineEdit_D_initloc.setText(utils.prasePositionStr(rndloc))
def qsInitRun():
    global rpResp
    global mapRespStat
    stat, rpResp = network.startrun(qtwindow.lineEdit_D_initloc.text(), qtwindow.lineEdit_B_userid.text())
    if stat:
        qtwindow.groupBox_D.setEnabled(False)
        qtwindow.pushButton_D_send.setEnabled(False)
        qtwindow.groupBox_E.setEnabled(True)
        mapRespStat = 2
        qtwindow.label_E_dist.setText(rpResp['data']['length'])
        qtwindow.label_E_reqtime.setText(rpResp['requesttime'])
        qtwindow.label_E_initloc.setText(rpResp['initloc'])
        qtwindow.label_E_runid.setText(str(rpResp['data']['runPageId']))
        config.setConfig("resumedata",base64.b64encode(json.dumps(rpResp, separators=(',',':')).encode()).decode())
        qtwindow.label_Z_status.setText("等待操作: 点击地图选择途径点")
        qtwindow.groupBox_F.setEnabled(True)
        routeInit()
def qsTrash():
    global mapRespStat
    map_clear()
    config.setConfig("resumedata","")
    qtwindow.label_E_reqtime.setText("")
    qtwindow.label_E_initloc.setText("")
    qtwindow.label_E_runid.setText("")
    qtwindow.lineEdit_D_initloc.setText("")
    qtwindow.label_Z_status.setText("等待操作: 点击地图选择起点")
    qtwindow.clabel_E_resume.setVisible(False)
    qtwindow.groupBox_D.setEnabled(True)
    qtwindow.pushButton_D_send.setEnabled(False)
    qtwindow.groupBox_E.setEnabled(False)
    qtwindow.groupBox_F.setEnabled(False)
    qtwindow.groupBox_G.setEnabled(False)
    mapRespStat = 1
def qsUndo():
    global route_routes
    global route_pnts
    global route_rawpnts
    global route_epnts
    if len(route_pnts)>1:
        if route_rawpnts.pop()[0]=="e":
            map_delp(10+len(route_epnts))
            route_epnts.pop()
        map_dell(len(route_routes)-1)
        route_routes.pop()
        route_pnts.pop()
        route_distance[0]-=route_distance.pop()
    qtwindow.lineEdit_F_route.setText(','.join(route_rawpnts))
    qtwindow.label_F_dist.setText(str(format(route_distance[0], '.4f')) + "km")
def qsConfirm():
    global rpResp
    global mapRespStat
    global route_routes
    global route_rawpnts
    global routeData
    global final_bNodes
    global final_tNodes
    global route_distance

    if route_distance[0] < float(rpResp['data']['length']):
        logging.error("距离不足")
        qtwindow.label_Z_status.setText("距离不足")
        return

    pointsrequired = [1,2]
    # required at least 1b+2t points
    for pnt in route_rawpnts:
        if(pnt[0]=='b'):
            pointsrequired[0] -= 1
        elif(pnt[0]=='t'):
            pointsrequired[1] -= 1
     
    if(pointsrequired[0] > 0 or pointsrequired[1] > 0):
        logging.error("途径点数量不足")
        qtwindow.label_Z_status.setText("途径点数量不足")
        return

    mapRespStat = 0
    qtwindow.checkBox_F_hidepoints.setChecked(False)
    qtwindow.groupBox_E.setEnabled(False)
    qtwindow.groupBox_F.setEnabled(False)
    qtwindow.pushButton_Z_logout.setEnabled(False)
    final_route, final_distance = mapapi.generate_path(route_routes)

    if final_distance < float(rpResp['data']['length']):
        final_distance = float(rpResp['data']['length']) + random.uniform(0.05, 0.1)

    # route confirmed, add points to response
    routeData = const.routeData
    respappended = [False, False, False, False, False, False]


    for pnt in route_rawpnts:
        if(pnt[0]=='b'):
            if not respappended[int(pnt[1])]:
                respappended[int(pnt[1])] = True
                map_addp(1+int(pnt[1]), final_bNodes[int(pnt[1])]['position'], "red", "必经点 b" + pnt[1], "b" + pnt[1], False, icon="ok")
                routeData['bNode'].append(final_bNodes[int(pnt[1])])
        elif(pnt[0]=='t'):
            if not respappended[int(pnt[1])+2]:
                respappended[int(pnt[1])+2] = True
                map_addp(3+int(pnt[1]), final_tNodes[int(pnt[1])], "green", "途径点 t" + pnt[1], "t" + pnt[1], False, icon="ok")
                routeData['tNode'].append(final_tNodes[int(pnt[1])])

    for i in range(len(route_routes)):
        map_dell(i)
    map_addl(0, final_route, "orange")
    # reformat path
    tmp = []
    for p in final_route:
        tmp.append({'latitude': str(format(float(p['lat']), '.6f')), 'longitude': str(format(float(p['lng']), '.6f')), 'speed': str(format(random.uniform(0.5, 3.5), '.6f'))})
    final_route = tmp
    
    routeData['track'] = final_route
    qtwindow.groupBox_G.setEnabled(True)
    qtwindow.label_G_starttime.setText(rpResp['requesttime'])
    qtwindow.lineEdit_G_speed.setText(str(random.randint(300,360)))
    qtwindow.lineEdit_G_distance.setText(str(format(final_distance, '.8f')))
    qtwindow.lineEdit_G_bupin.setText(str(format(random.uniform(120, 140), '.1f')))
    qtwindow.lineEdit_G_bushu.setText(str(random.randint(1800,2300)))
    qe_duration()
    qtwindow.label_Z_status.setText("等待操作: 确认提交数据")

def qs_finalconfirm():
    global rpResp
    global routeData

    if float(qtwindow.lineEdit_G_distance.text()) < float(rpResp['data']['length']):
        logging.error("距离不足")
        qtwindow.label_Z_status.setText("距离不足")
        return

    startTime = datetime.strptime(rpResp['requesttime'], "%Y-%m-%d %H:%M:%S")

    # gen trend
    trendy = ["50.566666","100.86667","100.2","50.266666","100.28333","100.816666","50.283333","50.46667","101.666664","101.65","100.53333","50.6","49.983334","50.05","50.583332"]
    trend = []
    for i in range(0,23):
        trend.append({'x': str((i+1)/10), 'y': trendy[random.randint(0, 14)]})

    dis = float(qtwindow.lineEdit_G_distance.text())
    speed = int(qtwindow.lineEdit_G_speed.text())
    bupin = float(qtwindow.lineEdit_G_bupin.text())
    bushu = int(qtwindow.lineEdit_G_bushu.text())

    duration = int(dis * speed)  # seconds
    speed = "%s'%s''" % (speed // 60, speed - speed // 60 * 60)
    qtwindow.lineEdit_G_speed.setText(speed)
    
    endTime = (startTime + timedelta(seconds=duration)).strftime("%Y-%m-%d %H:%M:%S")
    qtwindow.label_G_endtime.setText(endTime)

    # construct post data
    routeData['goal'] = rpResp['data']['length']
    routeData['endTime'] = endTime
    routeData['startTime'] = startTime.strftime("%Y-%m-%d %H:%M:%S")
    routeData['userid'] = qtwindow.lineEdit_B_userid.text()
    routeData['runPageId'] = rpResp['data']['runPageId']
    routeData['real'] = str('%.4f'% (dis*1000))
    routeData['duration'] = str(duration)
    routeData['speed'] = speed
    # routeData['track'] = path
    routeData['trend'] = trend
    routeData['buPin'] = '%.1f' % bupin
    routeData['totalNum'] = "%d" % bushu
    qtwindow.groupBox_G.setEnabled(False)
    waitingthread.start()

def qtDelay():
    global routeData
    startTime = datetime.strptime(routeData['startTime'], "%Y-%m-%d %H:%M:%S")
    durationtmp = startTime + timedelta(seconds=int(routeData['duration'])) - datetime.now()
    while int(durationtmp.total_seconds()) > 0:
        qtwindow.label_Z_status.setText("提交: 等待" + str(int(durationtmp.total_seconds())) + "秒...")
        durationtmp = startTime + timedelta(seconds=int(routeData['duration'])) - datetime.now()
        time.sleep(1)
    qtwindow.label_Z_status.setText("提交...")
    time.sleep(1)
    
def qtSubmit():
    global routeData
    stat, runid = network.saverun(routeData)
    config.setConfig("resumedata","")
    if stat:
        stat, msg= network.rundetail(runid, qtwindow.lineEdit_B_userid.text())
        if stat:
            qtwindow.label_Z_status.setText("提交成功, 查询返回信息:" + msg)
            qtwindow.pushButton_Z_logout.setEnabled(True)
        else:
            qtwindow.label_Z_status.setText("提交成功, 查询失败")
    else:
        qtwindow.label_Z_status.setText("提交失败")
    
def qe_type():
    if qtwindow.radioButton_A_ios.isChecked():
        config.setConfig("type","ios")
    else:
        config.setConfig("type","android")
def qe_uuid():
    config.setConfig("uuid",qtwindow.lineEdit_A_uuid.text())
def qe_model():
    config.setConfig("model",qtwindow.lineEdit_A_model.text())
def qe_username():
    if qtwindow.checkBox_B_saveaccount.isChecked():
        config.setConfig("account",qtwindow.lineEdit_B_username.text())
    else:
        config.setConfig("account","")
def qe_password():
    if qtwindow.checkBox_B_savepassword.isChecked():
        config.setConfig("password",qtwindow.lineEdit_B_password.text())
    else:
        config.setConfig("password","")
def qe_hidepoints():
    global final_bNodes
    global final_tNodes
    global rpResp
    global route_epnts
    if qtwindow.checkBox_F_hidepoints.isChecked():
        mapScript('delmarkersall();')
    else:
        map_addp("0", rpResp['initloc'], "blue", "起点 st", "st", False)
        for i,node in enumerate(final_bNodes):
            map_addp(1+i, node['position'], "red", "必经点 b" + str(i), "b" + str(i), False)
        for i,node in enumerate(final_tNodes):
            map_addp(3+i, node, "green", "途经点 t" + str(i), "t" + str(i), False)
        for i,node in enumerate(route_epnts):
            map_addp(10+i, route_epnts[i], "orange", "额外点 e" + str(i), "e" + str(i), False)
    
def qe_utoken():
    config.setConfig("utoken",qtwindow.lineEdit_B_utoken.text())
def qe_userid():
    config.setConfig("userid",qtwindow.lineEdit_B_userid.text())
def qe_initloc():
    try:
        map_addp(0, qtwindow.lineEdit_D_initloc.text(), "blue", "起点 st", "NULL", True)
        qtwindow.pushButton_D_send.setEnabled(True)
    except:
        pass
def qe_duration():
    duration = int(float(qtwindow.lineEdit_G_speed.text()) * float(qtwindow.lineEdit_G_distance.text()))
    qtwindow.lineEdit_G_time.setText(str(duration))
def qe_debug():
    logger = logging.getLogger()
    if qtwindow.checkBox_Z_debug.isChecked():
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

#Qt Classes
class webchannel(QObject):
    @pyqtSlot(str)
    def js2py(self,msg):
        mapResponse(msg)

class waitingThread(QThread): 
    endSignal = pyqtSignal()
    def __init__(self):  
        super().__init__() 
    def run(self):
        qtDelay()
        self.endSignal.emit()

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.Title.setText(const.version)
        self.browser.page().setWebChannel(qwebchannel)
        qwebchannel.registerObject('channelObject', locchannel)
        # Button events
        self.pushButton_B_login.clicked.connect(qsLogin)
        self.pushButton_B_seslogin.clicked.connect(qsSesLogin)
        self.pushButton_A_random.clicked.connect(qsuuidRandom)
        self.pushButton_Z_start.clicked.connect(qsOaStart)
        self.pushButton_Z_logout.clicked.connect(qsLogout)
        self.pushButton_D_send.clicked.connect(qsInitRun)
        self.pushButton_D_random.clicked.connect(qsInitlocRandom)
        self.pushButton_E_trash.clicked.connect(qsTrash)
        self.pushButton_F_undo.clicked.connect(qsUndo)
        self.pushButton_F_confirm.clicked.connect(qsConfirm)
        self.pushButton_G_finalconfirm.clicked.connect(qs_finalconfirm)

        self.lineEdit_A_uuid.editingFinished.connect(qe_uuid)
        self.lineEdit_A_model.editingFinished.connect(qe_model)
        self.radioButton_A_android.clicked.connect(qe_type)
        self.radioButton_A_ios.clicked.connect(qe_type)
        self.lineEdit_B_username.editingFinished.connect(qe_username)
        self.lineEdit_B_password.editingFinished.connect(qe_password)
        self.checkBox_B_saveaccount.stateChanged.connect(qe_username)
        self.checkBox_B_savepassword.stateChanged.connect(qe_password)
        self.lineEdit_B_utoken.editingFinished.connect(qe_utoken)
        self.lineEdit_B_userid.editingFinished.connect(qe_userid)
        self.lineEdit_D_initloc.textChanged.connect(qe_initloc)
        self.checkBox_F_hidepoints.stateChanged.connect(qe_hidepoints)
        self.lineEdit_G_distance.editingFinished.connect(qe_duration)
        self.lineEdit_G_speed.editingFinished.connect(qe_duration)
        self.checkBox_Z_debug.stateChanged.connect(qe_debug)
        ##
        self.groupBox_B.setEnabled(False)
        self.groupBox_C.setEnabled(False)
        self.groupBox_D.setEnabled(False)
        self.groupBox_E.setEnabled(False)
        self.groupBox_F.setEnabled(False)
        self.groupBox_G.setEnabled(False)
        self.pushButton_Z_logout.setEnabled(False)
        self.pushButton_D_send.setEnabled(False)
        self.clabel_E_resume.setVisible(False)
        ##
        # self.lineEdit_D_initloc.setEnabled(False)
        # self.pushButton_D_random.setEnabled(False)
        self.lineEdit_F_route.setEnabled(False)
        self.lineEdit_G_time.setEnabled(False)

os.system("cls")
print(const.version + "\n")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s:%(lineno)d - [%(levelname)s] %(message)s')

# Update check
dnsresolver = dns.resolver.Resolver()
dnsresolver.nameservers = ['dns9.hichina.com', 'dns10.hichina.com', '8.8.8.8']
try:
    logging.info("检查麦哲伦的吗吗, 当前版本:" + const.versioncheck)
    dnsresponse = dnsresolver.resolve('mzlnmsl.xyldomain.top', 'TXT')
    if dnsresponse[0].strings[0].decode()[:len(const.versioncheck)] == const.versioncheck:
        logging.info("吗吗版本检查成功")
    else:
        logging.info("解析返回:" + dnsresponse[0].strings[0].decode())
        raise Exception("吗吗版本不符")
except Exception as e:
    logging.warning("版本检查失败:")
    logging.warning(str(e))
    logging.warning("***不建议使用过期版本***")
    logging.warning("若仍要启动, 按任意键继续")
    os.system("pause>nul")

logging.info("初始化ui")
ctypes.windll.shcore.SetProcessDpiAwareness(2)
app = QApplication(sys.argv)
qwebchannel = QWebChannel()
locchannel = webchannel()
qtwindow = MainWindow()

if hasattr(sys, 'frozen'):
    # Handles PyInstaller
    mappath = "file:///" + os.path.dirname(sys.executable).replace('\\', '/') + "/route.html"
else: 
    mappath = "file:///" + os.path.dirname(__file__).replace('\\', '/') + "/route.html"
logging.debug("地图文件位置:" + mappath)
mapInit(mappath)
qtwindow.show()

main()
waitingthread = waitingThread()
waitingthread.endSignal.connect(qtSubmit)

sys.exit(app.exec_())