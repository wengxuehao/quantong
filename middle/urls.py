#  _*_ coding:utf-8 _*_
from django.urls import path
from middle import user_views

app_name = 'middle'

urlpatterns = [
    path('user_auth/', user_views.AuthTokenView.as_view(), name='user_auth'),  # 获取token
    path('rec_tree/', user_views.RecTreeView.as_view(), name='rec_tree'),  # 获取菜单树
    path('live_view/', user_views.DevLiveView.as_view(), name='live_view'),  # 获取直播流
    path('open_device/', user_views.Deviceopen_close_View.as_view(), name='open_device'),  # 开启关闭设备
    # path('close_device/', user_views.DevicecloseView.as_view(), name='close_device'),  # 关闭设备
    path('device_status/', user_views.Devicestatus_View.as_view(), name='device_status'),  # 设备状态
    path('playback/', user_views.PlayBack_View.as_view(), name='playback'),
    path('download/', user_views.DownLoadView.as_view(), name='download')
]
