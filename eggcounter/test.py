from __future__ import print_function
import cv2
import numpy
import copy
import sys

filename = sys.argv[1]
print("Load %s" % filename)

img = cv2.imread(filename)
original = copy.copy(img)
img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

'''
img2 = cv2.imread('without.jpg')
img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

img = img2
'''

def erode(img):
    x = 8
    k0 = numpy.ones((x, x), numpy.uint8)
    return cv2.erode(img, k0, iterations=1)

def dilate(img):
    x = 7
    k0 = numpy.ones((x, x), numpy.uint8)
    return cv2.dilate(img, k0, iterations=1)

def threshold(img, limits=(210, 255)):
    #_, thresh = cv2.threshold(img, 235, 255, cv2.THRESH_TOZERO)
    _, thresh = cv2.threshold(img, limits[0], limits[1], cv2.THRESH_TOZERO)
    return thresh



IMAGE_SIZE = (1024, 768)
IMAGE_SUBSTRACT_WIDTH = 200

img = img[0:IMAGE_SIZE[1] / 2, IMAGE_SUBSTRACT_WIDTH / 2:IMAGE_SIZE[0] - IMAGE_SUBSTRACT_WIDTH / 2]

img = threshold(img)

img = erode(img)

#img = cv2.GaussianBlur(img,(5,5),0)
img = dilate(img)


cv2.imwrite('out.jpg', img); #sys.exit()

def drawInfo(out, x, y, text, color=(255, 255, 0)):

    x += IMAGE_SUBSTRACT_WIDTH / 2

    font = cv2.FONT_HERSHEY_COMPLEX

    # Write on image
    cv2.putText(out, str(text), (x, y - 5), font, 2, color)
    #img = cv2.line(img,(0,0),(511,511),(255,0,0),5)
    #cv2.drawContours(out,[cnt],0,color,-1)
    cv2.rectangle(out, (x, y),(x + w, y + h), (0, 0, 255), 1)
    coordinates = x + w / 2, y + h / 2
    # Draw target
    cv2.line(out, (x + w / 2, y), (x + w / 2, y + h), (0, 0, 255), 1)
    cv2.line(out,(x, y + h / 2),(x + w, y + h / 2), (0, 0, 255), 1)


#mode = cv2.RETR_EXTERNAL
mode = cv2.RETR_LIST
#mode = cv2.RETR_CCOMP
#mode = cv2.RETR_TREE

min_carea = 700
max_carea = 2100
egg_count = 0

#wsize=(30, 62)
wsize=(30, 82)
hsize=(20, 62)

#method = cv2.CHAIN_APPROX_NONE
method = cv2.CHAIN_APPROX_SIMPLE
##method = cv2.CHAIN_APPROX_TC89_L1
#method = cv2.CHAIN_APPROX_TC89_KCOS
contours, h = cv2.findContours(img, mode, method)
for cnt in contours:
    approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)

    #if 11 < len(approx) < 15:
    if 21 > len(approx) > 5:
        ellipse = cv2.fitEllipse(cnt)
        h = ellipse[1][0]
        w = ellipse[1][1]

        adist = cv2.arcLength(cnt, True)
        carea = cv2.contourArea(cnt)

        if not (hsize[0] < h < hsize[1] and wsize[0] < w < wsize[1]):
            #print('Size (w:%i, h:%i) not in range (w:%i-%i, h:%ix%i)' % (w, h, wsize[0], wsize[1], hsize[0], hsize[1]))
            continue

        if not (min_carea < carea < max_carea):
            print('Contour area (%i) not in range (min:%i) !' % (carea, min_carea))
            continue

        print('found: carea:%i, size:%ix%i, adist:%i, approx:%i' % (carea, w, h, adist, len(approx)))

        marea = cv2.minEnclosingCircle(cnt)
        print('Min area:', marea)

        egg_count += 1
        x,y,w,h = cv2.boundingRect(cnt)
        drawInfo(original, x, y, egg_count)

        #drawInfo(img, x, y, egg_count)
        #else:
        #    print('h:', h, hsize, ', w:', w, wsize)
        #    print('len approx: %i, height: %i, width: %i, aDist:%i, contour area:%i' % (len(approx), h, w, adist, carea))
        #    print('--')

out = img
#out = original
#out = cv2.absdiff(img1, img2)

#cv2.imshow('desc', img1)
#cv2.imwrite('img1.jpg', img1)
#cv2.imwrite('img2.jpg', img2)
#cv2.imwrite('out.jpg', out)

#cv2.imwrite('out.jpg', original)

print('Found %i egg(s)' % egg_count)

