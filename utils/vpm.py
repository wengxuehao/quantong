import requests

from quantong import settings
from utils import result
from django.core.cache import cache


class BaseData:
    def __init__(self, *args, **kwargs):
        self.token_url = settings.TOKEN_URL
        self.dev_tree_url = settings.DEV_TREE
        self.json_headers = settings.JSON_RESULT
        self.live_url = settings.LIVE_URL
        self.video_url = settings.VIDEO_URL
        self.open_url = settings.OPEN_URL
        self.close_url = settings.CLOSE_URL
        self.device_status_url = settings.DEVICE_STATUS_URL
        self.playback_url = settings.PlayBack_URL
        self.download_url = settings.DownLoad_URL

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
        # rec_data = {'code': 0}
        try:
            rec_data = requests.get(url=self.token_url, params=data, headers=self.auth_token)
            token = rec_data.headers['Token']
            return token
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')
        except Exception as e:
            return data


class RecTree(BaseData):
    """
    获取设备树
    """

    def __init__(self, *args, **kwargs):
        super().__init__()

    def rec_tree(self):

        params = {
            "type": 0
        }
        rec_data = requests.get(url=self.dev_tree_url, headers=self.auth_token, params=params)

        try:
            rec_data = rec_data.json()
            return rec_data
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')
        except Exception as e:
            return rec_data


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
        data = {
            'channelId': camera_id,
            'protocol': "RTMP",
            "streamType": "0"
        }
        try:
            rec_data = requests.get(url=self.live_url, params=data, headers=self.auth_token)
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')
        except Exception:
            return result.server_error(message='请求失败,请重试.')
        else:
            receve_data = rec_data.json()

            return receve_data


#
class VideoView(BaseData):
    '''获取视频录像的url'''

    def __init__(self, *args, **kwargs):
        super().__init__()

    def video_view(self, camera_id, beginTime, endTime):
        '''
    channelId
    playTime
    protocol
    streamType'''
        params = {
            "channelId": camera_id,
            'protocol': "RTMP",
            "streamType": "0",
            'playTime': endTime - beginTime
        }
        try:
            rec_data = requests.get(url=self.playback_url, params=params, headers=self.auth_token)
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')

        else:
            rec_data = rec_data.json()
            return rec_data


class Device_open_close(BaseData):
    '''设备开启'''

    def __init__(self):
        super().__init__()

    def device_open(self, camera_id):

        data = {
            "channelId": camera_id,
            "type": 1
        }
        try:
            rec_data = requests.get(url=self.open_url, params=data, headers=self.auth_token)

            data = rec_data.json()
            return data
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')

    def device_close(self, camera_id):
        data = {
            "channelId": camera_id,
            "type": 1
        }

        try:
            rec_data = requests.get(url=self.close_url, params=data, headers=self.auth_token)
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')
        except Exception:
            return result.server_error(message='请求失败,请重试.')
        else:
            data = rec_data.json()
            return data


class Device_status(BaseData):
    def device_status(self, camera_id):
        deviceId = camera_id
        data = {
            "deviceId": deviceId
        }
        try:
            rec_data = requests.get(url=self.device_status_url, params=data, headers=self.auth_token)
            data = rec_data.json()
            return data
        except requests.exceptions.ConnectTimeout:
            return result.server_error(message='链接超时,请重试.')
        except Exception:
            return result.server_error(message='请求失败,请重试.')


class DownLoad_Video(BaseData):
    def down_load(self, camera_id, beginTime, endTime):
        ''' channelId
            startTime
            endTime'''
        params = {
            "channelId": camera_id,
            "startTime": beginTime,
            "endTime": endTime
        }
        try:
            rec_data = requests.get(url=self.download_url, params=params, headers=self.auth_token)
            data = rec_data.json()
            return data
        except Exception as e:
            data = {
                "message": e
            }

            return data
