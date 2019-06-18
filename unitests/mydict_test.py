#  _*_ coding:utf-8 _*_
import unittest

# from my_unittest import sum
import logging

logger = logging.getLogger('django')

# class TestSum(unittest.TestCase):
#     def test_list_int(self):
#         '''
#         构建输入数据
#         执行要测试模块，获取执行结果
#         与预期结果相比较，根据结果修改代码
#         测试一个整数列表的和
#         '''
#
#         data = [1, 2,3]
#         result = sum(data)
#         self.assertEqual(result, 6)
#
#     # def test_list_sum(self):
#     #     data = [1, 3, 4]
#     #
#     #     result = sum(data)
#     #     self.assertEqual(result, 6)
#
#
# if __name__ == '__main__':
#     unittest.main()


import unittest

from my_unittest import Dict

'''字典取值正误'''


class TestDict(unittest.TestCase):
    # 继承unittest.TestCase
    '''
    注释:以test开头的方法就是测试方法，
    不以test开头的方法不被认为是测试方法，测试的时候不会被执行。
    对每一类测试都需要编写一个test_xxx()方法。
    由于unittest.TestCase提供了很多内置的条件判断，
    我们只需要调用这些方法就可以断言输出是否是我们所期望的
'''

    def setUp(self):
        print('setUp...%s' % i)

    def tearDown(self):
        print('tearDown...')

    def test_init(self):
        d = Dict(a=1, b='test')
        self.assertEquals(d.a, 1)
        self.assertEquals(d.b, 'test')
        self.assertTrue(isinstance(d, dict))

    def test_key(self):
        d = Dict()
        d['key'] = 'value'
        self.assertEquals(d.key, 'value')

    def test_attr(self):
        d = Dict()
        d.key = 'value'
        self.assertTrue('key' in d)
        self.assertEquals(d['key'], 'value')

    def test_keyerror(self):
        d = Dict()
        with self.assertRaises(KeyError):
            value = d['empty']

    def test_attrerror(self):
        d = Dict()
        with self.assertRaises(AttributeError):
            value = d.empty


if __name__ == '__main__':
    unittest.main()
