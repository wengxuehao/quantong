#  _*_ coding:utf-8 _*_
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
        响应码 (200:success； 401:用户名或密码错误； 403:用户失效或禁用)
        """
        try:
            username = request.GET.get('loginName', '')
            password = request.GET.get('password', '')
            # 调用vpm接口,组合返回数据
            try:
                token = self.token_auth(username, password)
                if type(token) == str:
                    logger.info('login_verify[success][username:%s]' % username)
                    # 登陆success,保存token
                    auth = {
                        'username': username,
                        'password': password,
                        'token': token
                    }
                    cache.clear()
                    cache.set('token', token, 30 * 60)
                    return result.result(message='success', data=auth)
                else:
                    return result.result(message='success', data=token)

            except Exception as e:
                logger.error('login_verify[error][message:%s]' % e)
                return result.un_auth()
            # print(token.json())
        except:
            return result.result(message='请提交信息')


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
                logger.error('get_device_tree-error[message:%s]' % rec_data['code'])
                return JsonResponse(data=rec_data)
            else:
                quantong_tree = switch_tree_format(rec_data)
                logger.info('get_device_tree-success[message:%s]' % rec_data['code'])
                return result.result(code=rec_data["code"], message="success", data=quantong_tree)
        except:
            logger.warning('get_device_tree-warning')
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
                logger.error('return_live_address-error[message:%s]' % rec_data['code'])
                return JsonResponse(data=rec_data)
            else:
                logger.info('return_live_address-success[message:%s]' % rec_data['code'])
                url = rec_data['data']['address']
                return result.result(data={'url': url}, message='success', code=rec_data["code"])

        except:
            logger.info('return_live_address-warning')
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
                        logger.warning('device_open_fail-[message:%s]' % rec_data['message'])
                        return_data["cameraProcessResult"] = "2"
                        return_data["errorCode"] = str(rec_data["code"])
                        return_data["errorDesc"] = rec_data["message"]
                        return result.result(code=rec_data["code"], message="失败", data=return_data)
                    # elif rec_data['status'] == 400:
                    #     print(111111)
                    #     return result.result(code=rec_data["status"], message=rec_data['message'], data=return_data)
                    elif rec_data['code'] == 1002:
                        logger.warning('device_open_fail-[message:%s]' % rec_data['message'])
                        return result.result(code=rec_data['code'], message='失败', data=rec_data)
                    else:
                        logger.info('device_open-success[message:%s]' % rec_data['code'])
                        return_data["cameraProcessResult"] = "1"
                        return result.result(code=200, message="success", data=return_data)
                except:
                    logger.warning('device_open_fail-[message:%s]' % rec_data['message'])
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
                        logger.warning('device_close_fail[message:%s]' % rec_data['message'])
                        return_data["cameraProcessResult"] = "4"
                        return_data["errorCode"] = str(rec_data["code"])
                        return_data["errorDesc"] = rec_data["message"]
                        return result.result(code=rec_data["code"], message="失败", data=return_data)
                    # elif rec_data['status'] == 400:
                    #     return result.result(code=rec_data["status"], message=rec_data['message'], data='')
                    elif rec_data['code'] == 1001:
                        logger.warning('device_close_fail[message:%s]' % rec_data['message'])
                        return result.result(code=rec_data['code'], message='失败', data=rec_data)
                    else:
                        logger.info('device_close-success[message:%s]' % rec_data['code'])
                        return_data["cameraProcessResult"] = "3"
                        return result.result(code=200, message="success", data=return_data)
                except:
                    logger.warning('device_close_fail[message:%s]' % rec_data['message'])
                    return_data["cameraProcessResult"] = "4"
                    return_data["errorCode"] = str(rec_data["code"])
                    return_data["errorDesc"] = rec_data["message"]
                    return result.result(code=200, message='失败', data=return_data)
            else:
                return result.result(code=200, message="请传递正确参数", data='')
        except:
            logger.warning('device_closewarning')
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
                logger.error('get_device_statuserror[status:%s]' % rec_data['code'])
                # logger.info('摄像头状态数据%s' % rec_data)
                return JsonResponse(data=rec_data)
            else:
                logger.info('get_device_statussuccess[status:%s]' % rec_data['code'])
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

                return result.result(code=rec_data["code"], message="success", data=return_data)
        except Exception as e:
            logger.warning('get_device_status_fail[reason:%s]' % e)
            return result.params_error(message='请求错误,请重试...')


class PlayBackView(VideoView, View):
    '''视频录像回放地址'''

    def post(self, request):
        try:
            camera_id = json.loads(request.body.decode().replace("'", "\"")).get('cameraId')
            begin_time = json.loads(request.body.decode().replace("'", "\"")).get('beginTime')
            end_time = json.loads(request.body.decode().replace("'", "\"")).get('endTime')
            begin_time_sub = int(begin_time)
            end_time_sub = int(end_time)
            if begin_time_sub == 0 and end_time_sub == 0:
                # 当传递都为0时候，则为当天的零点到明天零点
                begin_time_zero = int(time.time()) - int(time.time() - time.timezone) % 86400
                end_time_zero = begin_time_zero + 86400
                try:
                    camera_id_file = camera_id
                    rec_data_file = self.get_file(camera_id=camera_id_file)
                    print(rec_data_file)
                    nStart = rec_data_file['data']['cList'][0]['nStart']
                    nEnd = rec_data_file['data']['cList'][0]['nEnd']
                    if begin_time_zero < nStart and end_time_zero > nEnd:

                        # 当传递的区间左边和右边都大于有的区间，只能返回有的区间
                        if rec_data_file['message'] == "录像信息为空" or rec_data_file['data'] == {} or rec_data_file[
                            'data'] == '':
                            logger.error('get_device_video_error[data:%s]' % rec_data_file['data'])
                            return result.result(code=rec_data_file['code'], data=rec_data_file,
                                                 message='查询录像error请校验录像文件信息')
                        else:
                            rec_data = self.video_view(camera_id=camera_id, begin_time=nStart,
                                                       end_time=nEnd)
                            if rec_data['data'] == '' or rec_data['message'] == '在此时间段内无对应的录像文件':
                                logger.error('video_list_message:%s' % rec_data['message'])
                                return result.result(code=rec_data['code'], data=rec_data_file['data']['cList'],
                                                     message=rec_data['message'])
                            else:
                                url = rec_data['data']['address']
                                logger.info('get_device_video[data:%s]' % rec_data['data'])
                                return_data = {
                                    "data": {
                                        "list": [{"beginTime": str(begin_time)}, {"endTime": str(end_time)},
                                                 {"playbackUrl": url}],
                                        "total": 1,
                                        "totalTimeUrl": url
                                    },
                                    "isWarning": 0
                                }
                                return result.result(data=return_data, message="success", code=rec_data["code"])

                    elif begin_time_zero < nStart:
                        # 当左侧超过可用区间
                        if rec_data_file['message'] == "录像信息为空" or rec_data_file['data'] == {} or rec_data_file[
                            'data'] == '':
                            logger.error('get_device_video_error[data:%s]' % rec_data_file['data'])
                            return result.result(code=rec_data_file['code'], data=rec_data_file,
                                                 message='查询录像error请校验录像文件信息')
                        else:
                            rec_data = self.video_view(camera_id=camera_id, begin_time=nStart,
                                                       end_time=end_time_zero)
                            # print(rec_data)
                            if rec_data['data'] == '' or rec_data['message'] == '在此时间段内无对应的录像文件':
                                logger.error('video_list_message:%s' % rec_data['message'])
                                return result.result(code=rec_data['code'], data=rec_data_file['data']['cList'],
                                                     message=rec_data['message'])
                            else:
                                url = rec_data['data']['address']
                                logger.info('get_device_video[data:%s]' % rec_data['data'])
                                return_data = {
                                    "data": {
                                        "list": [{"beginTime": str(begin_time)}, {"endTime": str(end_time)},
                                                 {"playbackUrl": url}],
                                        "total": 1,
                                        "totalTimeUrl": url
                                    },
                                    "isWarning": 0
                                }
                                return result.result(data=return_data, message="success", code=rec_data["code"])
                    elif end_time_zero > nEnd:
                        # 当右侧超过可用区间
                        if rec_data_file['message'] == "录像信息为空" or rec_data_file['data'] == {} or rec_data_file[
                            'data'] == '':
                            logger.error('get_device_video_error[data:%s]' % rec_data_file['data'])
                            return result.result(code=rec_data_file['code'], data=rec_data_file,
                                                 message='查询录像error请校验录像文件信息')
                        else:
                            rec_data = self.video_view(camera_id=camera_id, begin_time=begin_time_zero,
                                                       end_time=nEnd)
                            # print(rec_data)
                            if rec_data['data'] == '' or rec_data['message'] == '在此时间段内无对应的录像文件':
                                logger.error('video_list_message:%s' % rec_data['message'])
                                return result.result(code=rec_data['code'], data=rec_data_file['data']['cList'],
                                                     message=rec_data['message'])
                            else:
                                url = rec_data['data']['address']
                                logger.info('get_device_video[data:%s]' % rec_data['data'])
                                return_data = {
                                    "data": {
                                        "list": [{"beginTime": str(begin_time)}, {"endTime": str(end_time)},
                                                 {"playbackUrl": url}],
                                        "total": 1,
                                        "totalTimeUrl": url
                                    },
                                    "isWarning": 0
                                }
                                return result.result(data=return_data, message="success", code=rec_data["code"])
                except Exception as e:
                    logger.warning('get_video_fail[message:%s]' % e)
                    return result.result(message='当前时间段没有录像信息或者录像文件生成失败', data={})
                    # print(e)
            elif begin_time_sub != 0 and end_time_sub == 0:
                camera_id_file = camera_id
                rec_data_file = self.get_file(camera_id=camera_id_file)
                nStart = rec_data_file['data']['cList'][0]['nStart']
                nEnd = rec_data_file['data']['cList'][0]['nEnd']
                # 开始时间是提供来的，结束时间是明天零点
                begin_time_zero = int(time.time()) - int(time.time() - time.timezone) % 86400
                end_time_zero = begin_time_zero + 86400
                if begin_time_sub < nStart and end_time_zero > nEnd:
                    # 左右区间都大于可用区间情况下
                    rec_data = self.video_view(camera_id=camera_id, begin_time=nStart, end_time=nEnd)
                    if rec_data["code"] >= 400 or rec_data["code"] < 200:
                        logger.error('get_device_video_error[data:%s]' % rec_data['data'])
                        return result.result(code=rec_data['code'], data=rec_data_file['data']['cList'],
                                             message=rec_data['message'])
                    else:
                        url = rec_data['data']['address']
                        logger.info('get_device_video[data:%s]' % rec_data['data'])
                        return_data = {
                            "data": {
                                "list": [{"beginTime": str(begin_time)}, {"endTime": str(end_time)},
                                         {"playbackUrl": url}],
                                "total": 1,
                                "totalTimeUrl": url
                            },
                            "isWarning": 0
                        }
                        return result.result(data=return_data, message="success", code=rec_data["code"])
                elif begin_time_sub < nStart:
                    # 左侧区间不在可用区间内
                    rec_data = self.video_view(camera_id=camera_id, begin_time=nStart, end_time=end_time_zero)
                    if rec_data["code"] >= 400 or rec_data["code"] < 200:
                        logger.error('get_device_video_error[data:%s]' % rec_data['data'])
                        return result.result(code=rec_data['code'], data=rec_data_file['data']['cList'],
                                             message=rec_data['message'])
                    else:
                        url = rec_data['data']['address']
                        logger.info('get_device_video[data:%s]' % rec_data['data'])
                        return_data = {
                            "data": {
                                "list": [{"beginTime": str(begin_time)}, {"endTime": str(end_time)},
                                         {"playbackUrl": url}],
                                "total": 1,
                                "totalTimeUrl": url
                            },
                            "isWarning": 0
                        }
                        return result.result(data=return_data, message="success", code=rec_data["code"])
                elif end_time_zero > nEnd:
                    # 右侧区间不在可用区间内
                    rec_data = self.video_view(camera_id=camera_id, begin_time=begin_time_sub, end_time=nEnd)
                    if rec_data["code"] >= 400 or rec_data["code"] < 200:
                        logger.error('get_device_video_error[data:%s]' % rec_data['data'])
                        return result.result(code=rec_data['code'], data=rec_data_file['data']['cList'],
                                             message=rec_data['message'])
                    else:
                        url = rec_data['data']['address']
                        logger.info('get_device_video[data:%s]' % rec_data['data'])
                        return_data = {
                            "data": {
                                "list": [{"beginTime": str(begin_time)}, {"endTime": str(end_time)},
                                         {"playbackUrl": url}],
                                "total": 1,
                                "totalTimeUrl": url
                            },
                            "isWarning": 0
                        }
                        return result.result(data=return_data, message="success", code=rec_data["code"])
            elif begin_time_sub == 0 and end_time_sub != 0:
                camera_id_file = camera_id
                rec_data_file = self.get_file(camera_id=camera_id_file)
                nStart = rec_data_file['data']['cList'][0]['nStart']
                nEnd = rec_data_file['data']['cList'][0]['nEnd']
                # 当提交来的开始时间是当天零点，结束时间是提交来的
                if begin_time_sub < nStart and end_time_sub > nEnd:
                    # TODO 两侧区间都不在可用范围内
                    rec_data = self.video_view(camera_id=camera_id, begin_time=nStart, end_time=nEnd)
                    if rec_data["code"] >= 400 or rec_data["code"] < 200:
                        logger.error('get_device_video_error[data:%s]' % rec_data['data'])
                        return result.result(code=rec_data['code'], data=rec_data_file['data']['cList'],
                                             message=rec_data['message'])
                    else:
                        rec_data = self.video_view(camera_id=camera_id, begin_time=begin_time_sub,
                                                   end_time=end_time_sub)
                        url = rec_data['data']['address']
                        logger.info('get_device_video[data:%s]' % rec_data['data'])
                        return_data = {
                            "data": {
                                "list": [{"beginTime": str(begin_time)}, {"endTime": str(end_time)},
                                         {"playbackUrl": url}],
                                "total": 1,
                                "totalTimeUrl": url
                            },
                            "isWarning": 0
                        }
                        return result.result(data=return_data, message="success", code=rec_data["code"])
                elif begin_time_sub < nStart:
                    # 当左侧不在范围内
                    rec_data = self.video_view(camera_id=camera_id, begin_time=nStart, end_time=end_time_sub)

                    if rec_data["code"] >= 400 or rec_data["code"] < 200:
                        logger.error('get_device_video_error[data:%s]' % rec_data['data'])
                        return result.result(code=rec_data['code'], data=rec_data_file['data']['cList'],
                                             message=rec_data['message'])
                    else:
                        url = rec_data['data']['address']
                        logger.info('get_device_video[data:%s]' % rec_data['data'])
                        return_data = {
                            "data": {
                                "list": [{"beginTime": str(begin_time)}, {"endTime": str(end_time)},
                                         {"playbackUrl": url}],
                                "total": 1,
                                "totalTimeUrl": url
                            },
                            "isWarning": 0
                        }
                        return result.result(data=return_data, message="success", code=rec_data["code"])
                elif end_time_sub > nEnd:
                    # 当右侧不在范围内
                    begin_time_zero = int(time.time()) - int(time.time() - time.timezone) % 86400
                    rec_data = self.video_view(camera_id=camera_id, begin_time=nStart, end_time=nEnd)
                    if rec_data["code"] >= 400 or rec_data["code"] < 200:
                        logger.error('get_device_video_error[data:%s]' % rec_data['data'])
                        return result.result(code=rec_data['code'], data=rec_data_file['data']['cList'],
                                             message=rec_data['message'])
                    else:
                        rec_data = self.video_view(camera_id=camera_id, begin_time=begin_time_sub,
                                                   end_time=end_time_sub)
                        url = rec_data['data']['address']
                        logger.info('get_device_video[data:%s]' % rec_data['data'])
                        return_data = {
                            "data": {
                                "list": [{"beginTime": str(begin_time)}, {"endTime": str(end_time)},
                                         {"playbackUrl": url}],
                                "total": 1,
                                "totalTimeUrl": url
                            },
                            "isWarning": 0
                        }
                        return result.result(data=return_data, message="success", code=rec_data["code"])
            else:
                # 当传递的时间两侧都不为0的情况
                camera_id_file = camera_id
                rec_data_file = self.get_file(camera_id=camera_id_file)
                nStart = rec_data_file['data']['cList'][0]['nStart']
                nEnd = rec_data_file['data']['cList'][0]['nEnd']
                if begin_time_sub < nStart and end_time_sub > nEnd:
                    # 当传递的两侧都是不在范围内的
                    rec_data = self.video_view(camera_id=camera_id, begin_time=nStart, end_time=nEnd)
                    if rec_data['data'] == '':
                        return result.result(data=rec_data)
                    url = rec_data['data']['address']
                    logger.info('get_device_video[data:%s]' % rec_data['data'])
                    return_data = {
                        "data": {
                            "list": [{"beginTime": str(nStart)}, {"endTime": str(nEnd)}, {"playbackUrl": url}],
                            "total": 1,
                            "totalTimeUrl": url
                        },
                        "isWarning": 0
                    }
                    return result.result(data=return_data, message="success", code=rec_data["code"])
                elif begin_time_sub < nStart:
                    # 当左侧不在范围内
                    rec_data = self.video_view(camera_id=camera_id, begin_time=nStart, end_time=end_time_sub)
                    if rec_data['data'] == '':
                        return result.result(data=rec_data)
                    url = rec_data['data']['address']
                    logger.info('get_device_video[data:%s]' % rec_data['data'])
                    return_data = {
                        "data": {
                            "list": [{"beginTime": str(begin_time)}, {"endTime": str(end_time)}, {"playbackUrl": url}],
                            "total": 1,
                            "totalTimeUrl": url
                        },
                        "isWarning": 0
                    }
                    return result.result(data=return_data, message="success", code=rec_data["code"])
                elif end_time_sub > nEnd:
                    # 当右侧不在范围内
                    rec_data = self.video_view(camera_id=camera_id, begin_time=begin_time_sub, end_time=nEnd)
                    if rec_data['data'] == '':
                        return result.result(data=rec_data)
                    url = rec_data['data']['address']
                    logger.info('get_device_video[data:%s]' % rec_data['data'])
                    return_data = {
                        "data": {
                            "list": [{"beginTime": str(begin_time_sub)}, {"endTime": str(nEnd)}, {"playbackUrl": url}],
                            "total": 1,
                            "totalTimeUrl": url
                        },
                        "isWarning": 0
                    }
                    return result.result(data=return_data, message="success", code=rec_data["code"])
                else:
                    # 当传递的两个时间都在范围内的
                    rec_data = self.video_view(camera_id=camera_id, begin_time=begin_time_sub, end_time=end_time_sub)
                    if rec_data['data'] == '':
                        return result.result(data=rec_data)
                    url = rec_data['data']['address']
                    logger.info('get_device_video[data:%s]' % rec_data['data'])
                    return_data = {
                        "data": {
                            "list": [{"beginTime": str(begin_time_sub)}, {"endTime": str(end_time_sub)}, {"playbackUrl": url}],
                            "total": 1,
                            "totalTimeUrl": url
                        },
                        "isWarning": 0
                    }
                    return result.result(data=return_data, message="success", code=rec_data["code"])
        except Exception as e:
            logger.warning('get_video_fail[message:%s]' % e)
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
                        camera_id_file = camera_id
                        rec_data_file = self.get_file(camera_id=camera_id_file)
                        # print(rec_data_file)
                        # 获取录像文件信息,查询录像文件在什么范围内有,然后下载和回访才有效
                        if rec_data_file['message'] == "录像信息为空" or rec_data_file['data'] == {} or rec_data_file[
                            'data'] == '':
                            logger.error('device_download_error[data:%s]' % rec_data_file['data'])
                            return result.result(data=rec_data_file['data'], message='设备下载文件error',
                                                 code=rec_data_file['code'])
                            # end_time = rec_data_file['data']['cList'][-1]['nEnd']
                        else:
                            # 当success,以及data有数据时候,查询录像文件的范围
                            logger.info('device_download_normal[data:%s]' % rec_data_file['data'])
                            begin_time = rec_data_file['data']['cList'][-1]['nStart']
                            end_time = rec_data_file['data']['cList'][-1]['nEnd']
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
                                return result.result(data=return_data, message="success", code=rec_data["code"])

                    except Exception as e:
                        logger.warning('device_download_fail[reason:%s]' % e)
                        # print(os.path.join(os.path.dirname(BASE_DIR), "quantong/logs/quantong.log"))
                        return result.params_error(message='请求错误,请重试...')



            else:
                day = time.localtime(begin_time)
                end_time = begin_time - (day[-4] + day[-5] * 60 + day[-6] * 3600) + 86400
                rec_data = self.down_load(camera_id, int(begin_time), int(end_time))
                print(rec_data)
                if rec_data["code"] >= 400 or rec_data["code"] < 200 or rec_data['message'] == '在此时间段内无对应的录像文件':
                    logger.error('device_download_error[data:%s]' % rec_data['data'])
                    return JsonResponse(data=rec_data)
                else:
                    logger.info('device_download_normal[data:%s]' % rec_data['data'])

                    url = rec_data["data"]['address']
                    return_data = {
                        "videoDownloadFormat": url
                    }
                    return result.result(data=return_data, message="success", code=rec_data["code"])
        except Exception as e:
            logger.warning('device_download_fail[message:%s]' % e)
            return result.params_error(message='请求错误,请重试...')
