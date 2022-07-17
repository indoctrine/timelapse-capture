import cv2
import sys
import os
import time
import numpy
import imutils
from skimage.metrics import structural_similarity as compare_ssim

OS_PATH=os.path.join(os.getcwd(), "TestPuzzle")
FILE_PREFIX="test-puzzle"
EXTENSION=".jpg"
CAMERA_PORT=1
CAPTURE_DELAY=60
CAPTURE_HEIGHT=1920
CAPTURE_WIDTH=1080
FIRST_RUN=True

class TimelapseCam(cv2.VideoCapture):
    def __init__(self, cam_port, options, delay, cap_width=1920, cap_height=1080):
        if not cam_port or not options or not delay:
            print("Missing mandatory arguments in constructor!")
            sys.exit(1)
        cv2.VideoCapture.__init__(self, cam_port, options)
        self.set(cv2.CAP_PROP_FRAME_WIDTH, cap_width)
        self.set(cv2.CAP_PROP_FRAME_HEIGHT, cap_height)
        self.delay = delay

class Shot():
    def __init__(self, path, ext, file_name):
        self.previous = time.time()
        self.delta = 0
        self.prevcap = None
        self.cap = None
        self.index = 0
        self.file_name = file_name
        self.ext = ext
        self.path = path
    def test_path(self):
        '''Test if path is writeable'''
        return os.access(self.path, os.W_OK)
    def check_index(self, full_path):
        '''Check if index exists in the full path'''
        if os.path.exists(full_path):
            self.index += 1
            return False
        else:
            return True
    def make_unique_path(self):
        '''Create unique path to pick up where the previous run left off'''
        if self.test_path():
            while True:
                full_path = os.path.join(self.path, self.file_name + str(self.index) + self.ext)
                if self.check_index(full_path):
                    # OK to write to next index
                    return full_path
    def make_compare_path(self, offset=0):
        '''Create comparison path with offset'''
        if self.test_path():
            full_path = os.path.join(self.path, self.file_name + str(self.index - offset) + self.ext)
            if os.path.exists(full_path):
                return full_path
    def update_delta(self):
        '''Update delta between current time and previous time'''
        self.current = time.time()
        self.delta += self.current - self.previous
        self.previous = self.current
    def reset_delta(self):
        '''Reset the delta back to zero to begin another run'''
        self.delta = 0
    def convert_image(self, img):
        '''Convert image to greyscale'''
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    def compare_images(self):
        '''Compare images using SSIM algorithm to detect if user has left'''
        curr_img_grey = self.convert_image(self.cap)
        if self.prevcap is None:
            self.prevcap = cv2.imread(self.make_compare_path(1))
        prev_grey_img = self.convert_image(self.prevcap)
        (score, diff) = compare_ssim(curr_img_grey, prev_grey_img, full=True)
        print(f"Similarity score between image #{self.index} and image #{self.index - 1} is {round(score * 100)}%")
        self.check = False
        return score

img = Shot(path=OS_PATH, file_name=FILE_PREFIX, ext=EXTENSION)

while True:
    img.update_delta()

    if img.delta > CAPTURE_DELAY or FIRST_RUN:
        cam = TimelapseCam(cam_port=CAMERA_PORT, delay=CAPTURE_DELAY, options=cv2.CAP_DSHOW)
        img.cap = cam.read()[1]
        if img.cap.any():
            cv2.imwrite(img.make_unique_path(), img.cap)
            print(f"Capturing image #{img.index}...")
            img.reset_delta()
            img.check = True
        cam.release()
        FIRST_RUN = False

    print(f"{round(cam.delay - img.delta)} seconds until next run")
    if img.index > 0 and img.check == True:
        score = img.compare_images()
        if score > 0.94:
            print("User has left the table")
            break
        img.prevcap = img.cap
    time.sleep(cam.delay / 5)

if cam.read():
    cam.release()
