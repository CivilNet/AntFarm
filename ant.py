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
import platform
import datetime

current_platform = platform.system()
TMPLATES_DIR = 'template_icons'
screenshot_img = '{}/current_gemfield_farm.png'.format(tempfile.gettempdir())
adb_screenshot_cmd = 'adb exec-out screencap -p > {}'.format(screenshot_img)
adb_screen_stayon_cmd = 'adb shell svc power stayon usb'
adb_back_cmd = 'adb shell input keyevent 4'

def errorMsg(str):
    print('Error: {}'.format(str) )
    if current_platform == 'Linux':
        os.system('wall Error: {}'.format(str))
    sys.exit(1)

def warningMsg(str):
    print('Warning: {}'.format(str) )
    if current_platform == 'Linux':
        os.system('wall Warning: {}'.format(str))
    
def swipe(start_x, start_y, end_x, end_y, duration):
    adb_swipe_cmd = 'adb shell input swipe {} {} {} {} {}'.format(start_x, start_y, end_x, end_y, duration)
    os.system(adb_swipe_cmd)
    time.sleep(1)

def getRandomSleep():
    return random.randint(30,90)

class Ant(object):
    def __init__(self, logdir):
        self.template_dict = {}
        self.logdir = logdir
        self.step = 0
        self.monitor = None
        self.crib_pos = None
        self.initTemplate()
        self.setScreenStayon()

        if self.logdir and not os.path.isdir(self.logdir):
            os.makedirs(self.logdir)

    def setScreenStayon(self):
        print('preparing to keep screen on...')
        os.system(adb_screen_stayon_cmd)

    def loadTemplate(self, icon):
        icon_path = os.path.join(TMPLATES_DIR, icon)
        rc = cv2.imread(icon_path, 0)
        if rc is None:
            errorMsg('Template {} not exist.'.format(icon_path))
        template_key = '{}_template'.format(icon[:-4])
        self.template_dict[template_key] = rc

    def initTemplate(self):
        for icon in os.listdir(TMPLATES_DIR):
            if not icon.endswith('.png'):
                continue
            self.loadTemplate(icon)

    def scanMonitor(self):
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
        self.height, self.width = self.monitor.shape[:2]
        #delete the image
        os.remove(screenshot_img)

    def getIconPos(self, template_name, threshold, is_left=False):
        return self.match(self.template_dict[template_name], threshold, template_name, is_left)

    def checkFarm(self):
        for i in range(5):
            self.scanMonitor()
            #need to close prompt window first
            rc = self.getIconPos('close_donate_icon_template', 0.9)
            if not rc:
                rc = self.getIconPos('close_icon_template', 0.8)
            if rc:
                x,y = rc
                adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
                os.system(adb_tap_cmd)
                time.sleep(2)
                continue
            #check crib
            if self.getIconPos('crib_template', 0.8):
                return
            #suppose we are in homepage
            rc = self.getIconPos('ant_farm_icon_template', 0.9)
            if not rc:
                print(adb_back_cmd)
                os.system(adb_back_cmd)
                time.sleep(2)
                continue

            x,y = rc
            adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
            os.system(adb_tap_cmd)
            time.sleep(8)
        errorMsg('Cannot locate your zhifubao app correctly.')

    def expelThief(self):
        for i in range(3):
            rc = self.getIconPos('thief_template', 0.8)
            if rc is None:
                print('No thief found...')
                break
            print('Found thief {}'.format(i))
            x,y = rc
            adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
            warningMsg('preparing to expel the thief with {}...'.format(adb_tap_cmd))
            os.system(adb_tap_cmd)
            self.scanMonitor()

    def match(self, template, threshold, op, is_left=False, thresh=False):
        monitor = cv2.cvtColor(self.monitor, cv2.COLOR_BGR2GRAY)
        if thresh:
            monitor = cv2.adaptiveThreshold(monitor,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
            cv2.imwrite('gemfield_{}.jpg'.format(self.step),monitor)
        w, h = template.shape[::-1]
        res = cv2.matchTemplate(monitor, template, cv2.TM_CCOEFF_NORMED)
        res_max = res.max()
        print('{}: {}'.format(op, res_max))
        threshold = max(threshold, res_max)
        loc = np.where( res >= threshold)
        rc = None
        for pt in zip(*loc[::-1]):
            if is_left:
                rc = (pt[0] + w//10, pt[1] + h//2)
            else:
                rc = (pt[0] + w//2, pt[1] + h//2)
        return rc

    def expelRobber(self):
        rc = self.getIconPos('robber_template', 0.8)
        if rc is None:
            print('No robber found...')
            return
        print('Found robber...')
        x,y = rc
        adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
        warningMsg('preparing to expel the robber with {}...'.format(adb_tap_cmd))
        os.system(adb_tap_cmd)

    def feed(self):
        rc = self.getIconPos('indicator_template', 0.8)
        if rc is None:
            rc = self.getIconPos('double_indicator_template', 0.8)
        #still has food left
        if rc:
            print('Still has food left...')
            return
 
        for i in range(3):
            self.crib_pos = self.getIconPos('crib_template', 0.8)
            if self.crib_pos:
                break
            time.sleep(3)
            self.scanMonitor()

        if self.crib_pos is None:
            errorMsg('Make sure your screen of phone is on...')

        x,y = self.crib_pos
        adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
        warningMsg('preparing to feed gemfield chicken with {}...'.format(adb_tap_cmd))
        os.system(adb_tap_cmd)

    def backhome(self):
        print(adb_back_cmd)
        os.system(adb_back_cmd)
        time.sleep(2)

    def playFarm(self):
        self.checkFarm()
        self.expelThief()
        self.expelRobber()
        self.feed()

    def checkForest(self):
        for i in range(5):
            self.scanMonitor()
            if self.getIconPos('back_from_forest_template', 0.9, is_left=True):
                return
            #suppose we are in homepage
            rc = self.getIconPos('forest_icon_template', 0.9)
            if not rc:
                print(adb_back_cmd)
                os.system(adb_back_cmd)
                time.sleep(2)
                continue

            x,y = rc
            adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
                
            os.system(adb_tap_cmd)
            time.sleep(8)
            
        errorMsg('Cannot locate your zhifubao app correctly.')

    def findMoreFriends(self):
        for i in range(3):
            swipe(self.width // 2, self.height - 10, self.width // 2, self.height // 2, 400 )
            self.scanMonitor()
            rc = self.getIconPos('more_friends_template', 0.9)
            if not rc:
                continue
            x,y = rc
            adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
            print(adb_tap_cmd)
            os.system(adb_tap_cmd)
            time.sleep(5)
            break

    #current screen
    def getEnergy(self):
        self.scanMonitor()
        for i in range(10):
            rc = self.getIconPos('forest_energy_template', 0.9)
            if not rc:
                break
            x,y = rc
            self.getEnergyFromFriend(x,y)

    def getEnergyFromFriend(self, x, y):
        adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
        print(adb_tap_cmd)
        #enter this friend page
        os.system(adb_tap_cmd)
        time.sleep(2)
        self.scanMonitor()
        for i in range(6):
            rc = self.getIconPos('energy_hand_day_template', 0.9)
            if rc is None:
                rc = self.getIconPos('energy_hand_night_template', 0.9)
            if not rc:
                break
            x,y = rc
            adb_tap_cmd = 'adb shell input tap {} {}'.format(x, y - 60)
            print(adb_tap_cmd)
            os.system(adb_tap_cmd)
            self.scanMonitor()
        #back
        print(adb_back_cmd)
        os.system(adb_back_cmd)
        time.sleep(2)
        self.scanMonitor()

    def playForest(self):
        self.checkForest()
        self.findMoreFriends()
        count = 0
        for i in range(30):
            self.getEnergy()
            if self.getIconPos('no_friends_template', 0.8):
                print('end of friends list')
                count += 1
            if count >= 2:
                break
            swipe(self.width // 2, self.height - 10, self.width // 2, self.height // 2, 500)

        #back
        for i in range(5):
            print(adb_back_cmd)
            os.system(adb_back_cmd)
            time.sleep(3)
            self.scanMonitor()
            rc = self.getIconPos('forest_icon_template', 0.9)
            if rc:
                return
        errorMsg('Could not back to Zhifubao homepage.')

class Antforest(Ant):
    def play(self):
        while True:
            self.playForest()
            time.sleep(getRandomSleep())

class Antfarm(Ant):
    def play(self):
        while True:
            self.playFarm()
            time.sleep(getRandomSleep())

class Antdefault(Ant):
    def play(self):
        counter = 0
        while True:
            now = datetime.datetime.now()
            counter += 1
            self.playFarm()
            is_breakfast = now.hour == 7 and now.minute <= 35
            if is_breakfast or counter == 1:
                self.backhome()
                self.playForest()
                continue
            time.sleep(getRandomSleep())

class Antall(Ant):
    def play(self):
        counter = 0
        while True:
            now = datetime.datetime.now()
            counter += 1
            self.playFarm()
            is_breakfast = now.hour == 7 and now.minute <= 35
            is_snacks = (now.hour <2 or now.hour >= 6) and now.minute <= 2
            if is_breakfast or is_snacks or counter == 1:
                self.backhome()
                self.playForest()
                continue
            time.sleep(getRandomSleep())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--logdir', default=None, type=str, help='You should specify the log dir.')
    parser.add_argument('--mode', default='default', type=str, help='There have 4 modes: forest|farm|default|all')
    args = parser.parse_args()
    if args.mode not in ['default','farm','forest','all']:
        errorMsg('Usage: {} --mode <forest|farm|default|all>'.format(sys.argv[0]))

    ant = eval('Ant{}'.format(args.mode))(args.logdir)
    ant.play()