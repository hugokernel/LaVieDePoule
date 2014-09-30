from SimpleCV import Image, ColorMap, Color
import time

img = Image('with.jpeg')
#img = Image('lenna.png')
#c = img.findCorners()

OEUF = (0x76, 0x78, 0x77)

#clr = ColorCurve([[0,0], [100, 120], [180, 230], [255, 255]])
#img.applyIntensityCurve(clr)
'''
bina = img.binarize()
dilate = img.dilate(10)
#c = img.findBlobs()
'''

peaks = img.huePeaks()
print peaks
peak_one = peaks[0][0]
print peak_one

hue = img.hueDistance(peak_one)
hue.show()

#c.colorDistance(Color.YELLOW)

#cm = ColorMap(color = Color.RED, startmap = min(blobs.area()) , endmap = max(blobs.area()))
#for b in blobs:
#    b.draw(cm[b.area()])


#print c.show(autocolor=True)
#print img.show()
#print dilate.show()

time.sleep(20)

