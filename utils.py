import hashlib

from math import pi, sqrt, sin, cos, atan, atan2

def prasePositionStr(inputd, invert=False):
    if type(inputd)==type("NMSL"):
        inputd = inputd.replace(',',' ')
        inputd = inputd.replace('，',' ')
        tmp = inputd.split()
        lng = float(tmp[0])
        lat = float(tmp[1])
    else:
        try:
            lng = float(inputd['lng'])
            lat = float(inputd['lat'])
        except:
            lng = float(inputd['longitude'])
            lat = float(inputd['latitude'])
    if lng < lat or invert:
        if not(lng < lat and invert):
            return str(lat) + "," + str(lng)
    return str(lng) + "," + str(lat)
    
def prasePositionObj(inputd):
    if type(inputd)==type("NMSL"):
        inputd = inputd.replace(',',' ')
        inputd = inputd.replace('，',' ')
        tmp = inputd.split()
        lng = float(tmp[0])
        lat = float(tmp[1])
    else:
        try:
            lng = float(inputd['lng'])
            lat = float(inputd['lat'])
        except:
            lng = float(inputd['longitude'])
            lat = float(inputd['latitude'])
    if lng < lat:
        return{'lng': str(lat),'lat': str(lng)}
    return{'lng': str(lng),'lat': str(lat)}

def langle(ang1, ang2):
    tmp = abs(ang1 - ang2)
    if tmp > 180:
        tmp = 360 - tmp
    return tmp

def angle(pos1, pos2):
    try:
        x1 = float(pos1['lat'])
    except:
        x1 = float(pos1['latitude'])
    try:
        y1 = float(pos1['lng'])
    except:
        y1 = float(pos1['longitude'])
    try:
        x2 = float(pos2['lat'])
    except:
        x2 = float(pos2['latitude'])
    try:
        y2 = float(pos2['lng'])
    except:
        y2 = float(pos2['longitude'])
    angle = 0.0
    dx = x2 - x1
    dy = y2 - y1
    if  x2 == x1:
        angle = pi / 2.0
        if  y2 == y1 :
            angle = 0.0
        elif y2 < y1 :
            angle = 3.0 * pi / 2.0
    elif x2 > x1 and y2 > y1:
        angle = atan(dx / dy)
    elif  x2 > x1 and  y2 < y1 :
        angle = pi / 2 + atan(-dy / dx)
    elif  x2 < x1 and y2 < y1 :
        angle = pi + atan(dx / dy)
    elif  x2 < x1 and y2 > y1 :
        angle = 3.0 * pi / 2.0 + atan(dy / -dx)
    return (angle * 180 / pi)


def haversine(pos1, pos2):
    try:
        lat1 = float(pos1['lat'])
    except:
        lat1 = float(pos1['latitude'])
    try:
        long1 = float(pos1['lng'])
    except:
        long1 = float(pos1['longitude'])
    try:
        lat2 = float(pos2['lat'])
    except:
        lat2 = float(pos2['latitude'])
    try:
        long2 = float(pos2['lng'])
    except:
        long2 = float(pos2['longitude'])

    degree_to_rad = float(pi / 180.0)

    d_lat = (lat2 - lat1) * degree_to_rad
    d_long = (long2 - long1) * degree_to_rad

    a = pow(sin(d_lat / 2), 2) + cos(lat1 * degree_to_rad) * cos(lat2 * degree_to_rad) * pow(sin(d_long / 2), 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    km = 6367 * c
    mi = 3956 * c

    return {"km": km, "miles": mi}