# __author__ : htzs
# __time__   : 19-5-6 下午4:02
import os

from django.http import HttpResponse, JsonResponse
from django.views.generic.base import View
# from utils import result
# from utils.vpm import UserAuth, RecTree, LiveView, Device_open, Device_close, Device_status
from django.core.cache import cache
import json
# from utils.vpm import RecTree, UserAuth, LiveView, DeviceOpen, DeviceClose, DeviceStatus, VideoView, DownLoadVideo
import time
import datetime

from quantong.settings import BASE_DIR
from utils import result
from utils.vpm import UserAuth, RecTree, UserAuth, LiveView, DeviceOpen, DeviceClose, DeviceStatus, VideoView, \
    DownLoadVideo
import logging

logger = logging.getLogger('django')


class AuthTokenView(UserAuth, View):
    """
    用户验证 获取token
    """

    def get(self, request):

        """
        获取阳光username password,请求token 并返回
        :param request:
        :return:
        响应码 (200:成功； 401:用户名或密码错误； 403:用户失效或禁用)
        """
        username = request.GET.get('loginName', '')
        password = request.GET.get('password', '')
        # 调用vpm接口,组合返回数据
        try:
            token = self.token_auth(username, password)
            if type(token) == str:
                logger.info('登录验证[成功][username:%s]' % username)
                # 登陆成功,保存token
                auth = {
                    'username': username,
                    'password': password,
                    'token': token
                }
                cache.clear()
                cache.set('token', token, 30 * 60)
                return result.result(message='成功', data=auth)
            else:
                return result.result(message='成功', data=token)

        except Exception as e:
            logger.error('登录验证[异常][message:%s]' % e)
            return result.un_auth()
        # print(token.json())


def switch_tree_format(rec_data):
    '''数据格式转换'''
    # print(rec_data)

    quantong_tree = {
        "groupList": [],
        "devList": []
    }

    def add_group(total):
        if total.__contains__("dataList"):
            for group in total["dataList"]:
                if group["menuName"] != "设备信息":
                    add_group(group)

                    object_added_into_grouplist = {}
                    object_added_into_grouplist["groupId"] = group["id"]
                    object_added_into_grouplist["groupName"] = group["name"]
                    object_added_into_grouplist["parentId"] = group["parentId"]
                    object_added_into_grouplist["clientId"] = "admin"
                    object_added_into_grouplist["groupType"] = "1"
                    quantong_tree["groupList"].append(object_added_into_grouplist)
                else:
                    break
        else:
            pass

    def add_camera(total):
        if total.__contains__("dataList"):
            for group in total["dataList"]:
                if group["menuName"] != "设备信息":
                    add_camera(group)
                else:
                    object_added_into_devlist = {}
                    object_added_into_devlist["devId"] = group["id"]
                    object_added_into_devlist["devName"] = group["name"]
                    object_added_into_devlist["status"] = group["status"]
                    object_added_into_devlist["clientId"] = "admin"
                    object_added_into_devlist["cameraList"] = []
                    if group.__contains__("dataList"):
                        for pipeline in group["dataList"]:
                            pipe = {}

                            pipe["cameraId"] = pipeline["id"]
                            pipe["cameraName"] = pipeline["name"]
                            pipe["status"] = pipeline["status"]
                            pipe["groupId"] = pipeline["parentId"]

                            object_added_into_devlist["cameraList"].append(pipe)

                    quantong_tree["devList"].append(object_added_into_devlist)
        else:
            pass

    for rec_data in rec_data["data"]:
        object_added_into_grouplist = {}
        object_added_into_grouplist["groupId"] = rec_data["id"]
        object_added_into_grouplist["groupName"] = rec_data["name"]
        object_added_into_grouplist["parentId"] = ""
        object_added_into_grouplist["clientId"] = "admin"
        object_added_into_grouplist["groupType"] = "1"
        quantong_tree["groupList"].append(object_added_into_grouplist)

        add_group(rec_data)
        add_camera(rec_data)

    return quantong_tree


class RecTreeView(RecTree, View):
    """
    处理设备树返回
    """

    def post(self, request):
        try:
            rec_data = self.rec_tree()
            if rec_data["code"] >= 400 or rec_data["code"] < 200:
                logger.error('获取设备树异常[message:%s]' % rec_data['code'])
                return JsonResponse(data=rec_data)
            else:
                quantong_tree = switch_tree_format(rec_data)
                logger.info('获取设备树成功[message:%s]' % rec_data['code'])
                return result.result(code=rec_data["code"], message="成功", data=quantong_tree)
        except:
            logger.warning('获取设备树失败')
            return result.params_error(message='请求错误,请重试...')


class DevLiveView(LiveView, View):
    """
    返回直播地址
    channelId
    protocol
    streamType
    """

    def post(self, request):
        try:
            temp = json.loads(request.body.decode())
            camera_id = temp["cameraId"]
            rec_data = self.live_view(camera_id=camera_id)
            if rec_data["code"] >= 400 or rec_data["code"] < 200:
                logger.error('返回直播地址异常[message:%s]' % rec_data['code'])
                return JsonResponse(data=rec_data)
            else:
                logger.info('返回直播地址成功[message:%s]' % rec_data['code'])
                url = rec_data['data']['address']
                return result.result(data={'url': url}, message='成功', code=rec_data["code"])

        except:
            logger.info('返回直播地址失败')
            return result.params_error(message='请求错误,请重试...请校验token')


class DeviceTurnOnOffView(DeviceOpen, DeviceClose, View):
    '''开启关闭设备'''

    def post(self, request):
        try:
            temp = json.loads(request.body.decode())
            camera_id = temp["cameraId"]
            on_or_off = int(temp["equipmentSwitch"])
            return_data = {
                "cameraProcessResult": "0",
                "errorCode": "",
                "errorDesc": ""
            }

            if on_or_off == 1:
                # 开启设备
                try:
                    rec_data = self.device_open(camera_id=camera_id)
                    # print(rec_data)
                    if rec_data["code"] != 200 and rec_data["code"] != 1002:
                        logger.warning('设备开启失败[message:%s]' % rec_data['message'])
                        return_data["cameraProcessResult"] = "2"
                        return_data["errorCode"] = str(rec_data["code"])
                        return_data["errorDesc"] = rec_data["message"]
                        return result.result(code=rec_data["code"], message="失败", data=return_data)
                    # elif rec_data['status'] == 400:
                    #     print(111111)
                    #     return result.result(code=rec_data["status"], message=rec_data['message'], data=return_data)
                    elif rec_data['code'] == 1002:
                        logger.warning('设备开启失败[message:%s]' % rec_data['message'])
                        return result.result(code=rec_data['code'], message='失败', data=rec_data)
                    else:
                        logger.info('设备开启成功[message:%s]' % rec_data['code'])
                        return_data["cameraProcessResult"] = "1"
                        return result.result(code=200, message="成功", data=return_data)
                except:
                    logger.warning('设备开启失败[message:%s]' % rec_data['message'])
                    return_data["cameraProcessResult"] = "2"
                    return_data["errorCode"] = str(rec_data["code"])
                    return_data["errorDesc"] = rec_data["message"]
                    return result.result(code=200, message='失败', data=return_data)

            elif on_or_off == 0:
                # 关闭设备
                try:
                    rec_data = self.device_close(camera_id=camera_id)
                    # print(rec_data)
                    if rec_data["code"] != 200 and rec_data["code"] != 1001:
                        logger.warning('设备关闭失败[message:%s]' % rec_data['message'])
                        return_data["cameraProcessResult"] = "4"
                        return_data["errorCode"] = str(rec_data["code"])
                        return_data["errorDesc"] = rec_data["message"]
                        return result.result(code=rec_data["code"], message="失败", data=return_data)
                    # elif rec_data['status'] == 400:
                    #     return result.result(code=rec_data["status"], message=rec_data['message'], data='')
                    elif rec_data['code'] == 1001:
                        logger.warning('设备关闭失败[message:%s]' % rec_data['message'])
                        return result.result(code=rec_data['code'], message='失败', data=rec_data)
                    else:
                        logger.info('设备关闭成功[message:%s]' % rec_data['code'])
                        return_data["cameraProcessResult"] = "3"
                        return result.result(code=200, message="成功", data=return_data)
                except:
                    logger.warning('设备关闭失败[message:%s]' % rec_data['message'])
                    return_data["cameraProcessResult"] = "4"
                    return_data["errorCode"] = str(rec_data["code"])
                    return_data["errorDesc"] = rec_data["message"]
                    return result.result(code=200, message='失败', data=return_data)
            else:
                return result.result(code=200, message="请传递正确参数", data='')
        except:
            logger.warning('开启关闭设备失败')
            # print(rec_data)
            return result.params_error(message='请求错误,请重试...请校验token是否过期')


class DeviceStatusView(DeviceStatus, View):
    '''查询运行状态'''

    # 调用的是vpm的查询通道信息的接口!!!!!!!
    def post(self, request):
        try:
            temp = json.loads(request.body.decode())
            camera_id = temp["cameraId"]
            rec_data = self.device_status(camera_id=camera_id)
            # print(rec_data)
            if rec_data["code"] >= 400 or rec_data["code"] < 200:
                logger.error('设备运行状态查询异常[status:%s]' % rec_data['code'])
                # logger.info('摄像头状态数据%s' % rec_data)
                return JsonResponse(data=rec_data)
            else:
                logger.info('设备运行状态查询成功[status:%s]' % rec_data['code'])
                # logger.info('摄像头状态数据%s' % rec_data)
                return_data = {
                    "cameraId": rec_data["data"]['channelId'],
                    "cameraState": -1
                }

                if rec_data["data"]["online"]:
                    if rec_data["data"]["flow"]:
                        # 通电在用
                        return_data["cameraState"] = 1

                    else:
                        # 禁用
                        return_data["cameraState"] = 3
                else:
                    # 通电未使用
                    return_data["cameraState"] = 2

                return result.result(code=rec_data["code"], message="成功", data=return_data)
        except Exception as e:
            logger.warning('设备运行状态查询失败[reason:%s]' % e)
            return result.params_error(message='请求错误,请重试...')


class PlayBackView(VideoView, View):
    '''视频录像回放地址'''

    def post(self, request):
        try:
            camera_id = json.loads(request.body.decode().replace("'", "\"")).get('cameraId')
            begin_time = json.loads(request.body.decode().replace("'", "\"")).get('beginTime')
            end_time = json.loads(request.body.decode().replace("'", "\"")).get('endTime')
            begin_time = int(begin_time)
            end_time = int(end_time)
            if begin_time == 0:
                begin_time = int(time.time()) - int(time.time() - time.timezone) % 86400
                # print(begin_time)
                if end_time == 0:
                    try:
                        camera_id1 = camera_id
                        rec_data1 = self.get_file(camera_id=camera_id1)
                        # print(rec_data1)
                        # 获取录像文件信息,查询录像文件在什么范围内有,然后下载和回放才有效
                        if rec_data1['message'] == "录像信息为空" or rec_data1['data'] == {} or rec_data1['data'] == '':
                            logger.error('设备录像回放地址查询异常[data:%s]' % rec_data1['data'])
                            return result.result(code=rec_data1['code'], data=rec_data1, message='查询录像失败')
                            # end_time = rec_data1['data']['cList'][-1]['nEnd']
                        else:
                            # 当success,以及data有数据时候,查询录像文件的范围
                            # logger.info('设备录像地址正常[data:%s]' % rec_data1['data'])
                            logger.info('录像文件列表%s' % rec_data1['data']['cList'])
                            begin_time = rec_data1['data']['cList'][-1]['nStart']
                            end_time = rec_data1['data']['cList'][-1]['nEnd']
                            rec_data = self.video_view(camera_id=camera_id, begin_time=begin_time, end_time=end_time)
                            logger.error('录像生成情况:%s' % rec_data['message'])
                            url = rec_data['data']['address']
                            logger.info('设备录像地址正常[data:%s]' % rec_data['data'])
                            return_data = {
                                "data": {
                                    "list": [{"beginTime": str(begin_time)}, {"endTime": str(end_time)},
                                             {"playbackUrl": url}],
                                    "total": 1,
                                    "totalTimeUrl": url
                                },
                                "isWarning": 0
                            }
                            return result.result(data=return_data, message="成功", code=rec_data["code"])
                            # return JsonResponse(data=rec_data)

                    except Exception as e:
                        logger.warning('设备运行状态查询失败[message:%s]' % e)
                        return result.result(message='当前时间段没有录像信息或者录像文件生成失败', data={})
                        # print(e)
            if begin_time != 0 and end_time == 0:
                day = time.localtime(begin_time)
                end_time = begin_time - (day[-4] + day[-5] * 60 + day[-6] * 3600) + 86400
            rec_data = self.video_view(camera_id=camera_id, begin_time=begin_time, end_time=end_time)

            if rec_data["code"] >= 400 or rec_data["code"] < 200:
                logger.error('设备录像回放地址查询异常[data:%s]' % rec_data['data'])
                return JsonResponse(data=rec_data)
            else:
                url = rec_data['data']['address']
                logger.info('设备录像地址正常[data:%s]' % rec_data['data'])
                return_data = {
                    "data": {
                        "list": [{"beginTime": str(begin_time)}, {"endTime": str(end_time)}, {"playbackUrl": url}],
                        "total": 1,
                        "totalTimeUrl": url
                    },
                    "isWarning": 0
                }
                return result.result(data=return_data, message="成功", code=rec_data["code"])
        except Exception as e:
            # print(rec_data)
            logger.warning('设备运行状态查询失败[message:%s]' % e)
            return result.params_error(message='请求错误,请重试...')


class DownLoadView(DownLoadVideo, View):
    '''视频下载'''

    def post(self, request):

        try:
            camera_id = json.loads(request.body.decode().replace("'", "\"")).get('cameraId')
            begin_time = json.loads(request.body.decode().replace("'", "\"")).get('beginTime')
            end_time = json.loads(request.body.decode().replace("'", "\"")).get('endTime')
            begin_time = int(begin_time)
            end_time = int(end_time)
            # print(end_time)
            # 加判断,如果传递来的都是0,需要获取当天零点到当前的时间来算,
            # 没有传递0,就按照实际时间戳来计算
            if begin_time == 0:
                begin_time = int(time.time()) - int(time.time() - time.timezone) % 86400
                if end_time == 0:
                    try:
                        camera_id1 = camera_id
                        rec_data1 = self.get_file(camera_id=camera_id1)
                        # print(rec_data1)
                        # 获取录像文件信息,查询录像文件在什么范围内有,然后下载和回访才有效
                        if rec_data1['message'] == "录像信息为空" or rec_data1['data'] == {} or rec_data1['data'] == '':
                            # print(os.path.join(os.path.dirname(BASE_DIR), "quantong/logs/quantong.log"))
                            logger.error('设备下载查询异常[data:%s]' % rec_data1['data'])
                            return result.result(data=rec_data1['data'], message=rec_data1['message'],
                                                 code=rec_data1['code'])
                            # end_time = rec_data1['data']['cList'][-1]['nEnd']
                        else:
                            # 当success,以及data有数据时候,查询录像文件的范围
                            logger.info('设备下载查询正常[data:%s]' % rec_data1['data'])
                            begin_time = rec_data1['data']['cList'][-1]['nStart']
                            end_time = rec_data1['data']['cList'][-1]['nEnd']
                            rec_data = self.down_load(camera_id=camera_id, begin_time=begin_time, end_time=end_time)
                            logger.info(rec_data)
                            if rec_data["code"] >= 400 or rec_data["code"] < 200 or rec_data[
                                'message'] == '在此时间段内无对应的录像文件':
                                return JsonResponse(data=rec_data)
                            else:
                                url = rec_data["data"]['address']
                                return_data = {
                                    "videoDownloadFormat": url
                                }
                                return result.result(data=return_data, message="成功", code=rec_data["code"])

                    except Exception as e:
                        logger.warning('设备下载查询失败[reason:%s]' % e)
                        # print(os.path.join(os.path.dirname(BASE_DIR), "quantong/logs/quantong.log"))
                        return result.params_error(message='请求错误,请重试...')



            else:
                day = time.localtime(begin_time)
                end_time = begin_time - (day[-4] + day[-5] * 60 + day[-6] * 3600) + 86400
                rec_data = self.down_load(camera_id, int(begin_time), int(end_time))
                print(rec_data)
                if rec_data["code"] >= 400 or rec_data["code"] < 200 or rec_data['message'] == '在此时间段内无对应的录像文件':
                    logger.error('设备下载查询异常[data:%s]' % rec_data['data'])
                    return JsonResponse(data=rec_data)
                else:
                    logger.info('设备下载查询正常[data:%s]' % rec_data['data'])

                    url = rec_data["data"]['address']
                    return_data = {
                        "videoDownloadFormat": url
                    }
                    return result.result(data=return_data, message="成功", code=rec_data["code"])
        except Exception as e:
            logger.warning('设备下载查询失败[message:%s]' % e)
            return result.params_error(message='请求错误,请重试...')
