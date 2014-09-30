from __future__ import print_function
import sys
import copy
import cv2
import numpy
from matplotlib import pyplot

CONTOUR_AREA=1200

def test_threshold(filename):
    img = cv2.imread(filename)
    imgray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    ret, thresh1 = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    ret, thresh2 = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
    ret, thresh3 = cv2.threshold(img, 127, 255, cv2.THRESH_TRUNC)
    ret, thresh4 = cv2.threshold(img, 127, 255, cv2.THRESH_TOZERO)
    ret, thresh5 = cv2.threshold(img, 127, 255, cv2.THRESH_TOZERO_INV)

    thresh = ['img', 'thresh1', 'thresh2', 'thresh3', 'thresh4', 'thresh5']

    for i in xrange(6):
        pyplot.subplot(2, 3, i + 1), pyplot.imshow(eval(thresh[i]), 'gray')
        pyplot.title(thresh[i])

    pyplot.show()

def alternate(images, original=None):
    index = 0
    image = images[index]

    def setimage(value):
        if value >= len(images):
            index = 0
        elif value < 0:
            index = len(images) - 1
        else:
            index = value
        return index, images[index]

    while True:
        cv2.imshow('image', image)

        key = cv2.waitKey(0)
        key &= 0xFF

        if key == 81:
            index, image = setimage(index - 1)
        elif key == 83:
            index, image = setimage(index + 1)
        elif key == 84 and original is not None:
            image = original
        elif key == 27:
            sys.exit()
        else:
            break

def egg_counter(filename, debug=False, verbose=False, doors_open=1, min_carea=CONTOUR_AREA, wsize=(30, 60), hsize=(35, 60)):
#def egg_counter(filename, debug=False, verbose=False, doors_open=1, min_carea=CONTOUR_AREA, wsize=(12, 60), hsize=(12, 60)):

    if verbose:
        print('Min contour area: %i' % min_carea)
        print('Width size: %i, %i' % wsize)
        print('Height size: %i, %i' % hsize)

    img = cv2.imread(filename)
    imgray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #imgray = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)

    #imgray = cv2.medianBlur(imgray, 7)

    #cv2.imshow('image', imgray)
    #cv2.waitKey(0)

    #kernel = numpy.ones((200,200),numpy.uint8)

    #erosion = cv2.erode(imgray,kernel,iterations = 1)

    #imgSplit = cv2.split(im)

    #ret,thresh = cv2.threshold(img,127,255,cv2.THRESH_TOZERO_INV)
    #ret,thresh = cv2.threshold(imgray,127,255,1)
    #ret,thresh = cv2.threshold(imgray,1,50,cv2.THRESH_TOZERO)
    #ret,thresh = cv2.threshold(imgSplit[1],100,100,cv2.THRESH_TOZERO)

    k0 = numpy.ones((13, 13), numpy.uint8)
    #k0 = numpy.ones((5, 5), numpy.uint8)
    k1 = numpy.ones((12, 12), numpy.uint8)
    #k1 = numpy.ones((5, 5), numpy.uint8)
    #i1 = cv2.dilate(imgray, kernel, iterations = 1)

    #kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
    #i2 = cv2.dilate(imgray, kernel, iterations = 1)

    #alternate([ i1, i2 ], img)

    '''
    eroded = cv2.erode(imgray, kernel, iterations = 1)
    dilated = cv2.dilate(imgray, kernel, iterations = 1)

    eroded_dilated = cv2.dilate(eroded, kernel, iterations = 1)

    opened = cv2.morphologyEx(imgray, cv2.MORPH_OPEN, kernel)

    alternate([ imgray, eroded, dilated, eroded_dilated, opened ], img)
    return 0
    '''

    imgray = cv2.erode(imgray, k0, iterations=1)
    imgray = cv2.dilate(imgray, k1, iterations=1)

    #alternate([ cv2.erode(imgray, k0, iterations=1), imgray ])

    doors_open = False

    if doors_open:
        # Porte de droite ouverte:
        ret, thresh = cv2.threshold(imgray, 100, 100, cv2.THRESH_TOZERO)
    else:
        # 2 portes ouvertes:
        #ret, thresh = cv2.threshold(imgray, 80, 200, cv2.THRESH_TOZERO_INV)
        ret, thresh = cv2.threshold(imgray, 80, 90, cv2.THRESH_TOZERO_INV)
        if verbose:
            print('Highlight actived !')
    #ret, thresh = cv2.threshold(imgray, 10, 100, cv2.THRESH_TOZERO_INV)

    #ret,thresh = cv2.threshold(imgray,150,250,cv2.THRESH_)

    #element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(30,30))


    # Otsu's thresholding after Gaussian filtering
    #blur = cv2.GaussianBlur(imgray,(5,5),0)
    #ret3,thresh = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    #print 'Image gray'
    #if verbose:
    #    #cv2.imshow('image', thresh)
    #    cv2.imshow('image', imgray)
    #    cv2.waitKey(0)

    #out = img
    #out = thresh
    out = copy.copy(imgray)

    egg_count = 0
    index = 0

    #mode = cv2.RETR_EXTERNAL
    mode = cv2.RETR_LIST
    #mode = cv2.RETR_CCOMP
    #mode = cv2.RETR_TREE

    #method = cv2.CHAIN_APPROX_NONE
    method = cv2.CHAIN_APPROX_SIMPLE
    #method = cv2.CHAIN_APPROX_TC89_L1
    #method = cv2.CHAIN_APPROX_TC89_KCOS
    contours, h = cv2.findContours(thresh, mode, method)

    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
        

        #if 11 < len(approx) < 15:
        if len(approx) > 5:
            ellipse =  cv2.fitEllipse(cnt)
            h = ellipse[1][0]
            w = ellipse[1][1]

            #if abs(h-w) < 2:
            #   print 'paf'
                #continue
        #elif len(approx) > 15:
            #print approx, h, w
            #print "circle"
            #if 1 < h < 100 and 1 < w < 100:
            #if 20 < h < 100 and 20 < w < 100:
            if hsize[0] < h < hsize[1] and wsize[0] < w < wsize[1]:

                #if len(approx) != 16:
                #    continue
                #print len(approx)
                #print cnt
                x,y,w,h = cv2.boundingRect(cnt)

                adist = cv2.arcLength(cnt, True)
                carea = cv2.contourArea(cnt)
                if verbose:
                    print('Egg:%i, len approx: %i, height: %i, width: %i, aDist:%i, contour area:%i' % (index, len(approx), h, w, adist, carea), end=' ')

                index += 1
                if carea < min_carea:
                    if verbose:
                        print('[not found]')
                    continue

                if verbose:
                    print('[found]')

                def drawInfo(out, x, y):
                  # Write on image
                  cv2.putText(out, str(egg_count), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 0))
                  #img = cv2.line(img,(0,0),(511,511),(255,0,0),5)

                  cv2.drawContours(out,[cnt],0,(255,255,0),-1)
                  cv2.rectangle(out, (x, y),(x + w, y + h), (0, 0, 255), 1)

                  coordinates = x + w / 2, y + h / 2

                  # Draw target
                  cv2.line(out, (x + w / 2, y), (x + w / 2, y + h), (0, 0, 255), 1)
                  cv2.line(out,(x, y + h / 2),(x + w, y + h / 2), (0, 0, 255), 1)

                drawInfo(out, x, y)

                egg_count += 1
        #else:
            #cv2.drawContours(img,[cnt],0,(0,255,255),-1)

    if debug:
        #cv2.imshow('im',imgray)

        alternate([ imgray, out, thresh ], img)

        cv2.destroyAllWindows()

    #cv2.imwrite('out.png', out)

    return egg_count

if __name__ == '__main__':

    import re
    from docopt import docopt

    help = """Egg counter

    Usage:
      eggcount.py [-vdt] <name>...
      eggcount.py [-vdt] --contour-area=<int> <name>...
      eggcount.py (-h | --help)

    Options:
      -h --help               _o/
      -v --verbose            Verbose mode
      -d --debug              Debug mode (use previous / next key to switch between different version of image, original version with bottom key)
      -t --test-threshold     Test threshold
      --contour-area=<int>    Min contour area
    """

    args = docopt(help, version='0.1')

    total = good = extra = missed = 0
    for filename in args['<name>']:
        if args['--test-threshold']:
            test_threshold(filename)
        else:
            m = re.search('([0-9]+)_([0-9]+)_*((?:[-a-z0-9]*).*)\.jpg', filename)
            if not m:
                continue

            total += 1

            index, count, flags = m.groups()

            count = int(count)

            if args['--verbose']:
                print("Open %s, must found %i" % (filename, count), end=' ')
            else:
                print("Open %s" % (filename), end=' ')

            if flags:
                flags = flags.split('-')
                if args['--verbose']:
                    print('(flags: ' + ', '.join([ flag for flag in flags ]) + ')', end=' ')

            if args['--debug']:
                print()

            carea = int(args['--contour-area']) if args['--contour-area'] else CONTOUR_AREA

            if 'highlight' in flags:
                egg_count = egg_counter(filename, doors_open=2, debug=args['--debug'], verbose=args['--verbose'], min_carea=carea)
            else:
                egg_count = egg_counter(filename, debug=args['--debug'], verbose=args['--verbose'], min_carea=carea)

            if egg_count != count:
                if egg_count > count:
                    extra += egg_count - count
                else:
                    missed += count - egg_count
                if args['--verbose']:
                    print('[Error] %i egg(s) found !' % (egg_count))
                else:
                    print('[Error]')
            else:
                print('[Ok]')
                good += 1

    print("Result: %i%% (%i/%i)" % (round(100 / total * good), good, total))
    
    #if args['--verbose']:
    print("- Extra egg detected : %i" % extra)
    print("- Missed egg : %i" % missed)

