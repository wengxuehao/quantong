# __author__ : htzs
# __time__   : 19-5-6 下午4:07


from django.http import JsonResponse


class HttpCode(object):
    """
    定义状态码
    """
    ok = 200  # 正常请求
    params_error = 400  # 参数错误
    un_auth = 401  # 没有授权
    method_error = 405  # 请求方法错误
    server_error = 500  # 服务器内部错误


def result(code=HttpCode.ok, message='', data=None, kwargs=None):
    """
    定义函数　返回json数据
    :param code:
    :param message:
    :param count:
    :param data:
    :param kwargs:
    :return:
    """
    json_dict = {'code': code, 'message': message, 'data': data}

    if kwargs and isinstance(kwargs, dict) and kwargs.keys():
        # 判断kwargs是否是字典以及是否有值
        json_dict.update(kwargs)

    return JsonResponse(json_dict)


def ok():
    """
    正常请求
    :return:
    """
    return result()


def params_error(message='', data=None):
    """
    参数错误
    :param message:
    :param data:
    :return:
    """
    return result(code=HttpCode.params_error, message=message, data=data)


def un_auth(message='', data=None):
    """
    没有授权
    :param message:
    :param data:
    :return:
    """
    return result(code=HttpCode.un_auth, message=message, data=data)


def method_error(message='', data=None):
    """
    请求方法错误
    :param message:
    :param data:
    :return:
    """
    return result(code=HttpCode.method_error, message=message, data=data)


def server_error(message='', data=None):
    """
    服务器错误
    :param message:
    :param data:
    :return:
    """
    return result(code=HttpCode.server_error, message=message, data=data)


