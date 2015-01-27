from __future__ import print_function
import sys
import os
import cv2
import numpy
from copy import copy
from matplotlib import pyplot
from ConfigParser import ConfigParser, NoSectionError

IMAGE_SIZE = (1024, 768)
IMAGE_SUBSTRACT_WIDTH = 200

# Contour area
carea_limits = (700, 2100)

# Size limits
width_limits = (25, 82)
height_limits = (20, 62)

# Threshold
threshold_limits = (110, 255)

# Approx poly length
approx_poly_length = (5, 21)

erode_kernel = 8
dilate_kernel = 7

contour_limit = 17

def load_config(filename, defaults=globals(), verbose=False):
    conf = ConfigParser()
    conf.readfp(open(filename))

    if verbose:
        print('Load config from %s file !' % filename)

    # Load min/max
    minmax = ('min', 'max')
    configuration = {}
    for section, kind in (('carea_limits', minmax), ('width_limits', minmax),
                    ('height_limits', minmax), ('threshold_limits', minmax),
                    ('approx_poly_length', minmax),
                    ('erode_kernel', 'value'), ('dilate_kernel', 'value')):
        try:
            if type(kind) == tuple:
                configuration[section] = [ int(conf.get(section, val)) for val in kind ]
            elif type(kind) == str:
                configuration[section] = int(conf.get(section, kind))
        except NoSectionError:
            configuration[section] = defaults[section]

    return configuration

configuration = globals()
configfile = os.path.dirname(os.path.realpath(__file__)) + '/config.ini'
if os.path.exists(configfile):
    configuration = load_config(configfile, verbose=True)

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
        elif chr(key) == 'q':
            break

def scan_image( filename,
                normal_file=None,
                export_file=None,
                debug=False,
                verbose=False,
                carea_limits=carea_limits,
                width_limits=width_limits,
                height_limits=height_limits,
                threshold_limits=threshold_limits,
                approx_poly_length=approx_poly_length,
                erode_kernel=erode_kernel,
                dilate_kernel=dilate_kernel,
                contour_limit=contour_limit):
    '''
    Scan une image a la recherche d'oeufs
    - filename:     Fichier d'entree dans un format lisible par opencv (jpg, png)
    - normal_file:  C'est le fichier d'entree (jpg, png) sur lequel sera applique les dessins suite a detection
    - export_file:  Fichier de sortie final
    '''

    egg_count = 0
    mark = True

    nest_index = None

    if verbose:
        print("""Configuration:
 Contour area limits: %i - %i
 Width limits       : %i - %i
 Height limits      : %i - %i""" % (carea_limits[0], carea_limits[1], width_limits[0], width_limits[1], height_limits[0], height_limits[1]))

    def threshold(img, limits=(210, 255)):
        #_, thresh = cv2.threshold(img, 235, 255, cv2.THRESH_TOZERO)
        _, thresh = cv2.threshold(img, limits[0], limits[1], cv2.THRESH_TOZERO)
        return thresh

    def erode(img):
        k0 = numpy.ones((erode_kernel,) * 2, numpy.uint8)
        return cv2.erode(img, k0, iterations=1)

    def dilate(img):
        k0 = numpy.ones((dilate_kernel,) * 2, numpy.uint8)
        return cv2.dilate(img, k0, iterations=1)

    img_original = cv2.imread(filename)
    if img_original == None:
        print("File not found !")
        return 0, None

    if normal_file:
        out = cv2.imread(normal_file)
    else:
        out = copy(img_original)

    while True:
        img = cv2.cvtColor(img_original, cv2.COLOR_BGR2GRAY)
        #imgray = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)

        # Crop image on nest
        img = img[0:IMAGE_SIZE[1] / 2, IMAGE_SUBSTRACT_WIDTH / 2:IMAGE_SIZE[0] - IMAGE_SUBSTRACT_WIDTH / 2]

        if mark:
            imgmark = copy(img)

        '''
        #imgray = cv2.medianBlur(imgray, 7)
        #cv2.imshow('image', imgray)
        #cv2.waitKey(0)
        #imgSplit = cv2.split(im)
        opened = cv2.morphologyEx(imgray, cv2.MORPH_OPEN, kernel)
        '''

        img = threshold(img, threshold_limits)
        img = erode(img)
        img = dilate(img)

        if debug:
            imgdebug = copy(img)
            cv2.imwrite('debug.jpg', img)

        # cv2.RETR_EXTERNAL, cv2.RETR_CCOMP, cv2.RETR_TREE
        mode = cv2.RETR_LIST

        # cv2.CHAIN_APPROX_NONE, cv2.CHAIN_APPROX_TC89_L1, cv2.CHAIN_APPROX_TC89_KCOS
        method = cv2.CHAIN_APPROX_SIMPLE
        contours, h = cv2.findContours(img, mode, method)

        if len(contours) > contour_limit:
            if debug:
                print('[Skip!] Contour length (%i) > limit (%i), thresholds: %s' % (len(contours), contour_limit, str(threshold_limits)))
            mint, maxt = threshold_limits
            mint += 10
            #mint += 4
            if mint >= 255:
                break

            threshold_limits = (mint, maxt)
            continue

        egg_count = 0
        index = -1
        for cnt in contours:
            index += 1

            def draw_debug(image, text_color=(255, 255, 0), graph_color=(0, 0, 255)):
                #x = x + IMAGE_SUBSTRACT_WIDTH / 2
                cv2.putText(image, '%02i' % index, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 2, text_color)
                cv2.line(image, (x + w / 2, y), (x + w / 2, y + h), graph_color, 1)
                cv2.line(image,(x, y + h / 2), (x + w, y + h / 2), graph_color, 1)

            def skip(message):
                if verbose:
                    print('[Skip!] %02i. %s' % (index, message))
        
                if mark:
                    draw_debug(imgmark)

            approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
            x, y, w, h = cv2.boundingRect(cnt)

            if not (approx_poly_length[0] <= len(approx) <= approx_poly_length[1]):
                skip("Approx poly length (%i) not in range !" % len(approx))
                continue

            ellipse =  cv2.fitEllipse(cnt)
            ellipse_h, ellipse_w = ellipse[1][0], ellipse[1][1]
            if not (width_limits[0] <= ellipse_w <= width_limits[1] and height_limits[0] <= ellipse_h <= height_limits[1]):
                skip('Size (%i, %i) not in range !' % (ellipse_w, ellipse_h))
                continue

            # Potentiel egg area
            '''
            import math
            ellipse_area = math.pi * w * h
            #if not (2000 < ellipse_area < 6000):
            #    #if verbose:
            #    print('[Skip] Ellipse area (%i) not in range (%i-%i) !' % (ellipse_area, 0, 0))
            #    continue
            '''

            adist = cv2.arcLength(cnt, closed=True)

            carea = cv2.contourArea(cnt)

            #index += 1
            if not (carea_limits[0] <= carea <= carea_limits[1]):
                skip('Contour area (%i) not in range !' % (carea))
                continue

            if verbose:
                print('[Found] %02i, len approx: %i, size: %i, %i, aDist:%i, contour area:%i' % (index, len(approx), h, w, adist, carea))
                if mark:
                    draw_debug(imgmark)

            colors = (
                (0, 0, 255),
                (255, 0, 0),
                (0, 255, 0),
            )

            def draw_info(image, x, y, w, h, index, margin=0, fill=False, target=False, text_color=(255, 255, 0), graph_color=(0, 0, 255)):

                x -= margin
                w += margin * 2
                y -= margin
                h += margin * 2

                # Write on image
                cv2.putText(image, str(index), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 2, text_color)
                cv2.rectangle(image, (x, y), (x + w, y + h), graph_color, 1)

                if target:
                    cv2.line(image, (x + w / 2, y), (x + w / 2, y + h), graph_color, 1)
                    cv2.line(image,(x, y + h / 2), (x + w, y + h / 2), graph_color, 1)

                if fill:
                    cv2.drawContours(image, [cnt], 0, graph_color, -1)

            cnt = cnt + (IMAGE_SUBSTRACT_WIDTH / 2, 0)
            draw_info(out, x + IMAGE_SUBSTRACT_WIDTH / 2, y, w, h, egg_count, margin=10, text_color=colors[egg_count % len(colors)], graph_color=colors[egg_count % len(colors)])

            nest_index = 1 if x > ((IMAGE_SIZE[0] - IMAGE_SUBSTRACT_WIDTH) / 2) else 2

            egg_count += 1

        if debug:
            #cv2.imshow('im',imgray)

            images = [ imgdebug, out, img_original ]
            if mark:
                images.insert(0, imgmark)

            alternate(images, img)

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
      eggcount.py [-vdt] --config=<path> <name>...
      eggcount.py (-h | --help)

    Options:
      -h --help             _o/
      -v --verbose          Verbose mode
      -d --debug            Debug mode (use previous / next key to switch between different version of image, original version with bottom key)
      -t --test-threshold   Test threshold
      -c --config=<path>    Import config from file
    """

    #eggcount.py [-vdt] --contour-area=<int> <name>...
    #--contour-area=<int>    Min contour area

    args = docopt(help, version='0.1')

    total = good = extra = missed = badnest = 0
    for filename in args['<name>']:
        if args['--test-threshold']:
            test_threshold(filename)
        else:
            m = re.search('([0-9]+)_([0-9]+)_*((?:[-a-z0-9]*).*)\.(jpg|png)', filename)
            if not m:
                continue

            # Load config if exists
            configfile = os.path.dirname(os.path.realpath(filename)) + '/config.ini'
            if not os.path.exists(configfile):
                configfile = None

            if args['--config']:
                configfile = args['--config']

            if configfile:
                configuration = load_config(configfile, configuration, verbose=args['--verbose'])

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

            #carea = int(args['--contour-area']) if args['--contour-area'] else carea_limits[0]

            '''
            if args['--config']:
                if args['--debug']:
                    print('Load config from %s file !' % args['--config'])

                config = __import__(args['--config'])
                config = getattr(config, args['--config'].split('.')[-1])

                for field in ('carea_limits', 'width_limits', 'height_limits', 'threshold_limits'):
                    try:
                        val = getattr(config, field)
                        if val:
                            #print('Set %s -> %s' % (field, val))
                            globals()[field] = val
                    except AttributeError:
                        pass
            '''

            '''
            if False:
                for threshold_limits in ( (210, 255), (235, 255) ):
                    egg_count, nest_index = scan_image(filename, threshold_limits=threshold_limits, debug=args['--debug'], verbose=args['--verbose'])
                    if egg_count:
                        break
            else:
                #egg_count, nest_index = scan_image(filename, debug=args['--debug'], verbose=args['--verbose'], carea_limits=carea_limits, width_limits=width_limits, height_limits=height_limits, threshold_limits=threshold_limits)
            '''
            egg_count, nest_index = scan_image(filename, debug=args['--debug'], verbose=args['--verbose'], **configuration)

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

