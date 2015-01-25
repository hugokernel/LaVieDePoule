from __future__ import print_function
import sys
import copy
import cv2
import numpy
from matplotlib import pyplot

MIN_CAREA = 700
#MIN_CAREA = 780
MAX_CAREA = 2100

IMAGE_SIZE = (1024, 768)
IMAGE_SUBSTRACT_WIDTH = 200

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

"""
def threshold(img, limits=(210, 255)):
    #_, thresh = cv2.threshold(img, 235, 255, cv2.THRESH_TOZERO)
    _, thresh = cv2.threshold(img, limits[0], limits[1], cv2.THRESH_TOZERO)
    return thresh

def erode(img):
    x = 8
    k0 = numpy.ones((x, x), numpy.uint8)
    return cv2.erode(img, k0, iterations=1)

def dilate(img):
    x = 7
    k0 = numpy.ones((x, x), numpy.uint8)
    return cv2.dilate(img, k0, iterations=1)

def scan_nest(img, egg_size_coeff=1, debug=False, verbose=False):

    mode = cv2.RETR_LIST                # RETR_EXTERNAL, RETR_CCOMP, RETR_TREE
    method = cv2.CHAIN_APPROX_SIMPLE    # CHAIN_APPROX_NONE, CHAIN_APPROX_TC89_L1, CHAIN_APPROX_TC89_KCOS

    contours, h = cv2.findContours(img, mode, method)

    contour_limit = 15
    approx_poly_length = (5, 21)

    if len(contours) > contour_limit:
        if debug:
            print('Contour length (%i) > limit (%i), thresholds: %s' % (len(contours), contour_limit, str(threshold_limits)))
        return None

    eggs = []
    for cnt in contours:
        #approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
        #if not (approx_poly_length[0] < len(approx) < approx_poly_length[1]):
        #    if verbose:
        #        print("[Skip] Approx poly length (%i) not in range (%s) !" % (len(approx), str(approx_poly_length)))
        #    break

        print(len(cnt))
        if len(cnt) < 5:
            continue

        #ellipse =  cv2.fitEllipse(cnt)
        #h, w = ellipse[1][0], ellipse[1][1]
        #print(w, h)
        #if not (wsize[0] <= w <= wsize[1] and hsize[0] <= h <= hsize[1]):
        #    if verbose:
        #        print('[Skip] Size (%i, %i) not in range (w:%i-%i, h:%i-%i))' % (w, h, wsize[0], wsize[1], hsize[0], hsize[1]))
        #    break

        # Potentiel egg area
        #import math
        #ellipse_area = math.pi * w * h

        cv2.imwrite('debug.jpg', img)

        x, y, w, h = cv2.boundingRect(cnt)
        print(w, h)

        adist = cv2.arcLength(cnt, closed=True)

        carea = cv2.contourArea(cnt)

        #print(carea, ellipse_area)

        #index += 1
        #MAX_CAREA = 2900
        #if not (MIN_CAREA < carea < MAX_CAREA):
        #    if verbose:
        #        print('[Skip] Contour area (%i) not in range (%i-%i) !' % (carea, MIN_CAREA, MAX_CAREA))
        #    break

        #if verbose:
        #    print('[found]')
        #    print('Egg index:%i, len approx: %i (limit: %s), height: %i, width: %i, aDist:%i, contour area:%i' % (index, len(approx), str((5, 21)), h, w, adist, carea))

        eggs.append((x, y, w, h))

    return eggs

def drawInfo(out, x, y, w, h, x_offset, egg_count=0):

    x += x_offset

    # Write on image
    cv2.putText(out, str(egg_count), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 0))
    #img = cv2.line(img,(0,0),(511,511),(255,0,0),5)

    #cv2.drawContours(out,[cnt+(x_offset, 0)],0,(255,255,0),-1)
    cv2.rectangle(out, (x, y),(x + w, y + h), (0, 0, 255), 1)

    coordinates = x + w / 2, y + h / 2

    # Draw target
    cv2.line(out, (x + w / 2, y), (x + w / 2, y + h), (0, 0, 255), 1)
    cv2.line(out,(x, y + h / 2),(x + w, y + h / 2), (0, 0, 255), 1)

def test_image(filename):

    img_original = cv2.imread(filename)

    image_width, image_height = IMAGE_SIZE

    '''
    Nest position [ y pos start, y pos end, x pos start, x pos end ]
    '''
    nest0 = [ 150, 350, 180, image_width / 2 ]
    nest1 = [ 150, 350, image_width / 2, image_width - 180 ]

    def crop(data, coord):
        return data[coord[0]:coord[1], coord[2]:coord[3]]

    for nest in (nest0, nest1):
        img = cv2.cvtColor(img_original, cv2.COLOR_BGR2GRAY)
        img_cropped = crop(img, nest)

        img = copy.copy(img_cropped)
        #cv2.imwrite('debug.jpg', img)
        #import time; time.sleep(2)

        img = threshold(img)
        img = erode(img)
        img = dilate(img)
        out = scan_nest(img, debug=True, verbose=True)

        print(out)
        for item in out:
            x, y, w, h = item
            drawInfo(img_cropped, x, y, w, h, 0)
            cv2.imwrite('debug.jpg', img_cropped)
            #break

test_image(sys.argv[1])

sys.exit()
"""

def scan_image(filename, export_file=None, debug=False, verbose=False, min_carea=MIN_CAREA, wsize=(30, 82), hsize=(20, 62), threshold_limits=(210, 255)):
#def scan_image(filename, debug=False, verbose=False, min_carea=MIN_CAREA, wsize=(12, 60), hsize=(12, 60)):

    nest_index = None

    if verbose:
        print('\nParameters: Min contour area: %i, width size: %i, %i, height size: %i, %i' % (min_carea, wsize[0], wsize[1], hsize[0], hsize[1]))

    def threshold(img, limits=(210, 255)):
        #_, thresh = cv2.threshold(img, 235, 255, cv2.THRESH_TOZERO)
        _, thresh = cv2.threshold(img, limits[0], limits[1], cv2.THRESH_TOZERO)
        return thresh

    def erode(img):
        x = 8
        k0 = numpy.ones((x, x), numpy.uint8)
        return cv2.erode(img, k0, iterations=1)

    def dilate(img):
        x = 7
        k0 = numpy.ones((x, x), numpy.uint8)
        return cv2.dilate(img, k0, iterations=1)

    img_original = cv2.imread(filename)
    if img_original == None:
        print("File not found !")
        return 0, None

    while True:
        out = copy.copy(img_original)
        img = cv2.cvtColor(img_original, cv2.COLOR_BGR2GRAY)
        #imgray = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)

        # Crop image on nest
        img = img[0:IMAGE_SIZE[1] / 2, IMAGE_SUBSTRACT_WIDTH / 2:IMAGE_SIZE[0] - IMAGE_SUBSTRACT_WIDTH / 2]

        '''
        #imgray = cv2.medianBlur(imgray, 7)
        #cv2.imshow('image', imgray)
        #cv2.waitKey(0)
        #imgSplit = cv2.split(im)
        opened = cv2.morphologyEx(imgray, cv2.MORPH_OPEN, kernel)
        '''

        #alternate([ cv2.erode(imgray, k0, iterations=1), imgray ])

        img = threshold(img, threshold_limits)
        #img = threshold(img, (230, 255))

        img = erode(img)
        img = dilate(img)

        #cv2.imwrite('debug.jpg', img)
        #return 0, None

        if debug:
            cv2.imwrite('debug.jpg', img)

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
        contours, h = cv2.findContours(img, mode, method)

        #print('contour:', len(contours))
        contour_limit = 17
        approx_poly_length = (5, 21)

        #contour_limit = 18
        if len(contours) > contour_limit: #04
            if debug:
                print('Contour length (%i) > limit (%i), thresholds: %s' % (len(contours), contour_limit, str(threshold_limits)))
            mint, maxt = threshold_limits
            mint += 10
            #mint += 4
            if mint >= 255:
                break

            threshold_limits = (mint, maxt)
            continue

        for cnt in contours:
            approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)

            if not (approx_poly_length[0] < len(approx) < approx_poly_length[1]):
                if verbose:
                    print("[Skip] Approx poly length (%i) not in range (%s) !" % (len(approx), str(approx_poly_length)))
                continue

            ellipse =  cv2.fitEllipse(cnt)
            h, w = ellipse[1][0], ellipse[1][1]

            #if abs(h-w) < 2:
            #   print 'paf'
                #continue
        #elif len(approx) > 15:
            #print approx, h, w
            #print "circle"
            #if 1 < h < 100 and 1 < w < 100:
            #if 20 < h < 100 and 20 < w < 100:
            #wsize = (30, 117);
            if not (wsize[0] <= w <= wsize[1] and hsize[0] <= h <= hsize[1]):
                if verbose:
                    print('[Skip] Size (%i, %i) not in range (w:%i-%i, h:%i-%i))' % (w, h, wsize[0], wsize[1], hsize[0], hsize[1]))
                continue

            # Potentiel egg area
            import math
            ellipse_area = math.pi * w * h
            #if not (2000 < ellipse_area < 6000):
            #    #if verbose:
            #    print('[Skip] Ellipse area (%i) not in range (%i-%i) !' % (ellipse_area, 0, 0))
            #    continue

            #if len(approx) != 16:
            #    continue
            #print len(approx)
            #print cnt
            x, y, w, h = cv2.boundingRect(cnt)

            adist = cv2.arcLength(cnt, closed=True)
            #print(adist)
            #if adist > 300:
            #    continue

            carea = cv2.contourArea(cnt)

            #print(carea, ellipse_area)

            #index += 1
            #MAX_CAREA = 2900
            if not (MIN_CAREA < carea < MAX_CAREA):
                if verbose:
                    print('[Skip] Contour area (%i) not in range (%i-%i) !' % (carea, MIN_CAREA, MAX_CAREA))
                continue

            if verbose:
                print('[found]')

                print('Egg index:%i, len approx: %i (limit: %s), height: %i, width: %i, aDist:%i, contour area:%i' % (index, len(approx), str((5, 21)), h, w, adist, carea))

            def drawInfo(out, x, y, x_offset):

                x += x_offset

                # Write on image
                cv2.putText(out, str(egg_count), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 0))
                #img = cv2.line(img,(0,0),(511,511),(255,0,0),5)

                cv2.drawContours(out,[cnt+(x_offset, 0)],0,(255,255,0),-1)
                cv2.rectangle(out, (x, y),(x + w, y + h), (0, 0, 255), 1)

                coordinates = x + w / 2, y + h / 2

                # Draw target
                cv2.line(out, (x + w / 2, y), (x + w / 2, y + h), (0, 0, 255), 1)
                cv2.line(out,(x, y + h / 2),(x + w, y + h / 2), (0, 0, 255), 1)

            #drawInfo(out, x, y)
            drawInfo(out, x, y, IMAGE_SUBSTRACT_WIDTH / 2)

            nest_index = 1 if x > ((IMAGE_SIZE[0] - IMAGE_SUBSTRACT_WIDTH) / 2) else 2

            egg_count += 1

        if debug:
            #cv2.imshow('im',imgray)

            alternate([ img, out, img_original ], img)

            cv2.destroyAllWindows()

        break

    if egg_count and export_file:
        cv2.imwrite(export_file, out)

    return egg_count, nest_index

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

    total = good = extra = missed = badnest = 0
    for filename in args['<name>']:
        if args['--test-threshold']:
            test_threshold(filename)
        else:
            m = re.search('([0-9]+)_([0-9]+)_*((?:[-a-z0-9]*).*)\.(jpg|png)', filename)
            if not m:
                continue

            total += 1

            index, count, flags, _ = m.groups()

            count = int(count)

            if args['--verbose']:
                print("Open %s, must found %i" % (filename, count), end=' ')
            else:
                print("Open %s" % (filename), end=' ')

            if flags:
                if flags in ('1', '2'):
                    nest = int(flags)
                else:
                    flags = flags.split('-')
                    if args['--verbose']:
                        print('(flags: ' + ', '.join([ flag for flag in flags ]) + ')', end=' ')

            if args['--debug']:
                print()

            carea = int(args['--contour-area']) if args['--contour-area'] else MIN_CAREA

            if False:
                for threshold_limits in ( (210, 255), (235, 255) ):
                    egg_count, nest_index = scan_image(filename, threshold_limits=threshold_limits, debug=args['--debug'], verbose=args['--verbose'], min_carea=carea)
                    if egg_count:
                        break
            else:
                egg_count, nest_index = scan_image(filename, debug=args['--debug'], verbose=args['--verbose'], min_carea=carea)

            if egg_count != count:
                if egg_count > count:
                    extra += egg_count - count
                else:
                    missed += count - egg_count

                #if args['--verbose']:
                print('[Error] %i egg(s) found !' % (egg_count))
                #else:
                #    print('[Error]')
            else:
                if nest_index and nest_index != nest:
                    badnest += 1
                    print('[Error] Bad nest !')
                else:
                    print('[Ok]')

                    good += 1

    print("Result: %i%% (%i/%i)" % (round(100 / (float(total) / float(good)) if good > 0 else 0), good, total))

    #if args['--verbose']:
    print("- Egg found : %i" % egg_count)
    print("- Extra egg detected : %i" % extra)
    print("- Missed egg : %i" % missed)
    print("- Bad nest : %i" % badnest)

