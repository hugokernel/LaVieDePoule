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

# Zone
zone_limits = (0, 0, 0, 0)

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

contour_limits = (0, 17)

def load_config(filename, defaults=globals(), verbose=False):
    conf = ConfigParser()
    conf.readfp(open(filename))

    if verbose:
        print('Load config from %s file !' % filename)

    # Load min/max
    minmax = ('min', 'max')
    minmax4 = ('xmin', 'xmax', 'ymin', 'ymax')
    configuration = {}
    for section, kind in (
        ('zone_limits', minmax4),
        ('carea_limits', minmax), ('width_limits', minmax),
        ('height_limits', minmax), ('threshold_limits', minmax),
        ('approx_poly_length', minmax), ('contour_limits', minmax),
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
    configuration = load_config(configfile, verbose=False)

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

def scan_image( input_file,
                support_file=None,
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
                contour_limits=contour_limits,
                zone_limits=zone_limits):
    '''
    Scan une image a la recherche d'oeufs
    - input_file   : Fichier d'entree dans un format lisible par opencv (jpg, png)
    - support_file : C'est le fichier d'entree (jpg, png) sur lequel sera applique les dessins suite a detection
    - export_file  : Fichier de sortie final
    '''

    eggs_found = []

    egg_count = 0
    mark = True

    if verbose:
        print("""Configuration:
 Contour area limits: %i - %i
 Width limits       : %i - %i
 Height limits      : %i - %i
 Approx poly length : %i - %i
 Contour limits     : %i - %i""" % (carea_limits[0], carea_limits[1], width_limits[0], width_limits[1], height_limits[0], height_limits[1], approx_poly_length[0], approx_poly_length[1], contour_limits[0], contour_limits[1]))

    img_original = cv2.imread(input_file)
    if img_original == None:
        print("File not found !")
        return 0, None

    def threshold(img, limits=(210, 255)):
        _, thresh = cv2.threshold(img, limits[0], limits[1], cv2.THRESH_TOZERO)
        return thresh

    def erode(img):
        k0 = numpy.ones((erode_kernel,) * 2, numpy.uint8)
        return cv2.erode(img, k0, iterations=1)

    def dilate(img):
        k0 = numpy.ones((dilate_kernel,) * 2, numpy.uint8)
        return cv2.dilate(img, k0, iterations=1)

    def draw_info(image, x, y, w, h, cnt, index, margin=0, fill=False, target=False, text_color=(255, 255, 0), graph_color=(0, 0, 255)):

        # Detection zone
        cv2.rectangle(image, (zone_limits[0], zone_limits[2]), (zone_limits[1], zone_limits[3]), (255, 255, 0), 1)

        x -= margin
        w += margin * 2
        y -= margin
        h += margin * 2

        # Write on image
        cv2.putText(image, str(index), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 2, text_color)
        cv2.rectangle(image, (x, y), (x + w, y + h), graph_color, 1)

        if target:
            cv2.line(image, (x + w / 2, y), (x + w / 2, y + h), graph_color, 1)
            cv2.line(image, (x, y + h / 2), (x + w, y + h / 2), graph_color, 1)

        if fill:
            cv2.drawContours(image, [cnt], 0, graph_color, -1)

    out = cv2.imread(support_file) if support_file else copy(img_original)
    while True:
        img = cv2.cvtColor(img_original, cv2.COLOR_BGR2GRAY)

        # Crop image on nests
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

        if contour_limits[0] > len(contours):
            if debug:
                print('[Skip!] Contour length (%i) not in range !' % (len(contours)))

            mint, maxt = threshold_limits
            mint -= 15
            #mint += 4
            if mint <= 10:
                break

            threshold_limits = (mint, maxt)
            #print(threshold_limits)
            continue

            break

        if len(contours) >= contour_limits[1]:
            if debug:
                print('[Skip!] Contour length (%i) not in range, try with another thresholds: %s' % (len(contours), str(threshold_limits)))
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

            #_x, _y, _width, _heigth = (zone_limits[0], zone_limits[2]), (zone_limits[1], zone_limits[3])
            _xmin, _xmax, _ymin, _ymax = zone_limits
            if not _xmin < x + IMAGE_SUBSTRACT_WIDTH < _xmax or not _ymin < y < _ymax:
                skip("Not in nest zone !")
                continue

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

            if not (carea_limits[0] <= carea <= carea_limits[1]):
                skip('Contour area (%i) not in range !' % (carea))
                continue

            position = (x + IMAGE_SUBSTRACT_WIDTH / 2 + w / 2, y + h / 2)

            if verbose:
                print('[Found] %02i, Pos: %s, Size: %i, %i, approx poly length: %i, aDist:%i, contour area:%i' % (index, position, h, w, len(approx), adist, carea))
                if mark:
                    draw_debug(imgmark)

            colors = (
                (0, 0, 255),
                (255, 0, 0),
                (0, 255, 0),
            )

            cnt = cnt + (IMAGE_SUBSTRACT_WIDTH / 2, 0)
            draw_info(out, x + IMAGE_SUBSTRACT_WIDTH / 2, y, w, h, cnt, egg_count, margin=10, text_color=colors[egg_count % len(colors)], graph_color=colors[egg_count % len(colors)])

            eggs_found.append(position)
            egg_count += 1

        if debug:
            images = [ imgdebug, out, img_original ]
            if mark:
                images.insert(0, imgmark)

            alternate(images, img)

            cv2.destroyAllWindows()

        break

    if egg_count and export_file:
        cv2.imwrite(export_file, out)

    return eggs_found

def scan_image_with_config_file(config_file, *args, **kwargs):
    '''
    Scan image with config file parameter
    '''
    conf = load_config(config_file)
    kwargs.update(conf)
    return scan_image(*args, **kwargs)

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

    args = docopt(help, version='0.1')

    total = good = extra = missed = badnest = egg_count = 0
    for filename in args['<name>']:
        if args['--test-threshold']:
            test_threshold(filename)
        else:
            m = re.search('([0-9]+)_([0-9]+)_*((?:[-a-z0-9]*).*)\.(jpg|png)', filename)
            if not m:
                continue

            if not os.path.exists(os.path.realpath(filename)):
                print("File not found !")
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
                print("Open %s, must found %i egg(s)" % (filename, count), end=' ')
            else:
                print("Open %s\t" % (filename), end=' ')

            if flags:
                if flags in ('1', '2'):
                    nests = [int(flags)]
                else:
                    nests = [ int(nest) for nest in flags.split(',') ]
                    if args['--verbose']:
                        print('(nests: ' + ', '.join([ str(flag) for flag in nests ]) + ')', end=' ')

            if args['--debug'] or args['--verbose']:
                print()

            #egg_count, nest_index = scan_image(filename, debug=args['--debug'], verbose=args['--verbose'], **configuration)
            eggs_found = scan_image(filename, debug=args['--debug'], verbose=args['--verbose'], **configuration)

            egg_count = len(eggs_found)

            if egg_count != count:
                if egg_count > count:
                    extra += egg_count - count
                else:
                    missed += count - egg_count

                print('[Error] %i egg(s) found !' % (egg_count))
            else:
                for x, y in eggs_found:
                    nest_index = 1 if x >= IMAGE_SIZE[0] / 2 else 2
                    if nest_index in nests:
                        del nests[nests.index(nest_index)]
                    else:
                        badnest += 1

                if badnest:
                    print('[Error] Bad nest !')
                else:
                    print('[Ok]')
                    good += 1

    print("Result: %i%% (%i/%i)" % (round(100 / (float(total) / float(good)) if good > 0 else 0), good, total))
    print("- Egg found\t\t: %i" % egg_count)
    print("- Extra egg detected\t: %i" % extra)
    print("- Missed egg\t\t: %i" % missed)
    print("- Bad nest\t\t: %i" % badnest)

