# from django.conf import settings
import hashlib
import requests
from django.http import JsonResponse

# from sun_pvm import settings
from quantong import settings
from utils import result
from django.core.cache import cache


class BaseData:
    def __init__(self, *args, **kwargs):
        self.token_url = settings.TOKEN_URL
        self.dev_tree_url = settings.DEV_TREE
        self.json_headers = settings.JSON_RESULT
        self.live_url = settings.LIVE_URL
        self.playback_url = settings.PlayBack_URL
        self.open_url = settings.TURN_ON_URL
        self.close_url = settings.TURN_OFF_URL
        self.device_status_url = settings.DEVICE_STATUS_URL
        self.download_url = settings.DOWNLOAD_URL
        self.get_file_url = settings.File_Url

    @property
    def auth_token(self):
        try:
            token = cache.get('token')
        except:
            return result.params_error(message='token过期,请重新获取.')
        else:
            self.json_headers.update({'Token': token})
            return self.json_headers

    # @staticmethod
    # def password_hash(pwd):
    #     """
    #     密码md5
    #     :param pwd:
    #     :return:
    #     """
    #     md5 = hashlib.md5()
    #     md5.update(pwd.encode())
    #     result = md5.hexdigest()
    #     return result


class UserAuth(BaseData):
    """
    获取token 验证用户
    """

    def __init__(self, *args, **kwargs):
        super().__init__()

    def token_auth(self, username, password):
        data = {
            'username': username, 'password': password
        }
        try:
            rec_data = requests.get(url=self.token_url, params=data, headers=self.auth_token)
            token = rec_data.headers['Token']
            return token
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')
        except:
            return data


class RecTree(BaseData):
    """
    获取设备树
    """

    def __init__(self, *args, **kwargs):
        super().__init__()

    def rec_tree(self):
        try:

            rec_data = requests.get(url=self.dev_tree_url, headers=self.auth_token)
            data = rec_data.json()
            return data
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')
        # except Exception as e:
        #     print(self.json_headers['Token'])
        #     return '11111'
        # else:
        #     dev_tree = rec_data.json()
        #     return dev_tree


class LiveView(BaseData):
    """
    获取直播地址
    """

    def __init__(self, *args, **kwargs):
        super().__init__()

    def live_view(self, camera_id):
        """
        获取直播地址
        :return:
        """
        params = {
            'channelId': '{'+camera_id+'}',
            'protocol': "rtmp",
            "streamType": "0"
        }
        try:
            # print(params)
            rec_data = requests.get(url=self.live_url, params=params, headers=self.auth_token)
            return_data = rec_data.json()
            return return_data
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')
        except:
            return result.server_error(message='请求失败,请重试.')


#
# class VideoView(BaseData):
#     '''获取视频录像的url'''
#
#     def __init__(self, *args, **kwargs):
#         super().__init__()
#
#     def video_view(self,):

class DeviceOpen(BaseData):
    def __init__(self):
        super().__init__()

    def device_open(self, camera_id):
        print(camera_id)
        data = {
            "channelId": '{'+camera_id+'}',
            "type": 0
        }
        data = str(data).replace("'", "\"")
        try:
            rec_data = requests.put(url=self.open_url + "/" + '{'+camera_id+'}', data=data, headers=self.auth_token)

            rec_data = rec_data.json()
            return rec_data
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')
        except:
            return result.server_error(message='请求失败,请重试.')


class DeviceClose(BaseData):
    def device_close(self, camera_id):
        data = {
            "channelId": '{'+camera_id+'}',
            "type": 1
        }
        data = str(data).replace("'", "\"")
        try:
            rec_data = requests.put(url=self.close_url + "/" + '{'+camera_id+'}', data=data, headers=self.auth_token)

            rec_data = rec_data.json()
            return rec_data
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')
        except:
            return result.server_error(message='请求失败,请重试.')


class DeviceStatus(BaseData):
    def device_status(self, camera_id):
        data = {
            "channelId": '{'+camera_id+'}'
        }
        try:
            rec_data = requests.get(url=self.device_status_url, params=data, headers=self.auth_token)

            data = rec_data.json()
            return data
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')
        except:
            return result.server_error(message='请求失败,请重试.')


class VideoView(BaseData):
    # 获取录像回放地址
    def __init__(self, *args, **kwargs):
        super().__init__()

    def video_view(self, camera_id, begin_time, end_time):
        params = {
            "channelId": '{'+camera_id+'}',
            "startTime": begin_time,
            "endTime": end_time
        }
        try:
            rec_data = requests.get(url=self.playback_url, params=params, headers=self.auth_token)

            rec_data = rec_data.json()
            return rec_data
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')
        except:
            return result.server_error(message='请求失败,请重试.')

    def get_file(self, camera_id):
        params = {
            'channelId': '{'+camera_id+'}'
        }
        try:
            rec_data = requests.get(url=self.get_file_url, params=params, headers=self.auth_token)
            rec_data = rec_data.json()
            return rec_data
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')


class DownLoadVideo(BaseData):
    def down_load(self, camera_id, begin_time, end_time):
        # print(camera_id)
        params = {
            "channelId": '{'+camera_id+'}',
            "startTime": begin_time,
            "endTime": end_time
        }
        try:
            rec_data = requests.get(url=self.download_url, params=params, headers=self.auth_token)

            rec_data = rec_data.json()
            return rec_data
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')
        except:
            return result.server_error(message='请求失败,请重试.')

    def get_file(self, camera_id):
        params = {
            'channelId': '{'+camera_id+'}'
        }
        try:
            rec_data = requests.get(url=self.get_file_url, params=params, headers=self.auth_token)
            rec_data = rec_data.json()
            return rec_data
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')


#
# class Video_File(BaseData):
#     def get_file(self, camera_id):
#         params = {
#             'channelId': camera_id
#         }
#         try:
#             rec_data = requests.get(url=self.get_file_url, params=params, headers=self.auth_token)
#             rec_data = rec_data.json()
#             return rec_data
#         except requests.exceptions.ConnectTimeout:
#             return result.server_error(message='链接超时,请重试.')
