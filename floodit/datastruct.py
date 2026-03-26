import random


class Table:
    """二维表"""

    def __init__(self, numbers: list, size: tuple):
        """
        生成一个宽为 size[0]、高为 size[1]，从 numbers 中随机取样为元素的二维表。

        numbers: 内容为数字的 list
        size: 具有两个数字元素的 list 或 tuple
        """
        self.numbers = list(numbers)
        self.size = size
        self.ary = [
            [random.choice(self.numbers) for _ in range(self.size[0])]
            for _ in range(self.size[1])
        ]

    def __iter__(self):
        return iter(self.ary)

    def __getitem__(self, item):
        return self.ary[item]

    def __len__(self):
        return len(self.ary)
