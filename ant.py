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
minute_candidates = [0,1,20,21,40,41]
hour_candidates = [0,1,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]

def errorMsg(str):
    print('Error: {}'.format(str) )
    if current_platform == 'Linux':
        os.system('wall Error: {}'.format(str))
    sys.exit(1)

def warningMsg(str):
    print('Warning: {}'.format(str) )
    return
    if current_platform == 'Linux':
        os.system('wall Warning: {}'.format(str))
    
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

    def tap(self, rc, msg='tap'):
        x,y = rc
        adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
        print('preparing to {} with {}...'.format(msg, adb_tap_cmd))
        os.system(adb_tap_cmd)

    def swipe(self, start_x, start_y, end_x, end_y, duration):
        adb_swipe_cmd = 'adb shell input swipe {} {} {} {} {}'.format(start_x, start_y, end_x, end_y, duration)
        os.system(adb_swipe_cmd)
        time.sleep(1)

    def back(self, time_sleep=2):
        os.system(adb_back_cmd)
        time.sleep(time_sleep)

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

    def scanMonitor(self, time_sleep=0):
        time.sleep(time_sleep)
        adb_rc = 1
        try:
            adb_rc = os.system(adb_screenshot_cmd)
        except Exception as e:
            errorMsg('Check the phone connection with computer. Detail: {}'.str(e))

        if adb_rc != 0:
            errorMsg('Check the phone connection with computer.')

        if not os.path.isfile(screenshot_img):
            errorMsg('Could not take a screenshot from adb command. Check your phone connection with computer.')

        self.step += 1
        if self.logdir:
            shutil.copyfile(screenshot_img, os.path.join(self.logdir, 'gemfield_farm_{:06d}.png'.format(self.step)))

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
                self.tap(rc)
                time.sleep(2)
                continue
            #check crib
            if self.getIconPos('crib_template', 0.7):
                return
            #suppose we are in homepage
            rc = self.getIconPos('ant_farm_icon_template', 0.9)
            if not rc:
                self.back(2)
                continue

            self.tap(rc)
            time.sleep(8)
        errorMsg('Cannot locate your zhifubao app correctly.')

    def expelThief(self):
        for i in range(3):
            rc = self.getIconPos('thief_template', 0.8)
            if rc is None:
                print('No thief found...')
                break
            print('Found thief {}'.format(i))
            self.tap(rc, 'expel the thief')
            self.scanMonitor(2)

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
        self.tap(rc, 'expel the robber')
        
    def feed(self):
        rc = self.getIconPos('indicator_template', 0.8)
        if rc is None:
            rc = self.getIconPos('double_indicator_template', 0.8)
        #still has food left
        if rc:
            print('Still has food left...')
            return
 
        for i in range(3):
            self.crib_pos = self.getIconPos('crib_template', 0.7)
            if self.crib_pos:
                break
            self.scanMonitor(3)

        if self.crib_pos is None:
            errorMsg('Make sure your screen of phone is on...')

        self.tap(self.crib_pos, 'feed gemfield chicken')

    def getMoreFood(self):
        now = datetime.datetime.now()
        if now.hour not in hour_candidates:
            print('Will not get food since the forest time is coming...')
            return
        if now.minute not in minute_candidates:
            print('Will not get food since just did earlier...')
            return

        rc = self.getIconPos('farm_friends_template', 0.8)
        if rc is None:
            print('No friends found')
            return
        self.tap(rc, 'click friend icon')
        for _ in range(50):
            self.scanMonitor(2)
            rc = self.getIconPos('farm_medal_template', 0.8)
            if not rc:
                break
            rc = self.getIconPos('farm_thief_flag_template', 0.8)
            if not rc:
                self.swipe(self.width // 2, self.height - 10, self.width // 2, self.height // 1.5, 600 )
                continue

            self.getFoodFromFriend(rc)
        self.back(1)

    def getFoodFromFriend(self, rc):
        self.tap(rc, 'enter friend page')
        time.sleep(3)
        self.scanMonitor()

        rc = self.getIconPos('thief_template', 0.9)
        if rc:
            self.notifyFriend(rc)
        else:
            rc = self.getIconPos('robber_template', 0.9)
            if rc:
                self.notifyFriend(rc)
        self.back(1)

    def notifyFriend(self,rc):
        self.tap(rc, 'click the thief/robber')
        self.scanMonitor(1)
        rc = self.getIconPos('farm_message_template', 0.9)
        if not rc:
            return
        self.tap(rc, 'send message to friend')

    def playFarm(self):
        self.checkFarm()
        self.expelThief()
        self.expelRobber()
        self.feed()
        self.getMoreFood()

    def checkForest(self):
        for i in range(5):
            self.scanMonitor()
            if self.getIconPos('back_from_forest_template', 0.9, is_left=True):
                return
            #suppose we are in homepage
            rc = self.getIconPos('forest_icon_template', 0.9)
            if not rc:
                self.back(2)
                continue

            self.tap(rc)
            time.sleep(8)
            
        errorMsg('Cannot locate your zhifubao app correctly.')

    def findMoreFriends(self):
        for i in range(3):
            self.swipe(self.width // 2, self.height - 10, self.width // 2, self.height // 2, 400 )
            self.scanMonitor()
            rc = self.getIconPos('more_friends_template', 0.9)
            if not rc:
                continue
            self.tap(rc)
            
            time.sleep(5)
            break

    #current screen
    def getEnergy(self):
        self.scanMonitor()
        for _ in range(10):
            rc = self.getIconPos('forest_energy_template', 0.9)
            if not rc:
                break
            self.reapOrHelp(rc)

        for _ in range(10):
            rc = self.getIconPos('forest_reap_template', 0.9)
            if not rc:
                break
            self.reapOrHelp(rc)

    def reapOrHelp(self, rc):
        self.tap(rc)
        time.sleep(3)
        self.scanMonitor()
        for _ in range(6):
            rc = self.getIconPos('energy_hand_day_template', 0.9)
            rc2 = self.getIconPos('help_reap_template', 0.9)
            if not rc and not rc2:
                break
            if rc:
                x,y = rc
                rc = (x-50, y-70)
                self.tap(rc)
            if rc2:
                x,y = rc2
                rc = (x-50, y-70)
                self.tap(rc)

            self.scanMonitor(2)

        self.back(0)
        self.scanMonitor(3)

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
            self.swipe(self.width // 2, self.height - 10, self.width // 2, self.height // 2, 500)

        #back
        for i in range(5):
            self.back(0)
            self.scanMonitor(3)
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
                self.back(2)
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
                self.back(2)
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
