
from __future__ import print_function
from picamera import PiCamera

class Camera:

    '''
    Little class for abstract picamera functions
    '''

    resolution = (1024, 768)

    callback_before = None
    callback_after = None

    photo_file = '/tmp/image.jpg'
    video_file = '/tmp/video.jpg'

    def include(func):
        def wrapper(self, **kwargs):
            if self.callback_before:
                self.callback_before()
            status = func(self, **kwargs)
            if self.callback_after:
                self.callback_after()
            return status
        return wrapper

    def setCallback(self, callback_before=None, callback_after=None):
        self.callback_before = callback_before
        self.callback_after = callback_after

    @include
    def takePhoto(self, resolution=resolution, low_light=False, filename=photo_file):
        with PiCamera() as camera:
            camera.resolution = resolution

            if low_light:
                camera.framerate = Fraction(1, 6)
                camera.shutter_speed = 6000000
                #camera.exposure_mode = 'off'
                camera.ISO = 800
                # Give the camera a good long time to measure AWB
                # (you may wish to use fixed AWB instead)
                time.sleep(10)

            camera.capture(filename)

        return True

    @include
    def takeVideo(self, duration, resolution=resolution, filename=video_file):
        with PiCamera() as camera:
            camera.resolution = resolution
            camera.start_recording(filename)
            camera.wait_recording(duration)
            camera.stop_recording()

        return True

if __name__ == '__main__':
    c = Camera()
    c.setCallback(lambda: print('before'), lambda: print('after'))
    c.takePhoto()

