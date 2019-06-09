#  _*_ coding:utf-8 _*_
from django.urls import path
from . import user_views

app_name = 'middle'

urlpatterns = [
    path('user_auth/', user_views.AuthTokenView.as_view(), name='user_auth'),  # 获取token
    path('rec_tree/', user_views.RecTreeView.as_view(), name='rec_tree'),  # 获取菜单树
    path('live_view/', user_views.DevLiveView.as_view(), name='live_view'),  # 获取直播流
    path('turn_on_off_device/', user_views.DeviceTurnOnOffView.as_view(), name='on_off_device'),  # 开启关闭设备
    path('device_status/', user_views.DeviceStatusView.as_view(), name='device_status'),  # 查询设备状态
    path('playback/', user_views.PlayBackView.as_view(), name='playback'),  # 获取录像地址
    path('download/', user_views.DownLoadView.as_view(), name='download')  # 录像下载
]
