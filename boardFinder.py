import cv2
import numpy as np
from shapely.geometry import Polygon
from shapely.geometry import Point
from typing import List
from timeit import default_timer as timer
from quad import Quad


class BoardFinder:

    def idsPresent(ids):
        return (ids is not None and 0 in ids and 1 in ids and 2 in ids and 3 in ids)


    def findCorners(bboxs, ids):
        #print(f'finding corners on: {img.shape}')
        #bboxs, ids = aruco.findArucoMarkers(img, draw=draw)
        idAry = ids.flatten()
        if (BoardFinder.idsPresent(idAry)):
            tl = bboxs[np.where(idAry == 0)[0][0]][0][0].astype(int)
            tr = bboxs[np.where(idAry == 1)[0][0]][0][0].astype(int)
            br = bboxs[np.where(idAry == 2)[0][0]][0][0].astype(int)
            bl = bboxs[np.where(idAry == 3)[0][0]][0][0].astype(int)
            return np.array([tl, tr, br, bl], np.float32)
        else:
            return None

    def between(p1, p2, distance):
        x = (p2[0] - p1[0]) * distance + p1[0]
        y = (p2[1] - p1[1]) * distance + p1[1]
        return [int(x), int(y)]

    def getSquares(warpedImg, warpWidth, warpHeight, drawPoints=True, drawSquares=True):
        #print(warpedImg.shape)
        #warpHeight, warpWidth,  _ = warpedImg.shape
        points = []
        for j in range(0,9):
            yl = BoardFinder.between([0,0], [0,warpHeight-1], j/8)
            row = []
            for i in range(0,9):
                bt = BoardFinder.between(yl, [warpWidth-1,yl[1]], i/8)
                #print(bt)
                row.append(bt)
                #cv2.circle(warpedImg, bt, 10, (255,0,0), 3)
            points.append(row)
        #print(points)
        if drawPoints:
            for row in points:
                for point in row:
                    cv2.circle(warpedImg, point, 10, (255,0,0), 3)
            
        squares = []
        for i in range (0,8):
            row = []
            rowLabel = 8-i
            for j in range(0,8):
                columnLabel = chr(97 + j)
                s = Quad(points[i][j], points[i][j+1], points[i+1][j+1], points[i+1][j], f'{columnLabel}{rowLabel}')
                row.append(s)
                if drawSquares:
                    cv2.polylines(warpedImg, s.polyCoords(), True, thickness=3, color=(0,0,255))
                    cv2.putText(warpedImg, s.name, [s.bl[0] + 10, s.bl[1] - 10], cv2.FONT_HERSHEY_SIMPLEX, 2, color=(0,0,255), thickness=3, lineType=2)

            squares.append(row)

        return squares
        #s : Square = Square(points[0][0], points[0][1], points[1][1], points[1][0], 'a1')
        
    def getOriginalSquares(inverseMatrix, warpedSquares):
        retval = []
        for row in warpedSquares:
            newRow = []
            for square in row:
                newSquare = square.warpInverse(inverseMatrix)
                newRow.append(newSquare)
            retval.append(newRow)
        return retval

    def getWarpBoard(img, rect, draw=True):
        tl, tr, br, bl = rect
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        # ...and now for the height of our new image
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        # take the maximum of the width and height values to reach
        # our final dimensions
        maxWidth = max(int(widthA), int(widthB))
        maxHeight = max(int(heightA), int(heightB))
        # construct our destination points which will be used to
        # map the screen to a top-down, "birds eye" view
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype = "float32")
        # calculate the perspective transform matrix and warp
        # the perspective to grab the screen
        #print(rect)
        #print(dst)
        warpMatrix = cv2.getPerspectiveTransform(rect, dst)
        warp = None
        if draw:
            print("drawing warped board")
            warp = cv2.warpPerspective(img, warpMatrix, (maxWidth, maxHeight))
        return warp, warpMatrix, maxWidth, maxHeight