import cv2
import numpy as np
import sys

img = cv2.imread('tests/with/7_2_highlight.jpg',0)
if img==None:
    print "cannot open ",filename

else:
    img = cv2.medianBlur(img,5)
    cimg = cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)
    circles = cv2.HoughCircles(img,cv2.cv.CV_HOUGH_GRADIENT,1,10,param1=100,param2=30,minRadius=50,maxRadius=100)
    circles = np.uint16(np.around(circles))
    for i in circles[0,:]:
        cv2.circle(cimg,(i[0],i[1]),i[2],(0,255,0),1) # draw the outer circle
        cv2.circle(cimg,(i[0],i[1]),2,(0,0,255),3) # draw the center of the circle

    cv2.imshow('detected circles',cimg)
    cv2.waitKey(0)
    cv2.imwrite('output.png',cimg)
    cv2.destroyAllWindows()
