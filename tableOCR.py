import cv2
import multiprocessing as mp
import numpy as np
import pandas as pd
import pytesseract
import re
import time
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'


def show_wait_destroy(winname, img):
    cv2.imshow(winname, img)
    cv2.moveWindow(winname, 500, 0)
    cv2.waitKey(0)
    cv2.destroyWindow(winname)


def hough_transform(img):
    """
        -Hough Transformation-

        Hough Transformation Lines
        https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_houghlines/py_houghlines.html

        Probabilistic is not used because of worse results
    """
    # shape of Image
    try:
        height, width, color = img.shape
    except ValueError:
        height, width = img.shape

    # empty Image
    whiteImage = 255 * np.ones(shape=[height, width, 3], dtype=np.uint8)

    # actual hugh translation
    lines = cv2.HoughLines(img, 1, np.pi / 180, 100)

    # Calculate and paint the found lines
    for line in lines:
        for rho, theta in line:
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a * rho
            y0 = b * rho
            x1 = int(x0 + 1000 * (-b))
            y1 = int(y0 + 1000 * a)
            x2 = int(x0 - 1000 * (-b))
            y2 = int(y0 - 1000 * a)

            # filter for vertical and horizontal lines
            if x2 - x1 == 0 or abs(y2 - y1) < 2:
                cv2.line(whiteImage, (x1, y1), (x2, y2), (0, 0, 0), 2)

    # Draw lines at the border for better contour detection later
    cv2.line(whiteImage, (0, 0),           (width, 0),     (0, 0, 0), 1)       # top
    cv2.line(whiteImage, (width, height),  (0, height),    (0, 0, 0), 1)       # bottom
    cv2.line(whiteImage, (0, 0),           (0, height),    (0, 0, 0), 1)       # left
    cv2.line(whiteImage, (width, height),  (width, 0),     (0, 0, 0), 1)       # right

    return whiteImage


def tesseract_ocr(img):
    res = pytesseract.image_to_string(img, config="--psm 6")
    # print(res)
    # filter some nasty text stuff out
    res = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', res)

    res = res.rstrip()
    res = res.lstrip()
    res = res.replace('\t', '')

    return res


def tesseract_ocr_mp(idx, img):
    """
        -PyTesseract OCR for Multiprocessing-

        image_to_string => String of text
        image_to_boxes => position of chars
        image_to_data => level, page_num, block_num, par_num, line_num, word_num, left, top, width, height, conf, text
        image_to_osd => Some Data about the Image

        Use the PyTesseract OCR Engine to get a String of Chars contained in a given Image
        Remove unwanted String chars
    """
    # res = pytesseract.image_to_string(img, config="--psm 6 -c tessedit_char_whitelist=0123456789,.-$%€")
    res = pytesseract.image_to_string(img, config="--psm 6")
    # filter some nasty text stuff out
    res = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', res)

    # remove tabstops and newLine at beginning/end of res,
    res = res.rstrip()
    res = res.lstrip()
    res = res.replace('\t', '')

    return [idx, res]


def table_to_ocr(input_path, img=None, debug=False):

    """
        -Init-

        Initialize some images that will be needed for processing
        And Check some Variables

        origImg -> will be the Original Image as Reference
        paintedImg -> will be a visual representation of the process (used for Debugging)
        src -> will be the source Processed Image on which all processes will be based on

    """
    if img is None:
        origImg = cv2.imread(input_path)
        paintedImg = cv2.imread(input_path)
        src = cv2.imread(input_path, cv2.IMREAD_COLOR)

        # check for correct path
        if src is None:
            print('Error opening image: ' + input_path)
            return -1
    else:
        origImg = np.array(img)
        paintedImg = np.array(img)
        src = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # check if img is already grey
    try:
        gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    except ValueError:
        gray = src

    """
        -Isolate Lines from Image-

        Find Horizontal and Vertical structures in the Image
        The Strictures will be Isolated from the text to identify Rows and Columns
         
    """

    # Apply adaptiveThreshold at the bitwise_not of gray
    gray = cv2.bitwise_not(gray)
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)

    # Create the images that will extract the horizontal and vertical lines
    horizontal = np.copy(bw)
    vertical = np.copy(bw)

    # Specify size on horizontal axis
    cols = horizontal.shape[1]
    horizontalSize = cols // 50
    # Create structure element for extracting horizontal lines through morphology operations
    horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontalSize, 1))
    # Apply morphology operations
    horizontal = cv2.erode(horizontal, horizontalStructure)
    horizontal = cv2.dilate(horizontal, horizontalStructure)

    # Specify size on vertical axis
    rows = vertical.shape[0]
    verticalSize = rows // 30
    # Create structure element for extracting vertical lines through morphology operations
    verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalSize))
    # Apply morphology operations
    vertical = cv2.erode(vertical, verticalStructure)
    vertical = cv2.dilate(vertical, verticalStructure)

    # if debug:
    #
    #     show_wait_destroy('vertical.jpg', vertical)
    #     show_wait_destroy('horizontal.jpg', horizontal)

    # show_wait_destroy('Raw isolated lines.jpg', lineImg)

    rows, cols = horizontal.shape

    # go trough every line and determine if white is below 25% -> kick line out
    horizontal_mean = (horizontal.sum(axis=1)/255/rows)    # sums every Row and calcs mean
    for i in range(len(horizontal_mean)):
        if horizontal_mean[i] <= 0.25:
            horizontal[i] = 0

    vertical = np.swapaxes(vertical, 0, 1)
    rows, cols = vertical.shape
    vertical_mean = (vertical.sum(axis=1)/255/cols)    # sums every Col and calcs mean
    for i in range(len(vertical_mean)):
        if vertical_mean[i] <= 0.25:
            vertical[i] = 0
    vertical = np.swapaxes(vertical, 0, 1)


    """
        -Enhance Lines-

        Enhance the found lines to draw a Table like Structure
        Hough Transformation is used
        
        When Adding the Images use the invert of the Image
        
    """
    # transform horizontal lines 2 times with flipped image for accuracy

    horizontal1 = hough_transform(horizontal)
    # flip and second go
    horizontal2 = cv2.rotate(horizontal, cv2.ROTATE_180)
    horizontal2 = hough_transform(horizontal2)
    horizontal2 = cv2.rotate(horizontal2, cv2.ROTATE_180)
    # add both and invert
    horizontal = 255 - (255-horizontal1 + (255-horizontal2))

    # transform vertical lines
    vertical1 = hough_transform(vertical)
    # flip and second go
    vertical2 = cv2.rotate(vertical, cv2.ROTATE_180)
    vertical2 = hough_transform(vertical2)
    vertical2 = cv2.rotate(vertical2, cv2.ROTATE_180)
    # add both and invert
    vertical = 255 - (255-vertical1 + (255-vertical2))

    # add vert and horiz lines as inverses
    lineImg = 255 - (255 - horizontal + (255 - vertical))

    # if debug:
    #     # show_wait_destroy('verticalHough.jpg', vertical)
    #     # show_wait_destroy('horizontalHough.jpg', horizontal)
    #     # show_wait_destroy('Refined lines added.jpg', lineImg)

    """
        -Find Contours-> Cells-
        
        After Preprocessing the Line Image find the Contours of every Cell
        Will be used to find Cells, Rows and Columns
        
    """

    # Preprocess Line Image
    lineImgContours = cv2.cvtColor(lineImg, cv2.COLOR_BGR2GRAY)     # grayscale
    ret, lineImgContours = cv2.threshold(lineImgContours, 127, 255, 0)      # threshold

    # Find Contours
    contours, hierarchy = cv2.findContours(lineImgContours, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Visual Representation
    cv2.drawContours(lineImg, contours, -1, (0, 255, 0), 2)
    # if debug:
    #     show_wait_destroy('Raw Contours.jpg', lineImg)

    """
        -Filter Contours-
        
        Used Filter:
        1. Filter for Cells (Rectangles) via Shape Approximation
        2. Filter for a given Cell Size
        
    """

    filteredContours = []
    for cnt in contours:

        # Shape Approximation
        epsilon = 0.001 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        if len(approx) == 4:                                # Filter 1: just include 4 corner Shapes
            if cv2.contourArea(cnt) > 300.0:                # Filter 2: just include size bigger than 300^2 px
                filteredContours.append(cnt)

    # Visual Representation
    cv2.drawContours(lineImg, filteredContours, -1, (255, 0, 0), 2)
    cv2.drawContours(paintedImg, filteredContours, -1, (255, 0, 0), 2)

    # if debug:
    #     show_wait_destroy('Filtered Contours.jpg', lineImg)

    """
        -Find Rows and Columns-

        Find Rows and Columns of the table based on the found Contours
        Save every found Row/Column once in rowsRange/columnsRange Variable
        Save every Contour with a defined Row/Column to rows/columns  
        Tolerance defines the tolerance between found Rows in Pixel
        
        Steps: 
        1. Create empty Lists
        2. Find Centroid (Schwerpunkt) of every Contour
        3. Based on the Centroid, search for an existing Row/Column with the given tolerance
            - If a Row/Column already exists, assign the Contour
            - If no Row/Column was found, create a new one, hold track of it and then assign the Contour
            
    """

    # Step 1:
    rows = []           # indexes every Contour with a row height and a row Index of rowRange
    columns = []        # indexes every Contour with a columns width and a columns Index of columnRange
    rowRange = []       # holds track of every row with a given height +- tolerance
    columnRange = []    # holds track of every columns with a given height +- tolerance

    index = 0
    tolerance = 2       # in px
    for cnt in filteredContours:

        # Step 2: Find Centroid of every Contour
        M = cv2.moments(cnt)
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        # draw a circle for visual marking
        cv2.circle(paintedImg, (cx, cy), radius=0, color=(0, 0, 255), thickness=10)

        # Step 2: for Rows
        if len(rowRange) == 0:                                                          # no rows yet
            rowRange.append(cy)                                                         # append new Row
            rows.append([cy, index, 0])                                                 # cy creates new row
        else:
            for i in range(len(rowRange)):                                              # search for existing row
                if cy > rowRange[i] + tolerance or cy < rowRange[i] - tolerance:        # tolerance +- 2 pixel
                    if i == len(rowRange)-1:                                            # no fitting row found
                        rowRange.append(cy)                                             # append new Row
                        rows.append([cy, index, i+1])                                   # cy creates new row index +1
                else:
                    rows.append([cy, index, i])                                     # cy is in the tolerance, row found
                    break

        # Step 2: for Columns
        if len(columnRange) == 0:                                                       # no rows yet
            columnRange.append(cx)                                                      # append new Row
            columns.append([cx, index, 0])                                              # cx creates new row
        else:
            for j in range(len(columnRange)):                                           # search for existing col
                if cx > columnRange[j] + tolerance or cx < columnRange[j] - tolerance:  # tolerance +- 2 pixel
                    if j == len(columnRange)-1:                                         # no fitting col found
                        columnRange.append(cx)                                          # append new col
                        columns.append([cx, index, j+1])                                # cx creates new column index +1
                else:
                    columns.append([cx, index, j])                                  # cx is in the tolerance, col found
                    break

        index += 1       # hold track of index of item from filteredContours List

    # Visual Representation of all found Contours, Rows and Columns with their Centroids
    if debug:
        show_wait_destroy('Computer Vision.jpg', paintedImg)

    """
        -Slice Image-
        
        Slice the Original Image according to the Found Rows and Columns
        Every cell is represented as a single Image which will be processed by OCR    
        Steps:
        1. Preprocess the whole Original Image for better OCR results
        2. Create a List which will contain every sliced Image
        3. Calculate Coordinates for Image slicing based on the found Contours (Rectangles)
            - get all rectangle coordinates
            - calculate longest distance from P1 because only two corners are needed for slicing
        4. actually slice the Images
        
    """

    # Step 1: preprocess the Image

    # gray = cv2.bitwise_not(gray)

    origImg = cv2.cvtColor(origImg, cv2.COLOR_BGR2GRAY)                             # grayscale

    # ret, origImg = cv2.threshold(np.array(origImg), 125, 255, cv2.THRESH_BINARY)    # threshold
    # ret, origImg = cv2.threshold(origImg, 125, 255, cv2.THRESH_BINARY)
    # ret, origImg = cv2.threshold(origImg, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # origImg = cv2.adaptiveThreshold(origImg, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY, 11, 2)

    # show_wait_destroy("", origImg)

    # Step 2: create empty List
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

        # Step 3: for every rectangle (with pythagoras)
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

        # correct Point coordinates for line height/width
        # px -= 1
        # py -= 1

        # Step 4: slice the Image at calculated coordinates
        if y1 != py and x1 != px:
            slicedImage = origImg[y1:py, x1:px].copy()
            imageList.append(slicedImage)

    """
        -Create empty Pandas DF-

        create an empty DataFrame with the calculated size
        
    """

    row = range(len(rowRange))                  # size of rows
    col = range(len(columnRange))               # size of columns
    df = pd.DataFrame(index=row, columns=col)   # create DF

    """
        -MP OCR every Images-

        Multi Processes all sliced Images with the OCR engine
        Writes the results to the DataFrame 
        
    """

    start = time.time()     # timer for Performance Measurement
    print("Ocr begin")
    # result list has [index, result] to keep track of processed images
    resultList = []
    pool = mp.Pool(mp.cpu_count())
    resultList.append(pool.starmap(tesseract_ocr_mp, enumerate(imageList)))
    pool.close()
    print("Ocr done")
    # results are out of Order, sort them by the Index
    resultList.sort(key=lambda x: x[0])

    # write result in DataFrame for export
    for i in range(len(resultList[0])):
        r = len(rowRange) - 1 - rows[i][2]          # coordinate of row
        c = len(columnRange) - 1 - columns[i][2]    # coordinate of col

        # print(resultList[i][1])
        df.iat[r, c] = resultList[0][i][1]

    if debug:
        print(df)

    # timer for Performance Measurement
    stop = time.time()
    print((stop - start), "s for MP OCR")

    """
        -OCR every Images-

        Same as above but without the Multiprocessing => at least 3 times slower
        
    """
    # start = time.time()
    # print("Ocr begin")
    #
    # for i in range(len(imageList)):
    #     r = len(rowRange)-1-rows[i][2]      # coordinate of row
    #     c = len(columnRange)-1-columns[i][2]   # coordinate of col
    #
    #     df.iat[r, c] = tesseract_ocr(imageList[i])
    #
    # print("Ocr done")
    # stop = time.time()
    # print((stop-start), "s for OCR")


    """
        -Export-
        
        Possible Outputs:
        0. "cvs" => DEFAULT creates new Sheet in CSV format on a given Path 
        1. "excel"          creates new Excel Sheet on a given Path
        2. "clipboard"      copies Table to Clipboard for pasting to file
        
        => Path can be set by giving an output_path Value. Defaults to Input Path
                
    """

    # if output_path == "":
    #     # format the output path and remove the ".png" or ".jpg" or ".jpeg" file ending
    #     # find "." starting from 5 index before the end of the string
    #     i = input_path.find(".", len(input_path) - 5, len(input_path))
    #     if i == -1:             # no file ending found
    #         i = len(input_path)
    #     # remove file ending
    #     output_path = input_path[:i:]
    #
    # # look for given output Format and Export the DataFrame
    # if output_format == "excel":
    #     df.to_excel(output_path + ".xlsx", index=False, header=False)
    # elif output_format == "clipboard":
    #     df.to_clipboard(excel=True, index=False, header=False)
    # else:   # default
    #     df.to_csv(output_path + ".csv", index=False, header=False)
    return df


# if __name__ == "__main__":
#     table_to_ocr(input_path="images/Excel/ExcelTabelle.png", debug=True)
#     # main("images/Bundesliga.png", True)
