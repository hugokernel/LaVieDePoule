
from __future__ import print_function
from contextlib import contextmanager
from picamera import PiCamera
from fractions import Fraction

class Camera:

    '''
    Little class for abstract picamera functions
    '''

    configuration = {
        'resolution': (1024, 768)
    }

    callback_before = None
    callback_after = None

    photo_file = '/tmp/image.jpg'
    video_file = '/tmp/video.jpg'

    def __init__(self, configuration=configuration):
        self.configuration = configuration

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

    @contextmanager
    def attributes(self, configuration):
        # Save context
        old_configuration = self.configuration
        self.configuration = configuration
        try:
            yield
        finally:
            self.configuration = old_configuration

    @include
    def takePhoto(self, filename=photo_file, configuration=None):
        configuration = configuration if configuration else self.configuration
        with PiCamera() as camera:
            for key, val in configuration.items():
                setattr(camera, key, val)

            # Give the camera a good long time to measure AWB
            # (you may wish to use fixed AWB instead)
            #time.sleep(10)

            camera.capture(filename)

        return True

    @include
    def takeVideo(self, duration, resolution=configuration['resolution'], filename=video_file):
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

