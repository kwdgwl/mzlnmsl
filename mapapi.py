import hashlib
import random
import time
import urllib
import logging
from typing import List, Dict
from math import pi, sqrt, sin, cos, atan2
#from const import routeData
import requests

import utils

host = 'http://api.map.baidu.com'
my_ak = '2sNZOdba8vVgbfpYGQZUvz7GwdRUYUiB'
my_sk = '9gbIMAXlvUYuSOZdY2qsxiLlyOmtu9Ry'

def get_sn(url: str):
    queryStr = url + '&ak=%s' % my_ak + '&timestamp=%s' % time.time()
    encodedStr = urllib.parse.quote(queryStr, safe="/:=&?#+!$,;'@()*[]")
    rawStr = encodedStr + my_sk
    sn = hashlib.md5(urllib.parse.quote_plus(rawStr).encode('ascii')).hexdigest()
    return queryStr + '&sn=%s' % sn


def url_params(url: str, params: Dict):
    l = []
    for k, v in params.items():
        l.append('%s=%s' % (k, v))
    return url + '&'.join(l)


def get_school_location(school: str):
    url = '/geocoding/v3/?'
    school = school.replace('(', '')
    school = school.replace(')', '')
    oj = {
        "address": school,
        "output": "json"
    }
    r = requests.get(host + get_sn(url_params(url, oj)))
    
    rj = r.json()

    try:
        location = rj['result']['location']
        logging.info('学校坐标:' + str(location))
        return location
    except:
        logging.error("坐标获取失败")
        raise Exception("这里出了点错, 但我不想处理")
    


def get_route(startp: str, endp: str, region='上海'):
    url = '/direction/v1?'
    oj = {
        'origin': utils.prasePositionStr(startp, invert=True),
        'destination': utils.prasePositionStr(endp, invert=True),
        'mode': 'walking',
        'region': region,
        'output': 'json',
        'coord_type': 'gcj02',
        'ret_coordtype': 'gcj02'
    }
    r = requests.get(host + get_sn(url_params(url, oj)))
    rj = r.json()
    try:
        route = rj['result']['routes'][0]
    except:
        logging.error("路线获取失败")
        return []
    steps = route['steps']
    # dis = route['distance']
    path = [step['path'].split(';') for step in steps]
    path = [startp] + [item for lst in path for item in lst] + [endp]
    return path


def generate_path(routelist) -> Dict:
    points = []
    for point in routelist:
        points += point
    paths = []
    for point in points:
        paths.append(utils.prasePositionObj(point))

    logging.info("传入路径: "+str(len(paths))+"节点")
    paths = gen_continous_route(paths, 0.002)
    logging.info("连贯处理: "+str(len(paths))+"节点")
    paths = randomize_route(paths, 0.000005)
    logging.info("随机化: "+str(len(paths))+"节点")
    removedt, paths = remove_extra_points(paths, 80, 170, 0.005)
    logging.info("去锐角, 去重: "+str(len(paths))+"节点")
    paths = gen_continous_route(paths, 0.008)
    logging.info("连贯处理: "+str(len(paths))+"节点")
    removedt, paths = remove_extra_points(paths, 100, 150, 0.0075)
    logging.info("去锐角, 去重: "+str(len(paths))+"节点")
    paths = randomize_route(paths, 0.00001)
    logging.info("随机化: "+str(len(paths))+"节点")
    dis = calculate_distance(paths)
    logging.info("最终计算距离: "+str(dis))

    return paths, dis

def calculate_distance(path: List[dict]):
    dis=0.0
    for i in range(len(path)-1):
        dis+=utils.haversine(utils.prasePositionObj(path[i]), utils.prasePositionObj(path[i+1]))['km']
    return dis

def gen_continous_route(path: List[dict], maxdis) -> List[dict]:
    extra_points = []
    for i in range(len(path) - 1):
        points = []
        start_lng = float(path[i]['lng'])
        start_lat = float(path[i]['lat'])
        end_lng = float(path[i + 1]['lng'])
        end_lat = float(path[i + 1]['lat'])
        distance = utils.haversine(path[i], path[i + 1])
        if distance['km'] > maxdis:
            extra_points_num = int(distance['km'] / (maxdis / 2.0))
            offset_lng = (end_lng - start_lng) / extra_points_num
            offset_lat = (end_lat - start_lat) / extra_points_num
            for j in range(extra_points_num):
                # pos_lng = start_lng + offset_lng * j + random.uniform(-0.00001, 0.00001)
                # pos_lat = start_lat + offset_lat * j + random.uniform(-0.00001, 0.00001)
                pos_lng = start_lng + offset_lng * j
                pos_lat = start_lat + offset_lat * j
                points.append(
                    {
                        'lng': str(pos_lng),
                        'lat': str(pos_lat)
                    }
                )
        extra_points.append(points)
    result_path = []
    for i in range(len(path) - 1):
        result_path.append(path[i])
        result_path.extend(extra_points[i])
        # result_path.append(path[i + 1])
    return result_path


def remove_extra_points(path: List[dict], angl, angr, mindis) -> List[dict]:
    temp_path = path
    result_path = []
    removed = 1
    while removed > 0:
        removed = 0
        path = temp_path
        temp_path = []
        for i in range(len(path) - 1):
            temp_path.append(path[i])
            distance = utils.haversine(path[i], path[i + 1])
            if distance['km'] < mindis:
                del(path[i + 1])
                removed+=1
            if i >= len(path) - 3:
                for j in range(i+1,len(path)):
                    temp_path.append(path[j])
                break

    removed = 0
    for i in range(len(temp_path) - 2):
        result_path.append(temp_path[i])
        angle1 = utils.angle(temp_path[i], temp_path[i + 1])
        angle2 = utils.angle(temp_path[i + 1], temp_path[i + 2])
        anglet = utils.langle(angle1, angle2)
        
        if anglet > angl and anglet < angr:
            del(temp_path[i + 1])
            del(temp_path[i + 2])
            removed+=1
        if i >= len(temp_path) - 4:
            for j in range(i+1,len(temp_path)):
                result_path.append(temp_path[j])
            break
    
    return removed, result_path



def randomize_route(path: List[dict], rad) -> List[dict]:
    result_path = []
    for i in range(len(path)):
        
        start_lng = float(path[i]['lng'])
        start_lat = float(path[i]['lat'])
        pos_lng = start_lng + random.uniform(-rad, rad)
        pos_lat = start_lat + random.uniform(-rad, rad)
        result_path.append({'lng': str(pos_lng),'lat': str(pos_lat)})
    return result_path


