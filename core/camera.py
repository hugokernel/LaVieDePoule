
from __future__ import print_function
from contextlib import contextmanager
from picamera import PiCamera
from fractions import Fraction

class Camera:

    '''
    Little class for abstract picamera functions
    '''

    photo_configuration = {
        'resolution': (1024, 768)
    }

    video_configuration = {
        'resolution': (640, 480)
    }

    callback_before = None
    callback_after = None

    photo_file = '/tmp/image.jpg'
    video_file = '/tmp/video.h264'

    def __init__(self, photo_configuration=photo_configuration, video_configuration=video_configuration):
        self.photo_configuration = photo_configuration
        self.video_configuration = video_configuration

    def include(func):
        def wrapper(self, *args, **kwargs):
            if self.callback_before:
                self.callback_before()
            status = func(self, *args, **kwargs)
            if self.callback_after:
                self.callback_after()
            return status
        return wrapper

    def setCallback(self, callback_before=None, callback_after=None):
        self.callback_before = callback_before
        self.callback_after = callback_after

    @contextmanager
    def attributes(self, photo_configuration, video_configuration):
        # Save context
        old_photo_configuration = self.photo_configuration
        self.photo_configuration = photo_configuration

        old_video_configuration = self.video_configuration
        self.video_configuration = video_configuration
        try:
            yield
        finally:
            self.photo_configuration = old_photo_configuration
            self.video_configuration = old_video_configuration

    @include
    def takePhoto(self, filename=photo_file, configuration=None):
        configuration = configuration if configuration else self.photo_configuration
        with PiCamera() as camera:
            for key, val in configuration.items():
                setattr(camera, key, val)

            # Give the camera a good long time to measure AWB
            # (you may wish to use fixed AWB instead)
            #time.sleep(10)

            camera.capture(filename)

        return True

    @include
    def takeVideo(self, duration, filename=video_file, configuration=None):
        configuration = configuration if configuration else self.video_configuration
        with PiCamera() as camera:
            for key, val in configuration.items():
                setattr(camera, key, val)
            camera.start_recording(filename)
            camera.wait_recording(duration)
            camera.stop_recording()

        return True

if __name__ == '__main__':
    c = Camera()
    c.setCallback(lambda: print('before'), lambda: print('after'))
    c.takePhoto()

