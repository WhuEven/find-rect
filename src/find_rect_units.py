import cv2 as cv
import os
import numpy as np
import math

from .utils.min_max import min_max #返回（小的，大的）
from .line import Point, Line

def _find_lines(src_path):
    src = cv.imread(src_path)

    gray = cv.cvtColor(src, cv. COLOR_BGR2GRAY)  # gray
    ret, binary = cv.threshold(gray, 0, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)  # threshold
    dst = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 101, 20)
    kernel1 = cv.getStructuringElement(cv.MORPH_RECT, (1, 30))
    dilated1 = cv.dilate(dst, kernel1)
    eroded1 = cv.erode(dilated1, kernel1)
    thresh = cv.adaptiveThreshold(eroded1, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 11, 5)
    lines = cv.HoughLinesP(thresh, 1, np.pi / 180, 10, minLineLength=200, maxLineGap=5)

    kernel2 = cv.getStructuringElement(cv.MORPH_RECT, (30, 1))
    dilated2 = cv.dilate(dst, kernel2)
    eroded2 = cv.erode(dilated2, kernel2)
    thresh1 = cv.adaptiveThreshold(eroded2, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 11, 5)
    lines2 = cv.HoughLinesP(thresh1, 1, np.pi / 180, 10, minLineLength=200, maxLineGap=5)

    #sort lines
    sorted_lines = sorted(lines, key=lambda x: x[0][0]) 
    sorted_lines2 = sorted(lines2, key=lambda x: x[0][1])

    #Remove excess lines
    col=[]
    col_temp = sorted_lines[0]
    sorted_lines.append(sorted_lines[0]) #temp bug
    for line in sorted_lines:
        if abs(line[0][0]-col_temp[0][0])<5:
            col_temp[0][1] = max(col_temp[0][1],line[0][1])
            col_temp[0][3] = min(col_temp[0][3],line[0][3])
        else:
            col.append(col_temp)
            col_temp = line


    row=[]
    row_temp = sorted_lines2[0]
    sorted_lines2.append(sorted_lines2[0]) #temp bug
    for line in sorted_lines2:
        if abs(line[0][1]-row_temp[0][1])<5:
            row_temp[0][0] = min(row_temp[0][0],line[0][0])
            row_temp[0][2] = max(row_temp[0][2],line[0][2])
        else:
            row.append(row_temp)
            row_temp = line
    
    normal_col = [Line.create_line(c[0][0], c[0][1], c[0][2], c[0][3]) for c in col]
    normal_row = [Line.create_line(r[0][0], r[0][1], r[0][2], r[0][3]) for r in row]
    
    return normal_col, normal_row

def _get_intersections(cols, rows, approx=5):
    '''
      找到行和列的交点并返回交点构成的二维列表（行优先）
      approx 是寻找交点的参数，当两条线没有相交但可以在一定范围内相交时也返回交点
      该范围由 approx 确定大小
      '''
    intersections = []
    for row in rows:
        row_intersections = []
        for col in cols:
            intersection = col.intersection(row, approx)
            if intersection is not None:
                row_intersections.append(intersection)
        intersections.append(row_intersections)
    
    return intersections

def _normalize_line(line):
    '''
      确定线两个端点的顺序，按照从上到下、从左到右的顺序重排两个端点
      '''
    if line.is_horizontal():
        left, right = min_max(line.start.x, line.end.x)
        y = line.start.y
        return Line(Point(left, y), Point(right, y))
    elif line.is_vertical():
        top, bottom = min_max(line.start.y, line.end.y)
        x = line.start.x
        return Line(Point(x, top), Point(x, bottom))
    else:
        print("Unknown line.")

def _find_rect_unit_with_left(intersections, topleft_row_no, topleft_col_no, bottomleft_row_no, bottomleft_col_no):
    '''
      根据矩形单元的左边两个点的坐标在所有交点中寻找矩形单元
      '''
    top_row = intersections[topleft_row_no]
    bottom_row = intersections[bottomleft_row_no]

    topleft = top_row[topleft_col_no]
    bottomleft = bottom_row[bottomleft_col_no]

    alter_topright_col_no = topleft_col_no + 1
    alter_bottomright_col_no = bottomleft_col_no + 1

    while alter_topright_col_no < len(top_row) and alter_bottomright_col_no < len(bottom_row):
        alter_topright = top_row[alter_topright_col_no]
        alter_bottomright = bottom_row[alter_bottomright_col_no]

        if alter_topright.x < alter_bottomright.x:
            alter_topright_col_no += 1
            continue
        elif alter_topright.x > alter_bottomright.x:
            alter_bottomright_col_no += 1
            continue
        else:
            return (topleft, alter_topright, bottomleft, alter_bottomright)
    
    return None

def _find_rect_unit_with_top_left(intersections, row_no, col_no):
    '''
      根据矩形单元的左上角点在所有交点中寻找矩形单元
      '''
    top_left = intersections[row_no][col_no]

    alter_bottom_row_no = row_no + 1
    while alter_bottom_row_no < len(intersections):
        alter_bottom_row = intersections[alter_bottom_row_no]
        for alter_bottom_left_col_no in range(len(alter_bottom_row)):
            alter_bottom_left = alter_bottom_row[alter_bottom_left_col_no]
            if alter_bottom_left.x < top_left.x:
                continue
            elif alter_bottom_left.x == top_left.x:
                return _find_rect_unit_with_left(intersections, row_no, col_no, alter_bottom_row_no, alter_bottom_left_col_no)
            else:
                break
        alter_bottom_row_no += 1
    
    return None

def _find_rect_units_in_normalized_points(intersections):
    '''
      在所有交点中寻找所有的矩形单元，对输入参数的要求是
      从上到下从左到右按照行优先的二维列表顺序排列端点
      '''
    rect_units = []

    max_row_no = len(intersections) - 1
    for row_no in range(max_row_no):
        max_col_no = len(intersections[row_no]) - 1
        for col_no in range(max_col_no):
            rect_unit = _find_rect_unit_with_top_left(intersections, row_no, col_no)

            if rect_unit is None:
                continue
            else:
                rect_units.append(rect_unit)
    
    return rect_units

def get_rect_units(src_path, approx=30):
    '''
      输入图片路径，即可找到所有的矩形单元
      approx 参数用来寻找模糊交点
      '''
    cols, rows = _find_lines(src_path)

    cols = [_normalize_line(col) for col in cols]
    rows = [_normalize_line(row) for row in rows]

    cols.sort(key=lambda line: line.start.x)
    rows.sort(key=lambda line: line.start.y)

    intersections = _get_intersections(cols, rows, approx)

    return _find_rect_units_in_normalized_points(intersections)
