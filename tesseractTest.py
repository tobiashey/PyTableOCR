try:
    from PIL import Image
except ImportError:
    import Image
import cv2
import re
import pandas as pd
import numpy as np
import pytesseract
from pytesseract import Output
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

# image_to_string => String of text
# image_to_boxes => position of chars
# image_to_data => level, page_num, block_num, par_num, line_num, word_num, left, top, width, height, conf, text
# image_to_osd => Some Data about the Image


def show_wait_destroy(winname, img):
    cv2.imshow(winname, img)
    cv2.moveWindow(winname, 500, 0)
    cv2.waitKey(0)
    cv2.destroyWindow(winname)


def hough_transform(img):
    # shape of Image
    try:
        height, width, color = img.shape
    except ValueError:
        height, width = img.shape

    # empty Image
    white_Image = 255 * np.ones(shape=[height, width, 3], dtype=np.uint8)

    # actual hugh translation
    lines = cv2.HoughLines(img, 1, np.pi / 360, 200)

    # Calculate and paint the found lines
    for line in lines:
        for rho, theta in line:
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a * rho
            y0 = b * rho
            x1 = int(x0 + 1000 * (-b))
            y1 = int(y0 + 1000 * (a))
            x2 = int(x0 - 1000 * (-b))
            y2 = int(y0 - 1000 * (a))

            # filter for vertical and horizontal lines
            if x2 - x1 == 0 or abs(y2 - y1) < 2:
                cv2.line(white_Image, (x1, y1), (x2, y2), (0, 0, 0), 2)
                # turn negative values to 0
                # if x1 == -1000:
                #     x1 = 0
                # if y1 == -1000:
                #     y1 = 0
                # if x2 == -1000:
                #     x2 = 0
                # if y2 == -1000:
                #     y2 = 0
                # lineArray = np.append(lineArray, [[(x1, y1), (x2, y2)]], axis=0)

    # minLineLength = 100
    # maxLineGap = 10
    # lines = cv2.HoughLinesP(lineImg,1,np.pi/180,100,minLineLength,maxLineGap)
    # for line in lines:
    #     for x1,y1,x2,y2 in line:
    #         # filter for vertical and horizontal lines
    #         if x2-x1 == 0 or abs(y2-y1) < 2:
    #             cv2.line(img,(x1,y1),(x2,y2),(0,255,0),2)

    # Draw lines at the border for better contour detection later
    cv2.line(white_Image, (0, 0),           (width, 0),     (0, 0, 0), 1)       # top
    cv2.line(white_Image, (width, height),  (0, height),    (0, 0, 0), 1)       # bottom
    cv2.line(white_Image, (0, 0),           (0, height),    (0, 0, 0), 1)       # left
    cv2.line(white_Image, (width, height),  (width, 0),     (0, 0, 0), 1)       # right

    return white_Image


def tesseract_ocr(img):
    res = pytesseract.image_to_string(img)
    # print(res)
    # filter some nasty text stuff out
    res = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', res)
    return res


def main(path):

    """--------Init-------"""
    origImg = cv2.imread(path)
    paintedImg = cv2.imread(path)
    src = cv2.imread(path, cv2.IMREAD_COLOR)

    # check for correct path
    if src is None:
        print('Error opening image: ' + path)
        return -1

    # check if img is already grey
    try:
        height, width, color = origImg.shape
        gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    except ValueError:
        height, width = origImg.shape
        gray = src

    """--------Find Lines-------"""
    # Apply adaptiveThreshold at the bitwise_not of gray
    gray = cv2.bitwise_not(gray)
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)

    # Create the images that will extract the horizontal and vertical lines
    horizontal = np.copy(bw)
    vertical = np.copy(bw)

    # Specify size on horizontal axis
    cols = horizontal.shape[1]
    horizontal_size = cols // 50
    # Create structure element for extracting horizontal lines through morphology operations
    horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
    # Apply morphology operations
    horizontal = cv2.erode(horizontal, horizontalStructure)
    horizontal = cv2.dilate(horizontal, horizontalStructure)

    # Specify size on vertical axis
    rows = vertical.shape[0]
    verticalsize = rows // 50
    # Create structure element for extracting vertical lines through morphology operations
    verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))
    # Apply morphology operations
    vertical = cv2.erode(vertical, verticalStructure)
    vertical = cv2.dilate(vertical, verticalStructure)

    lineImg = cv2.add(horizontal, vertical)
    # show_wait_destroy('Rawlines.jpg', lineImg)

    """--------Hough transform Lines-------"""
    # transform horizontal lines 2 times with fliped image for accuracy
    horizontal1 = hough_transform(horizontal)
    # show_wait_destroy('Refinedlines.jpg', horizontal1)
    # flip and seccond go
    horizontal2 = cv2.rotate(horizontal, cv2.ROTATE_180)
    horizontal2 = hough_transform(horizontal2)
    horizontal2 = cv2.rotate(horizontal2, cv2.ROTATE_180)
    # show_wait_destroy('Refinedlines.jpg', horizontal2)

    # addd bot inverted
    horizontal = 255 - (255-horizontal1 + (255-horizontal2))
    # show_wait_destroy('Refinedlines.jpg', horizontal)

    # transform vertical lines
    vertical = hough_transform(vertical)
    # show_wait_destroy('RefinedlinesFliped.jpg', vertical)

    # add vert and horiz lines as inverses
    lineImg = 255 - (255 - horizontal + (255 - vertical))
    # show_wait_destroy('Refinedlines.jpg', lineImg)

    """--------Find Contours-> Cells-------"""
    ret, thresh = cv2.threshold(cv2.cvtColor(lineImg, cv2.COLOR_BGR2GRAY), 127, 255, 0)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(lineImg, contours, -1, (0, 255, 0), 2)
    # show_wait_destroy('contours.jpg', lineImg)

    """--------Filter Contours-------"""
    # apply approx filter to find rectangles, remove the rest from contours (0.02 genauigkeit)
    filteredContours = []
    for cnt in contours:
        epsilon = 0.001 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        if len(approx) == 4:                            # remove cells with less than 4 edges
            if cv2.contourArea(cnt) > 300.0:              # remove cells with less than 400^2 px
                filteredContours.append(cnt)

    # cv2.drawContours(lineImg, filteredContours, -1, (255, 0, 0), 2)
    # show_wait_destroy('filteredContours.jpg', lineImg)
    cv2.drawContours(paintedImg, filteredContours, -1, (255, 0, 0), 2)

    """--------Find Rows and Collumns-------"""
    rows = []           # indexes every Contour with a row height and a row Index of rowRange
    columns = []        # indexes every Contour with a columns width and a columns Index of columnRange
    rowRange = []       # holds track of every row with a given height +- tolerance
    columnRange = []    # holds track of every columns with a given height +- tolerance

    index = 0
    tolerance = 2       # in px
    for cnt in filteredContours:                # find centroid of Contour for calculating rows and columns
        M = cv2.moments(cnt)
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        cv2.circle(paintedImg, (cx, cy), radius=0, color=(0, 0, 255), thickness=10)

        if len(rowRange) == 0:                                                      # no rows yet
            rowRange.append(cy)                                                     # append new Row
            rows.append([cy, index, 0])                                             # cy creates new row
        else:
            for i in range(len(rowRange)):                                              # search for existing row
                if cy > rowRange[i] + tolerance or cy < rowRange[i] - tolerance:        # tolerance +- 2 pixel
                    if i == len(rowRange)-1:                                            # no fitting row found
                        rowRange.append(cy)                                             # append new Row
                        rows.append([cy, index, i+1])                                   # cy creates new row index +1
                else:
                    rows.append([cy, index, i])                                     # cy is in the tolerance, row found
                    break

        if len(columnRange) == 0:                                                   # no rows yet
            columnRange.append(cx)                                                  # append new Row
            columns.append([cx, index, 0])                                          # cx creates new row
        else:
            for j in range(len(columnRange)):                                           # search for existing col
                if cx > columnRange[j] + tolerance or cx < columnRange[j] - tolerance:  # tolerance +- 2 pixel
                    if j == len(columnRange)-1:                                         # no fitting col found
                        columnRange.append(cx)                                          # append new col
                        columns.append([cx, index, j+1])                                # cx creates new column index +1
                else:
                    columns.append([cx, index, j])                                   # cx is in the tolerance, col found
                    break

        index +=1       # hold track of index of item from filteredContours

    # print(rows)
    # print(columns)
    # print("-----")
    # print(rowRange)
    # print(columnRange)
    show_wait_destroy('Computer Vision.jpg', paintedImg)

    """--------Slice Images-------"""
    # create list of sliced images according to rect coordinates
    # pytesseract over every sliced image
    imageList = []
    for rectangle in filteredContours:
        x1 = rectangle[0][0][0]
        y1 = rectangle[0][0][1]
        x2 = rectangle[1][0][0]
        y2 = rectangle[1][0][1]
        x3 = rectangle[2][0][0]
        y3 = rectangle[2][0][1]
        x4 = rectangle[3][0][0]
        y4 = rectangle[3][0][1]

        # calculate farthest distance between corner from point 1 to create a rectangle (with pythagoras)
        d12 = np.sqrt(((x2-x1)**2)+((y2-y1)**2))    # distance between P1 and P2
        d13 = np.sqrt(((x3-x1)**2)+((y3-y1)**2))    # distance between P1 and P3
        d14 = np.sqrt(((x4-x1)**2)+((y4-y1)**2))    # distance between P1 and P4
        if d12 > d13 and d12 > d14:
            # d between 1 and 2 is greatest
            px = x2
            py = y2
        elif d13 > d12 and d13 > d14:
            # d between 1 and 3 is greatest
            px = x3
            py = y3
        else:  # d14 > d12 and d14 > d13:
            # d between 1 and 4 is greatest
            px = x4
            py = y4

        # print(x1, y1, d12, d13, d14, px, py)
        slicedImage = origImg[y1:py, x1:px].copy()
        ret, slicedImage = cv2.threshold(np.array(slicedImage), 125, 255, cv2.THRESH_BINARY)    # treshholding
        imageList.append(slicedImage)
        # show_wait_destroy('sliced.jpg', slicedImage)

    """--------Create empty Pandas DF-------"""
    row = range(len(rowRange))
    col = range(len(columnRange))

    df = pd.DataFrame(index=row, columns=col)

    """--------OCR every Images-------"""
    for i in range(len(imageList)):
        r = len(rowRange)-1-rows[i][2]      # coordinate of row
        c = len(columnRange)-1-columns[i][2]   # coordinate of col

        df.iat[r, c] = tesseract_ocr(imageList[i])

    print(df)
    df.to_csv(path+'.csv', index=False, header=False)


if __name__ == "__main__":
    # main("images/Excel/ExcelTabelle.png")
    main("images/Bundesliga.png")
