# -*- coding:utf-8 -*-
import random


class Table(object):
    """二维表"""

    def __init__(self, numbers, size):
        """
            生成一个宽为size[0]高为size[1],从numbers中随机取样为元素的二维表
            numbers: 内容为数字的list
            size: 具有两个数字元素的list或者tuple
        """
        self.numbers = numbers
        self.size = size
        self.ary = []
        for i in xrange(self.size[1]):
            at = []
            for j in xrange(self.size[0]):
                at.append(random.choice(self.numbers))
            self.ary.append(at)

    def __iter__(self):
        return iter(self.ary)

    def __getitem__(self, item):
        return self.ary[item]

    def __len__(self):
        return len(self.ary)
