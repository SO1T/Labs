import math
import time
import queue
import sys
import argparse

def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='ukraine_poi.csv')
    parser.add_argument('--lat', type=float, default=50.45130913)
    parser.add_argument('--long', type=float, default=30.45735345)
    parser.add_argument('--size', type=float, default=3)
    parser.add_argument('--type')
    parser.add_argument('--subtype', default='supermarket')
    return parser

# cord - center circle, x1, y1 - dot, R - radius
def dotInCircle(cord, x1, y1, R):
    x, y = cord[0], cord[1]
    if ((x - x1) ** 2 + (y - y1) ** 2) <= R ** 2:
        return True
    return False

# check is circle in rect?
def circleInRect(cordCircle, cordRect, h, w, R):
    x, y = cordCircle[0], cordCircle[1]
    x1, y1 = cordRect[0], cordRect[1]

    circleDistanceX = abs(x - x1)
    circleDistanceY = abs(y - y1)

    if circleDistanceX > w + R or circleDistanceY > h + R:
        return False

    if circleDistanceX <= w or circleDistanceY <= h:
        return True

    cornerDistance_sq = (circleDistanceX - w) ** 2 + (circleDistanceY - h) ** 2

    return cornerDistance_sq <= R ** 2

# coordinats in decart system
def findXY(latitude, longitude):
    return 6371 * math.cos(latitude) * math.cos(longitude), 6371 * math.cos(latitude) * math.sin(longitude)

# iterator
def make_counter():
    i = 0

    def counter():  # counter() is a closure
        nonlocal i
        i += 1
        return i

    return counter

# Leaf with latitude, longtude and information
class Leaf:
    def __init__(self, cord, type, subtype, name, adress, subtype):
        self.cord = cord
        xy = findXY(cord[0], cord[1])
        self.x = xy[0]
        self.y = xy[1]
        self.type = type
        self.subtype = subtype
        self.name = name
        self.adress = adress

    def __str__(self):
        return 'Leaf: [latitude: %f, longtude: %f, x: %f, y: %f type: %s, subtype: %s, name: %s, adress: %s]' % \
               (self.cord[0], self.cord[1], self.x, self.y, self.type, self.subtype, self.name, self.adress)

# Rect Node
class Node:
    def __init__(self, cord, h, w, depth, n):
        self.x = cord[0]
        self.y = cord[1]
        self.h = h
        self.w = w
        self.depth = depth
        self.n = n
        self.dots = 0
        self.children = [None, None]
        self.divided = False
        self.leafes = []

# RTree
class RTree():
    def __init__(self, cord=(0, 0), h=10000, w=10000, n=100):
        self.root = Node(cord, h, w, 1, n)
    def add(self, leaf):
        temp = self.root
        # here check for the fact that the node is not the initial root
        if temp.children[0]:
            while temp.divided:
                if temp.depth % 2:
                    if temp.children[0].x + temp.children[0].w > leaf.x:
                        temp = temp.children[0]
                    else:
                        temp = temp.children[1]
                else:
                    if temp.children[0].y - temp.children[0].h < leaf.y:
                        temp = temp.children[0]
                    else:
                        temp = temp.children[1]
        # if there are more than n points in the node in which you want to add, divide it into 2 parts, adding the leaves to these nodes
        if temp.dots == temp.n:
            if temp.depth % 2:
                temp.leafes.sort(key=lambda x: x.x)
                mid = (temp.leafes[temp.n // 2 - 1].x + temp.leafes[temp.n // 2].x) / 2
                x0 = (mid + temp.x - temp.w) / 2
                x1 = (mid + temp.x + temp.w) / 2
                temp.children[0] = Node((x0, temp.y), temp.h, x0 - (temp.x - temp.w), temp.depth + 1, temp.n)
                temp.children[1] = Node((x1, temp.y), temp.h, (temp.x + temp.w) - x1, temp.depth + 1, temp.n)
                temp.children[0].leafes = temp.leafes[:temp.n // 2]
                temp.children[1].leafes = temp.leafes[temp.n // 2:]
                temp.children[0].dots += temp.n // 2
                temp.children[1].dots += temp.n // 2
                if mid > leaf.x:
                    temp.children[0].leafes.append(leaf)
                    temp.children[0].dots += 1
                else:
                    temp.children[1].leafes.append(leaf)
                    temp.children[1].dots += 1
            else:
                temp.leafes.sort(key=lambda y: y.y)
                mid = (temp.leafes[temp.n // 2 - 1].y + temp.leafes[temp.n // 2].y) / 2
                y0 = (mid + temp.y + temp.h) / 2
                y1 = (mid + temp.y - temp.h) / 2
                temp.children[0] = Node((temp.x, y0), (temp.y + temp.h) - y0, temp.w, temp.depth + 1, temp.n)
                temp.children[1] = Node((temp.x, y1), y1 - (temp.y - temp.h), temp.w, temp.depth + 1, temp.n)
                temp.children[0].leafes = temp.leafes[temp.n // 2:]
                temp.children[1].leafes = temp.leafes[:temp.n // 2]
                temp.children[0].dots += temp.n // 2
                temp.children[1].dots += temp.n // 2
                if mid < leaf.y:
                    temp.children[0].leafes.append(leaf)
                    temp.children[0].dots += 1
                else:
                    temp.children[1].leafes.append(leaf)
                    temp.children[1].dots += 1
            temp.divided = True
            temp.leafes = []
        else:
            temp.leafes.append(leaf)
            temp.dots += 1
    def findCord(self ,cord, R, type=None, subtype=None):
        out = []
        q = queue.Queue()
        q.put(self.root)
        while not q.empty():
            temp = q.get()
            if temp.divided:
                if circleInRect(cord, (temp.children[0].x, temp.children[0].y), temp.children[0].h, temp.children[0].w, R):
                    q.put(temp.children[0])
                if circleInRect(cord, (temp.children[1].x, temp.children[1].y), temp.children[1].h, temp.children[1].w, R):
                    q.put(temp.children[1])
            else:
                if type:
                    out += [el for el in temp.leafes if dotInCircle(cord, el.x, el.y, R) and (el.type == type or el.subtype == subtype)] #and
                else:
                    out += [el for el in temp.leafes if dotInCircle(cord, el.x, el.y, R)]

        return out

if __name__ == '__main__':

    start_time = time.time()
    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])

    tree = RTree()
    f = open(namespace.db)
    i = make_counter()
    for line in f:
        info = line.split(';')
        info[0] = info[0].replace(',', '.')
        info[1] = info[1].replace(',', '.')
        i()
        try:
            leaf = Leaf((float(info[0]), float(info[1])), info[2], info[3], info[4], info[5])
            tree.add(leaf)
        except ValueError:
            print("Value error on line:", i())

    out = tree.findCord(findXY(namespace.lat, namespace.long), namespace.size * 5, namespace.type, namespace.subtype)
    
    print("\nCoordinats in decart system:",findXY(namespace.lat, namespace.long))
    print("We found %s next entities in the sector:" % (len(out)))
    for el in out:
        print(el)
    print("\n\nTime: %s seconds" % (round(time.time() - start_time, 2)))

    f.close()