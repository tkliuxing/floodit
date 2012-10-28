#!/usr/bin/env python
# -*- coding:utf-8 -*-

def fill(ary, number, x=0, y=0, src=None):
    """
    将二维数组(ary)中相邻且相同的数字(src)替换为指定的数字(number),从坐标(x,y)开始填充。
    """
    if x<0 or y<0 or x>=len(ary[0]) or y>=len(ary):
        return
    if src is None:
        src = ary[y][x]
        if src == number:
            return
    if ary[y][x] == src:
        ary[y][x] = number
        # 如果该位置的数字和原始数字相同则替换为目标数字。
        fill(ary, number, x+1, y, src)
        fill(ary, number, x-1, y, src)
        fill(ary, number, x, y+1, src)
        fill(ary, number, x, y-1, src)
    else:
        return

def filldone(ary):
    """
    
    """
    src = ary[0][0]
    flag = True
    for i in ary:
        for j in i:
            if j != src:
                flag = False
    return flag

if __name__== '__main__':
    # A command line floodit game
    def pary(ary):
        #print ""
        for line in ary:
            print "".join(line)
            
    import random, pprint, os
    os.system("clear")
    ary = []
    symbols = ["1","2","3","4","5","6"]
    for i in range(7):
        at = []
        for j in range(7):
            at.append(random.choice(symbols))
        ary.append(at)
    pary(ary)
    while not filldone(ary):
        number = raw_input("Select symbol:")
        while number not in symbols:
            number = raw_input("Select symbol:")
        fill(ary,number,x=3,y=3)
        os.system("clear")
        pary(ary)
    print "You are win!"
