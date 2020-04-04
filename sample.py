import cv2 as cv

from src.find_rect_units import Point, get_rect_units

def _draw_rect_unit(img, rect_unit, text):
    topleft, topright, bottomleft, bottomright = rect_unit

    cv.rectangle(img, topleft.to_tuple(), bottomright.to_tuple(), (255, 0, 0), 3)
    cv.putText(img, text, bottomleft.to_tuple(), cv.FONT_HERSHEY_PLAIN, 4, (255, 0, 0), 2)

    return img

if __name__ == '__main__':
    src_path = r".\imgs\pic.jpg"

    rect_units = get_rect_units(src_path)

    img = cv.imread(src_path)
    for i in range(len(rect_units)):
        text = str(i)
        _draw_rect_unit(img, rect_units[i], text)
    
    cv.namedWindow("handled_img", cv.WINDOW_NORMAL | cv.WINDOW_KEEPRATIO)
    cv.imshow("handled_img", img)
    cv.waitKey(0)
