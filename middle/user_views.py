# __author__ : htzs
# __time__   : 19-5-6 下午4:02
import json
import time
from pprint import pprint

from django.http import HttpResponse, JsonResponse
from django.views.generic.base import View
# from utils import result
# from utils.vpm import UserAuth, RecTree, LiveView, Device_open, Device_close, Device_status
from django.core.cache import cache

# import result
from utils.vpm import RecTree, UserAuth, LiveView, Device_status, VideoView, DownLoad_Video, \
    Device_open_close

from utils import result


# from vpm import DownLoad_Video, UserAuth,RecTree,LiveView,Device_open,Device_status,VideoView


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
        token = self.token_auth(username, password)
        # print(token.json())
        if type(token) == str:
            # 登陆成功,保存token
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
            #
            # data = self.token_auth(username, password)
            # return result.result(message=data)


class RecTreeView(RecTree, View):
    """
    处理设备树返回
    """

    def get(self, request):
        rec_data = self.rec_tree()
        # print(rec_data)
        # data_list = rec_data['data'][0]['dataList']
        # pprint(rec_data['data'][0]['dataList'])
        try:
            data = rec_data['data'][0]
            return JsonResponse(data=data)
        except:
            code = rec_data['code']
            message = rec_data['message']
            data = {
                "errorCode": code,
                "errorDesc": message
            }
            return result.result(data=data)
        # else:
        #     rec_data = rec_data
        #     return result.result(data=rec_data)


class DevLiveView(LiveView, View):
    """
    返回直播地址
    channelId
    protocol
    streamType
    """

    def get(self, request):
        camera_id = request.GET.get('camera_id', '')
        receve_data = self.live_view(camera_id=camera_id)
        try:

            receve_data = receve_data
            url = receve_data['data']['address']
            return result.result(data={'url': url}, message='success')
            # return JsonResponse(data=receve_data)
        except Exception:
            code = receve_data['code']
            message = receve_data['message']
            data = {
                "errorCode": code,
                "errorDesc": message
            }
            return result.result(data=data)


class Deviceopen_close_View(Device_open_close, View):
    '''开启设备'''

    # 返回cameraProcessResult，errorCode，errorDesc

    def post(self, request):
        try:
            camera_id = json.loads(request.body.decode().replace("'", "\"")).get('camera_id')
            equipmentSwitch = json.loads(request.body.decode().replace("'", "\"")).get('equipmentSwitch')
            if equipmentSwitch == "1":
                # 开启设备
                data = self.device_open(camera_id=camera_id)
                code = data['code']
                message = data['message']
                errorCode = code
                errorDesc = message
                if code == 200:
                    '''开启设备成功'''
                    cameraProcessResult = 1
                    data = {
                        "cameraProcessResult": cameraProcessResult,
                        "errorCode": errorCode,
                        "errorDesc": errorDesc
                    }
                    return JsonResponse(data=data)
                else:
                    '''开启设备失败'''
                    cameraProcessResult = 2
                    data = {
                        "cameraProcessResult": cameraProcessResult,
                        "errorCode": errorCode,
                        "errorDesc": errorDesc
                    }
                    return JsonResponse(data=data)
            else:
                # 关闭设备
                # 当equipmentSwitch=="0"
                data = self.device_close(camera_id=camera_id)
                print(data)
                code = data['code']
                message = data['message']
                errorCode = code
                errorDesc = message
                if code == 200:
                    '''关闭设备成功'''
                    cameraProcessResult = 3
                    data = {
                        "cameraProcessResult": cameraProcessResult,
                        "errorCode": errorCode,
                        "errorDesc": errorDesc
                    }
                    return JsonResponse(data=data)
                else:
                    '''关闭设备失败'''
                    cameraProcessResult = 4
                    data = {
                        "cameraProcessResult": cameraProcessResult,
                        "errorCode": errorCode,
                        "errorDesc": errorDesc
                    }
                    return JsonResponse(data=data)
        except Exception as e:
            return result.result(data={"error_message": e})


class Devicestatus_View(Device_status, View):
    '''查询运行状态'''

    # 返回deviceId，cameraState
    def get(self, request):
        camera_id = request.GET.get('camera_id', '')
        data = self.device_status(camera_id=camera_id)
        try:
            deviceId = data['data']['deviceId']
            cameraState = data['data']['automatic']
            data = {
                "cameraId": deviceId,
                "cameraState": cameraState
            }
            return result.result(data=data)
        except Exception as e:
            code = data['code']
            message = data['message']
            data = {
                "errorCode": code,
                "errorDesc": message
            }
            return result.result(data=data)


class PlayBack_View(VideoView, View):
    def post(self, request):
        '''全通要求响应
        data
	    list
		beginTime
		endTime
		playbackUrl
	    total
	    totalTimeUrl
    isWarning'''
        camera_id = json.loads(request.body.decode().replace("'", "\"")).get('camera_id')
        beginTime = json.loads(request.body.decode().replace("'", "\"")).get('beginTime')
        endTime = json.loads(request.body.decode().replace("'", "\"")).get('endTime')
        data = self.video_view(camera_id=camera_id, beginTime=beginTime, endTime=endTime)
        try:
            url = data['data']['address']
            return_data = {
                "list":
                    [
                        {
                            "beginTime": beginTime,
                            "endTime": endTime,
                            "playbackUrl": url
                        }
                    ],
                "total": 1,
                "totalTimeUrl": url,
                "isWarning": 0
            }
            return result.result(data=return_data, message='success')
        except Exception as e:

            code = data['code']
            message = data['message']
            data = {
                "errorCode": code,
                "errorDesc": message
            }
            return result.result(data=data)


class DownLoadView(DownLoad_Video, View):
    def post(self, request):
        camera_id = json.loads(request.body.decode().replace("'", "\"")).get('camera_id')
        beginTime = json.loads(request.body.decode().replace("'", "\"")).get('beginTime')
        endTime = json.loads(request.body.decode().replace("'", "\"")).get('endTime')
        # 加判断,如果传递来的都是0,需要获取当天零点到当前的时间来算,
        # 没有传递0,就按照实际时间戳来计算
        if beginTime == 0 and endTime == 0:
            beginTime = int(time.time()) - int(time.time() - time.timezone) % 86400
            endTime = int(time.time()) - 300
            data = self.down_load(camera_id, beginTime, endTime)
            try:
                code = data['code']
                message = data['message']
                rec_data = data['data']
                url = rec_data['address']
                return_data = {
                    "videoDownloadFormat": ".mp4",
                    "url": url
                }

                return result.result(data=return_data, code=code, message=message)
            except Exception as e:
                code = data['code']
                message = data['message']
                return result.result(data=data, code=code, message=message)
        else:
            data = self.down_load(camera_id, beginTime, endTime)
            # code = data['code']
            # message = data['message']
            rec_data = data['data']
            url = rec_data['address']
            return_data = {
                "videoDownloadFormat": ".mp4",
                "url": url
            }
            return result.result(data=return_data)
