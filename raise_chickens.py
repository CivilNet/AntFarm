import os
import glob
import shutil
import argparse
import cv2
import time
import random
import numpy as np
import time

templates_dir = 'templates'
screenshot_img = 'current_gemfield_farm.png'
adb_screenshot_cmd = 'adb exec-out screencap -p > {}'.format(screenshot_img)

def swipe(start_x, start_y, end_x, end_y, duration):
    adb_swipe_cmd = 'adb shell input swipe {} {} {} {} {}'.format(start_x, start_y, end_x, end_y, duration)
    os.system(adb_swipe_cmd)

def getRandomSleep():
    #30 ~ 120 s
    return random.randint(30,90)

class AntFarm(object):
    def __init__(self, logdir=None):
        self.logdir = logdir
        self.bb_size = [300, 300]
        self.step = 0
        self.monitor = None
        self.templates_dir = templates_dir
        #init later
        self.crib_pos = None

        self.initTemplate()

        if self.logdir and not os.path.isdir(self.logdir):
            os.makedirs(self.logdir)

    def initTemplate(self):
        self.crib_template = cv2.imread(os.path.join(self.templates_dir, 'crib.png'), 0)
        self.indicator_template = cv2.imread(os.path.join(self.templates_dir, 'indicator.png'), 0)
        self.thief_template = cv2.imread(os.path.join(self.templates_dir, 'thief.png'), 0)

    def scanFarm(self):
        os.system(adb_screenshot_cmd)
        if not os.path.isfile(screenshot_img):
            raise Exception('Could not take a screenshot from adb command. Check your phone connection with computer.')

        if self.logdir:
            shutil.copyfile(screenshot_img, os.path.join(self.logdir, 'gemfield_farm_{:06d}.png'.format(self.step)))

        self.step += 1
        print('<========================== scan farm {} times ==========================>'.format(self.step))
        self.monitor = cv2.imread(screenshot_img)
        self.resolution = self.monitor.shape[:2]

    def getCribPos(self):
        rc = self.match(self.crib_template, 0.8)
        return rc

    def getIndicatorPos(self):
        return self.match(self.indicator_template, 0.8)

    def getThiefPos(self):
        return self.match(self.thief_template, 0.8)
        
    def feed(self, force=False):
        rc = self.getIndicatorPos()
        #still has food left
        if rc:
            print('Still has food left...')
            if not force:
                return
            print('But will force feed to wake up phone...')
        if self.crib_pos is None:
            self.crib_pos = self.getCribPos()

        x,y = self.crib_pos
        adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
        print('preparing feed gemfield chicken...')
        os.system(adb_tap_cmd)

    def expelThief(self):
        #default left thief
        for i in range(3):
            rc = self.getThiefPos()
            if rc is None:
                print('No thief found...')
                break
            print('Found thief {}'.format(i))
            x,y = rc
            adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
            os.system(adb_tap_cmd)


    def match(self, template, threshold):
        monitor = cv2.cvtColor(self.monitor, cv2.COLOR_BGR2GRAY)
        w, h = template.shape[::-1]
        res = cv2.matchTemplate(monitor, template, cv2.TM_CCOEFF_NORMED)

        print('Max probability: {}'.format(res.max()))
        threshold = max(threshold, res.max() )

        loc = np.where( res >= threshold)

        rc = None
        for pt in zip(*loc[::-1]):
            rc = (pt[0] + w//2, pt[1] + h//2)
            #cv2.rectangle(self.monitor, pt, (pt[0] + w, pt[1] + h), (0,0,255), 2)
        #cv2.imwrite('res.png', self.monitor)
        return rc

    def play(self):
        self.scanFarm()
        self.expelThief()
        self.feed(self.step % 15 == 2)
        time.sleep(getRandomSleep())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--logdir', default=None, type=str, help='You should specify the log dir.')
    args = parser.parse_args()
    
    chicken = AntFarm(args.logdir)
    while True:
        chicken.play()