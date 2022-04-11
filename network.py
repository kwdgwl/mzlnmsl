import logging
import requests
import hashlib
import const
import json
from datetime import datetime



# PROXIES = {'http': 'http://localhost:8888', 'https':'http://localhost:8888'}
# CERT_VERIFY = False
PROXIES = {}
CERT_VERIFY = True


def init(ostype, uuid):
    global isiOS
    global session
    global host
    global headers
    global key

    logging.debug("初始化, 类型:" + ostype)
    session = requests.Session()
    host = const.host
    if ostype == 'iOS':
        isiOS = True
        headers = const.ios_headers
        key = const.ios_key
    elif ostype == 'android':
        isiOS = False
        headers = const.android_headers
        key = const.android_key
    else:
        logging.critical("?")
    headers['uuid'] = uuid
    # misc init
    appupdate()
    misc(0)


def sign(data):
    global key
    sign = hashlib.md5()
    k = key + 'data' + data
    sign.update(k.encode('ascii'))
    return sign.hexdigest()


def login(account, password, model):
    global isiOS
    global session
    global host
    global headers

    logging.info("登录")

    ses_data = json.dumps(
        {"password": password, "info": headers['uuid'], "mobile": account, "type": model}, separators=(',', ':'))
    ses_sign = sign(ses_data)
    ses_params = {'data': ses_data, 'sign': ses_sign}
    ses_url = host + '/api/reg/login'

    if isiOS:
        if 'utoken' in headers:
            headers.pop('utoken')
        resp = session.post(ses_url, data=ses_params,
                            headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
    else:
        headers['utoken'] = ''
        resp = session.get(ses_url, params=ses_params,
                           headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
    resp = resp.json()

    if(resp['msg'] == u'登录成功'):
        logging.info("登录成功, 返回信息:")
        logging.info("姓名:" + resp['data']['username'])
        logging.info("学校:" + resp['data']['school'])
        logging.info("utoken:" + resp['data']['utoken'])
        logging.info("userid:" + resp['data']['userid'])
        return True, resp['data']['utoken'], resp['data']['userid']
    else:
        logging.warning("登录失败, 返回信息:" + resp['msg'])
        return False, "", ""


def userinfo(utoken, userid):
    global isiOS
    global session
    global host
    global headers

    logging.info("获取信息")
    headers['utoken'] = utoken

    ses_data = json.dumps({"userid": userid}, separators=(',', ':'))
    ses_sign = sign(ses_data)

    ses_params = {'data': ses_data, 'sign': ses_sign}
    ses_url = host + '/api/center/userCenter'

    if isiOS:
        resp = session.post(ses_url, data=ses_params,
                            headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
    else:
        resp = session.get(ses_url, params=ses_params,
                           headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
    resp = resp.json()

    if(resp['msg'] == u'获取成功'):
        logging.info("获取成功, 返回信息:")
        logging.info("姓名:" + resp['data']['username'])
        logging.info("学校:" + resp['data']['school'])
        logging.info("完成次数:" + str(resp['data']['effectiveTimes']))
        logging.info("目标次数:" + str(resp['data']['targetTotalTimes']))
        logging.info("userid:" + resp['data']['userid'])

        # misc
        appupdate()
        adreport(resp['data']['userid'])
        misc(2)
        misc(4)
        misc(3)
        misc(1)
        # misc(0)

        return True, resp['data']['username'], resp['data']['school'],  str(resp['data']['effectiveTimes']),  str(resp['data']['targetTotalTimes'])
    else:
        logging.warning("获取失败, 返回信息:" + resp['msg'])
        return False, "", "", "", ""


def logout(userid):
    global isiOS
    global session
    global host
    global headers

    logging.info("登出")

    ses_data = json.dumps({"userid": userid}, separators=(',', ':'))
    ses_sign = sign(ses_data)

    ses_params = {'data': ses_data, 'sign': ses_sign}
    ses_url = host + '/api/reg/exitLogin'

    if isiOS:
        resp = session.post(ses_url, data=ses_params,
                            headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
    else:
        resp = session.get(ses_url, params=ses_params,
                           headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
    resp = resp.json()

    if(resp['msg'] == u'退出成功'):
        if isiOS:
            headers.pop('utoken')
        else:
            headers['utoken'] = ''
        logging.info("登出成功")
        return True
    else:
        logging.warning("登出失败, 返回信息:" + resp['msg'])
        return False


def startrun(initloc, userid):
    global isiOS
    global session
    global host
    global headers

    logging.info("跑步开始请求")

    ses_data = json.dumps(
        {"userid": userid, "type": 1, "initLocation": initloc}, separators=(',', ':'))
    ses_sign = sign(ses_data)

    ses_params = {'data': ses_data, 'sign': ses_sign}
    ses_url = host + '/api/run/runPage'

    if isiOS:
        resp = session.post(ses_url, data=ses_params,
                            headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
    else:
        headers['ntoken'] = ''
        resp = session.get(ses_url, params=ses_params,
                           headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
        headers.pop('ntoken')
    resp = resp.json()
    try:
        if(resp['msg'] == u'获取成功'):
            logging.info('获取成功, runPageId:' + str(resp['data']['runPageId']))
            resp['requesttime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            resp['initloc'] = initloc
            return True, resp
        else:
            logging.warning('获取失败, 返回信息:' + resp['msg'])
            return False, {}
    except:
        logging.warning('获取失败: ' + str(resp))
        return False, {}


def saverun(runinfo):
    global isiOS
    global session
    global host
    global headers

    logging.info("上传数据")

    ses_data = json.dumps(runinfo, separators=(',', ':'))
    ses_sign = sign(ses_data)

    ses_params = {'data': ses_data, 'sign': ses_sign}
    ses_url = host + '/api/run/saveRunV2'

    if not isiOS:
        headers['ntoken'] = ''
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

    resp = session.post(ses_url, data=ses_params,
                        headers=headers, proxies=PROXIES, verify=CERT_VERIFY)

    if not isiOS:
        headers.pop('ntoken')
        headers.pop('Content-Type')

    resp = resp.json()
    if(resp['msg'] == u'成功'):
        logging.info('上传成功, runid:' + str(resp['data']['runid']))
        return True, str(resp['data']['runid'])
    else:
        logging.warning('上传失败, 返回信息:' + resp['msg'])
        return False, ""


def rundetail(runid, userid):
    global isiOS
    global session
    global host
    global headers

    logging.info("查询跑步信息")

    ses_data = json.dumps(
        {"runid": runid, "userid": userid}, separators=(',', ':'))
    ses_sign = sign(ses_data)

    ses_params = {'data': ses_data, 'sign': ses_sign}
    ses_url = host + '/api/center/runDetailV2'

    if isiOS:
        resp = session.post(ses_url, data=ses_params,
                            headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
    else:
        resp = session.get(ses_url, params=ses_params,
                           headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
    resp = resp.json()

    if(resp['msg'] == u'查询成功'):
        logging.info("查询完成, 服务器返回信息:" + resp['data']['runDesc'])
        return True, resp['data']['runDesc']
    else:
        logging.warning("查询失败, 返回信息:" + resp['msg'])
        return False, ''


def adreport(userid):
    global isiOS
    global session
    global host
    global headers

    logging.info("广告上报三次")

    ses_data = json.dumps({"userid": userid, "adId": "9071033990491217",
                          "type": "VideoAd"}, separators=(',', ':'))
    ses_sign = sign(ses_data)

    ses_params = {'data': ses_data, 'sign': ses_sign}
    ses_url = host + '/api/ad/report'

    if isiOS:
        resp = session.post(ses_url, data=ses_params,
                            headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
        resp = session.post(ses_url, data=ses_params,
                            headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
        resp = session.post(ses_url, data=ses_params,
                            headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
    else:
        logging.info("安卓广告上报跳过")
        return True
    resp = resp.json()

    if(resp['code'] == 200):
        logging.info("广告上报完成")
        return True
    else:
        logging.warning(
            "广告上报失败, 返回code:" + str(resp['code']))
        return False


def appupdate():
    global isiOS
    global session
    global host
    global headers

    logging.info("模拟查询版本更新")

    if isiOS:
        ses_data = json.dumps({"type": "2"}, separators=(',', ':'))
    else:
        logging.info("安卓版本检测跳过")
        return True
    ses_sign = sign(ses_data)

    ses_params = {'data': ses_data, 'sign': ses_sign}
    ses_url = host + '/api/reg/appUpdate'

    if isiOS:
        resp = session.post(ses_url, data=ses_params,
                            headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
    else:
        resp = session.get(ses_url, params=ses_params,
                           headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
    resp = resp.json()

    if(resp['msg'] == u'获取成功'):
        logging.info("获取成功, 版本:" + resp['data']['version'])
        return True, resp['data']['version']
    else:
        logging.warning("获取失败, 返回信息:" + resp['msg'])
        return False, ""


def misc(index):
    global isiOS
    global session
    global host
    global headers

    # index
    # ? appupdate
    # ? adreport
    # 0 adslist
    # 1 toastindex5
    # 2 apiconfig
    # 3 bjcallback
    # 4 discoveryinit
    misc_name = ["adsList", "toastIndex1", "apiConfig",
                 "bjCallback", "discovery/init(Android Only)"]
    misc_url = ['/api/art/adsList', '/api/Toast/get_index/1',
                '/index.php/api/configuration/apiConfig', '/index.php/api/reg/bjCallback', '/api/discovery/init']
    misc_data = [{}, {}, {}, {}, {}]
    misc_method = [['POST', 'GET'], ['POST', 'GET'], [
        'GET', 'GET'], ['GET', 'POST'], ['FUCK', 'GET']]
    # [IOS, ANDROID]

    logging.info("模拟杂项请求:" + misc_name[index])

    ses_data = json.dumps(misc_data[index], separators=(',', ':'))
    ses_sign = sign(ses_data)

    ses_params = {'data': ses_data, 'sign': ses_sign}
    ses_url = host + misc_url[index]

    if isiOS:
        ses_method = misc_method[index][0]
    else:
        ses_method = misc_method[index][1]

    if ses_method == 'POST':
        resp = session.post(ses_url, data=ses_params,
                            headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
    elif ses_method == 'GET':
        resp = session.get(ses_url, params=ses_params,
                           headers=headers, proxies=PROXIES, verify=CERT_VERIFY)
    else:
        return False
    resp = resp.json()

    if(resp['code'] == 200):
        logging.info("请求成功:" + misc_name[index])
        return True
    else:
        logging.warning(
            "请求失败:" + misc_name[index] + ", 返回code:" + str(resp['code']))
        return False
