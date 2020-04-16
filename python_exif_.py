from urllib import parse
import exifread
import re
import json
import requests
import sys
import hashlib


def latitude_and_longitude_convert_to_decimal_system(*arg):
    """
    经纬度转为小数, 作者尝试适用于iphone6、ipad2以上的拍照的照片，
    :param arg:
    :return: 十进制小数
    """
    return float(arg[0]) + ((float(arg[1]) + (float(arg[2].split('/')[0]) / float(arg[2].split('/')[-1]) / 60)) / 60)


# 获取图片的所有信息
def find_GPS_image(pic_path):
    GPS = {}
    date = ''
    with open(pic_path, 'rb') as f:
        tags = exifread.process_file(f)
        # print(tags.items())
        for tag, value in tags.items():
            if re.match('Image Make', tag):
                print('[*] 品牌信息: ' + str(value))
            if re.match('Image Model', tag):
                print('[*] 具体型号: ' + str(value))
            if re.match('EXIF LensModel', tag):
                print('[*] 摄像头信息: ' + str(value))
            if re.match('GPS GPSLatitudeRef', tag):
                GPS['GPSLatitudeRef'] = str(value)
            elif re.match('GPS GPSLongitudeRef', tag):
                GPS['GPSLongitudeRef'] = str(value)
            elif re.match('GPS GPSAltitudeRef', tag):
                GPS['GPSAltitudeRef'] = str(value)
            elif re.match('GPS GPSLatitude', tag):
                try:
                    match_result = re.match('\[(\w*),(\w*),(\w.*)/(\w.*)\]', str(value)).groups()
                    GPS['GPSLatitude'] = int(match_result[0]), int(match_result[1]), int(match_result[2])
                except:
                    deg, min, sec = [x.replace(' ', '') for x in str(value)[1:-1].split(',')]
                    GPS['GPSLatitude'] = latitude_and_longitude_convert_to_decimal_system(deg, min, sec)
            elif re.match('GPS GPSLongitude', tag):
                try:
                    match_result = re.match('\[(\w*),(\w*),(\w.*)/(\w.*)\]', str(value)).groups()
                    GPS['GPSLongitude'] = int(match_result[0]), int(match_result[1]), int(match_result[2])
                except:
                    deg, min, sec = [x.replace(' ', '') for x in str(value)[1:-1].split(',')]
                    GPS['GPSLongitude'] = latitude_and_longitude_convert_to_decimal_system(deg, min, sec)
            elif re.match('GPS GPSAltitude', tag):
                GPS['GPSAltitude'] = str(value)
                print('[*] GPS高度: ' + str(value))
            elif re.match('GPS GPSImgDirectionRef', tag):
                GPS['GPSImgDirectionRef'] = str(value)
                print('[*] GPS方向Ref: ' + str(value))
            elif re.match('GPS GPSImgDirection', tag):
                GPS['GPSImgDirection'] = str(value)
                print('[*] GPS方向: ' + str(value))
            elif re.match('.*Date.*', tag):
                date = str(value)
    # print({'GPS_information': GPS, 'date_information': date})
    print('[*] 拍摄时间: ' + date)
    return {'GPS_information': GPS, 'date_information': date}


# 百度地图逆地址解析 获取位置信息
def find_address_from_GPS(GPS):
    """
    使用Geocoding API把经纬度坐标转换为结构化地址。
    :param GPS:
    :return:
    """
    httpHead = 'http://api.map.baidu.com{0}{1}{2}'  # http请求头 提取出来
    secret_key = ''  # 百度地图应用ak
    sk = ''  # 百度地图用来生成sn的sk密钥
    if not GPS['GPS_information']:
        return '该照片无GPS信息'
    lat, lng = GPS['GPS_information']['GPSLatitude'], GPS['GPS_information']['GPSLongitude']
    print('[*] 经度: ' + str(lat) + ', 纬度: ' + str(lng))
    baidu_map_api = "/reverse_geocoding/v3/?ak={0}&output=json&coordtype=wgs84ll&location={1},{2}".format(
        secret_key, lat, lng)  # 请求参数拼接
    # 对queryStr进行转码，safe内的保留字符不转换
    encodedStr = parse.quote(baidu_map_api, safe="/:=&?#+!$,;'@()*[]")
    # 在最后直接追加上sk密钥
    rawStr = encodedStr + sk
    # md5加密得出来sn密钥用来请求百度地图
    sn = hashlib.md5(parse.quote_plus(rawStr).encode("utf8")).hexdigest()
    print(sn)
    url = httpHead.format(baidu_map_api, "&sn=", sn)  # 请求地址拼接
    print("baidugetdizhi", url)
    response = requests.get(url)  # 请求指定地址
    # print(response.text);
    v = json.loads(response.text)  # 对返回json信息进行转译处理
    print(v)
    if v["status"] != 0:  # 百度api文档指定status为0的时候解析成功其他状态码都是错误信息 打印并返回
        print(v["message"])
        return v["message"]
    else:
        baidu_map_address = json.loads(response.text)  # json处理
        formatted_address = baidu_map_address["result"]["formatted_address"]  # 获取指定信息 参考百度开发者api文档
        return formatted_address


if __name__ == '__main__':
    GPS_info = find_GPS_image("d:/1_p/66_exif/project/heic_jpg/2020_03_30_14_42_IMG_0570_600278349.jpg")  # 指定一张图片
    address = find_address_from_GPS(GPS_info)
    print('[*] 位置信息: ' + address)  # 打印信息

