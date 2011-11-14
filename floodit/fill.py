#!/bin/env python2.7
# -*- coding:utf-8 -*-

def fill(ary, number, x=0, y=0, src=None):
    """

    """
    if x<0 or y<0 or x>=len(ary[0]) or y>=len(ary):
        return
    if src is None:
        src = ary[0][0]
        if src == number:return
    if ary[x][y] == src:
        ary[x][y] = number
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
        print ""
        for line in ary:
            print "".join(line)
            
    import random, pprint, os
    os.system("clear")
    ary = []
    symbols = ["@","#","%","$","0","+"]
    for i in range(6):
        at = []
        for j in range(6):
            at.append(random.choice(symbols))
        ary.append(at)
    pary(ary)
    while not filldone(ary):
        number = raw_input("Select symbol:")
        while number not in symbols:
            number = raw_input("Select symbol:")
        fill(ary,number)
        os.system("clear")
        pary(ary)
    print "You are win!"
    
