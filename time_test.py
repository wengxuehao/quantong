#  _*_ coding:utf-8 _*_
import datetime
# 获取当前时间
import time

now = datetime.datetime.now()
# 获取今天零点
zeroToday = now - datetime.timedelta(hours=now.hour, minutes=now.minute, seconds=now.second,
                                     microseconds=now.microsecond)
# 获取23:59:59
lastToday = zeroToday + datetime.timedelta(hours=23, minutes=59, seconds=59)
# 获取前一天的当前时间
yesterdayNow = now - datetime.timedelta(hours=23, minutes=59, seconds=59)
# 获取明天的当前时间
tomorrowNow = now + datetime.timedelta(hours=23, minutes=59, seconds=59)
to_day = zeroToday
beginTime = int(time.time()) - int(time.time() - time.timezone) % 86400
time_test = beginTime + 86400
print('时间差', datetime.timedelta(hours=23, minutes=59, seconds=59))
print('当前时间', now)
print(int(time.time()))
print('今天零点', zeroToday)
print('获取23:59:59', lastToday)
print('昨天当前时间', yesterdayNow)
print('明天当前时间', tomorrowNow)
print("今天零点时间戳", beginTime)
# 输出：
# 时间差 23:59:59
# 当前时间 2018-06-11 21:04:20.858475
# 今天零点 2018-06-11 00:00:00
# 获取23:59:59 2018-06-11 23:59:59
# 昨天当前时间 2018-06-10 21:04:21.858475
# 明天当前时间 2018-06-12 21:04:19.858475
zero_today = int(time.time()) - int(time.time() - time.timezone) % 86400
# 時間戳轉化
timeStamp = beginTime+86400
timeArray = time.localtime(timeStamp)
otherStyleTime = time.strftime("%Y--%m--%d %H:%M:%S", timeArray)
print(otherStyleTime)
