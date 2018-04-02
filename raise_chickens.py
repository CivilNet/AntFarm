import os
import sys
import shutil
import argparse
import cv2
import time
import random
import numpy as np
import time
import tempfile

templates_dir = 'templates'
screenshot_img = '{}/current_gemfield_farm.png'.format(tempfile.gettempdir())
adb_screenshot_cmd = 'adb exec-out screencap -p > {}'.format(screenshot_img)
adb_lighter_cmd = 'adb shell input keyevent 221'
adb_darker_cmd = 'adb shell input keyevent 220'
adb_screen_stayon_cmd = 'adb shell svc power stayon usb'

def errorMsg(str):
    print('Error: {}'.format(str) )
    os.system('wall Error: {}'.format(str))
    sys.exit(1)

def warningMsg(str):
    print('Warning: {}'.format(str) )
    os.system('wall Warning: {}'.format(str))
    

def swipe(start_x, start_y, end_x, end_y, duration):
    adb_swipe_cmd = 'adb shell input swipe {} {} {} {} {}'.format(start_x, start_y, end_x, end_y, duration)
    os.system(adb_swipe_cmd)

def getRandomSleep():
    #30 ~ 120 s
    return random.randint(30,90)

def loadTemplate(template_img):
    rc = cv2.imread(template_img, 0)
    if rc is None:
        errorMsg('Template {} not exist.'.format(template_img))
    return rc

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
        self.setScreenStayon()

        if self.logdir and not os.path.isdir(self.logdir):
            os.makedirs(self.logdir)

    def initTemplate(self):
        self.crib_template = loadTemplate(os.path.join(self.templates_dir, 'crib.png') )
        self.indicator_template = loadTemplate(os.path.join(self.templates_dir, 'indicator.png') )
        self.double_indicator_template = loadTemplate(os.path.join(self.templates_dir, 'double_indicator.png') )
        self.thief_template = loadTemplate(os.path.join(self.templates_dir, 'thief.png') )
        self.robber_template = loadTemplate(os.path.join(self.templates_dir, 'robber.png') )

    def scanFarm(self):
        adb_rc = 1
        try:
            adb_rc = os.system(adb_screenshot_cmd)
        except Exception as e:
            errorMsg('Check the phone connection with computer. Detail: {}'.str(e))

        if adb_rc != 0:
            errorMsg('Check the phone connection with computer.')

        if not os.path.isfile(screenshot_img):
            errorMsg('Could not take a screenshot from adb command. Check your phone connection with computer.')

        if self.logdir:
            shutil.copyfile(screenshot_img, os.path.join(self.logdir, 'gemfield_farm_{:06d}.png'.format(self.step)))

        self.step += 1
        print('<========================== scan farm {} times ==========================>'.format(self.step))
        self.monitor = cv2.imread(screenshot_img)
        self.resolution = self.monitor.shape[:2]
        #delete the image
        os.remove(screenshot_img)

    def setScreenStayon(self):
        print('preparing to keep screen on...')
        # os.system(adb_lighter_cmd)
        # os.system(adb_darker_cmd)
        os.system(adb_screen_stayon_cmd)

    def getCribPos(self):
        rc = self.match(self.crib_template, 0.8)
        return rc

    def getIndicatorPos(self):
        rc = self.match(self.indicator_template, 0.8)
        if rc is None:
            rc = self.match(self.double_indicator_template, 0.8)

        return rc

    def getThiefPos(self):
        return self.match(self.thief_template, 0.8)

    def getRobberPos(self):
        return self.match(self.robber_template, 0.8)
        
    def feed(self):
        rc = self.getIndicatorPos()
        #still has food left
        if rc:
            print('Still has food left...')
            return
 
        if self.crib_pos is None:
            self.crib_pos = self.getCribPos()

        if self.crib_pos is None:
            errorMsg('Make sure your screen of phone is on...')

        x,y = self.crib_pos
        adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
        print('preparing to feed gemfield chicken with {}...'.format(adb_tap_cmd))
        os.system(adb_tap_cmd)

    def expelThief(self):
        for i in range(3):
            rc = self.getThiefPos()
            if rc is None:
                print('No thief found...')
                break
            print('Found thief {}'.format(i))
            x,y = rc
            adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
            warningMsg('preparing to expel the thief with {}...'.format(adb_tap_cmd))
            os.system(adb_tap_cmd)
            self.scanFarm()

    def expelRobber(self):
        rc = self.getRobberPos()
        if rc is None:
            print('No robber found...')
            return
        print('Found robber...')
        x,y = rc
        adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
        warningMsg('preparing to expel the robber with {}...'.format(adb_tap_cmd))
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
        self.expelRobber()
        self.feed()
        time.sleep(getRandomSleep())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--logdir', default=None, type=str, help='You should specify the log dir.')
    args = parser.parse_args()
    
    chicken = AntFarm(args.logdir)
    while True:
        chicken.play()