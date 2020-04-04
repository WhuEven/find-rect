
from .utils.min_max import min_max

class Point_Iter:
    def __init__(self, point, idx):
        self.point = point
        self.idx = idx
    
    def __iter__(self):
        return Point_Iter(self.point, self.idx + 1)
    
    def __next__(self):
        if self.idx > 1:
            raise StopIteration
        
        self.idx += 1
        if self.idx == 1:
            return self.point.x
        elif self.idx == 2:
            return self.point.y

class Line_Iter:
    def __init__(self, line, idx):
        self.line = line
        self.idx = idx
    
    def __iter__(self):
        return Line_Iter(self.lien, self.idx + 1)
    
    def __next__(self):
        if self.idx > 1:
            raise StopIteration

        self.idx += 1
        if self.idx == 1:
            return self.line.start
        elif self.idx == 2:
            return self.line.end

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __iter__(self):
        return Point_Iter(self, 0)
    
    def to_tuple(self):
        return self.x, self.y

class Line:
    def __init__(self, start, end):
        self.start = start
        self.end = end
    
    def __iter__(self):
        return Line_Iter(self, 0)
    
    @staticmethod
    def create_line(start_x, start_y, end_x, end_y):#静态方法，用Line.create_line()调用
        start = Point(start_x, start_y)
        end = Point(end_x, end_y)
        return Line(start, end)
    
    def intersection(self, other, approx=5):
        horizontal = self if self.is_horizontal() else other
        vertical = self if self.is_vertical() else other

        if not horizontal.is_horizontal() or not vertical.is_vertical():
            return None
        
        left, right = min_max(horizontal.start.x, horizontal.end.x)
        top, bottom = min_max(vertical.start.y, vertical.end.y)

        intersection = Point(vertical.start.x, horizontal.start.y)

        if intersection.x >= left - approx and intersection.x <= right + approx and intersection.y >= top - approx and intersection.y <= bottom + approx:
            return intersection
        else:
            return None

    def is_horizontal(self):
        return self.start.y == self.end.y
    
    def is_vertical(self):
        return self.start.x == self.end.x
