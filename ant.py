#! /usr/bin/env python
import os
import subprocess
import argparse
import cv2
import time
import random
import numpy as np
import datetime

adb_input = ['adb', 'shell', 'input']
adb_screen_stayon_cmd = ['adb', 'shell', 'svc', 'power', 'stayon', 'usb']
adb_back_cmd = adb_input + ['keyevent', '4']
farm_minute_candidates = [0,1,20,21,40,41]
farm_hour_candidates = [0,1,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
forest_hour_candidates = [0,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
forest_minute_candidates = [30,31]

def errorMsg(str):
    raise Exception('Error: {}'.format(str))

def randSleep():
    time.sleep(random.randint(30,90))

class Ant(object):
    def __init__(self, logdir, templatesdir):
        self.template_dict = {}
        self.logdir = logdir
        self.templatesdir  = templatesdir
        self.step = 0
        self.have_slept = False
        self.monitor = None
        self.crib_pos = None
        self.initTemplate()
        self.setScreenStayon()

        if self.logdir and not os.path.isdir(self.logdir):
            os.makedirs(self.logdir)

    def launchAlipay(self, retry):
        subprocess.run(['adb', 'shell',
            'am', 'start', '-S', 'com.eg.android.AlipayGphone/.AlipayLogin'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5+retry)
        for _ in range(5):
            self.scanMonitor(1)
            #check homepage
            if (self.getIconPos('ant_farm_icon_template', 0.9)
            and self.getIconPos('forest_icon_template', 0.9)):
                return
            #check update notification
            rc = self.getIconPos('update_template', 0.9)
            if rc:
                self.tap(rc, 'close-update-notification')
                continue
            #need to close prompt window first
            rc = self.getIconPos('close_donate_icon_template', 0.9)
            if not rc:
                rc = self.getIconPos('close_icon_template', 0.8)
            if rc:
                self.tap(rc, 'close-donate-window', 2)

    def tap(self, rc, msg='tap', time_sleep=5):
        adb_tap_cmd = adb_input + ['tap', '{} {}'.format(*rc)]
        print('TAP {} icon with {} + {}s sleep'.format(msg, adb_tap_cmd, time_sleep))
        subprocess.run(adb_tap_cmd)
        time.sleep(time_sleep)

    def swipe(self, start_x, start_y, end_x, end_y, duration):
        adb_swipe_cmd = adb_input + ['swipe', '{} {} {} {} {}'.format(start_x, start_y, end_x, end_y, duration)]
        subprocess.run(adb_swipe_cmd)

    def back(self, time_sleep=2):
        print("back and sleep {} seconds...".format(time_sleep))
        subprocess.run(adb_back_cmd)
        time.sleep(time_sleep)

    def setScreenStayon(self):
        print('preparing to keep screen on...')
        subprocess.run(adb_screen_stayon_cmd)

    def loadTemplate(self, icon):
        icon_path = os.path.join(self.templatesdir, icon)
        rc = cv2.imread(icon_path, 0)
        if rc is None:
            errorMsg('Template {} not exist.'.format(icon_path))
        template_key = '{}_template'.format(icon[:-4])
        self.template_dict[template_key] = rc

    def initTemplate(self):
        for icon in os.listdir(self.templatesdir):
            if not icon.endswith('.png'):
                continue
            self.loadTemplate(icon)

    def scanMonitor(self, time_sleep=2):
        time.sleep(time_sleep)
        try:
            bImg = subprocess.check_output(["adb", "shell", "screencap", "-p"])
            self.monitor = cv2.imdecode(np.frombuffer(bImg, np.uint8), 0)
            assert self.monitor is not None
            print('<======= scan farm {} times on {} ========>'.format(self.step, datetime.datetime.now()))
            self.step += 1
            self.height, self.width = self.monitor.shape[:2]
            if self.logdir:
                cv2.imwrite(os.path.join(self.logdir, 'gemfield_farm_{:06d}.png'.format(self.step)),
                        self.monitor)
        except Exception as e:
            errorMsg('Check the phone connection with computer. Detail: {}'.str(e))

    def getIconPos(self, template_name, threshold, is_left=False):
        return self.match(self.template_dict[template_name], threshold, template_name, is_left)

    def checkFarm(self):
        for i in range(5):
            self.scanMonitor(1)
            if self.getIconPos('crib_template', 0.9):
                return
            #suppose we are in homepage
            rc = self.getIconPos('ant_farm_icon_template', 0.9)
            if rc:
                self.tap(rc, 'enter-self-farm-page', 8)
            else:
                self.launchAlipay(i)
        errorMsg('Cannot locate your zhifubao app correctly.')

    def expelThief(self):
        for i in range(3):
            rc = self.getIconPos('thief_template', 0.8)
            if rc is None:
                print('No thief found...')
                break
            print('Found thief {}'.format(i))
            self.tap(rc, 'expel-the-thief')
            self.scanMonitor()

            rc = self.getIconPos('please_leave_me_alone_template', 0.8)
            if rc is None:
                print('No please_leave_me_alone_template found...')
                continue
            self.tap(rc, 'please_leave_me_alone_template')
            self.scanMonitor()


    def match(self, template, threshold, op, is_left=False, thresh=False):
        if thresh:
            cv2.imwrite('gemfield_{}.jpg'.format(self.step),
                cv2.adaptiveThreshold(self.monitor,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2))
        w, h = template.shape[::-1]
        res = cv2.matchTemplate(self.monitor, template, cv2.TM_CCOEFF_NORMED)
        res_max = res.max()
        print('MATCH {}: {}'.format(op, res_max))
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
        self.tap(rc, 'expel-the-robber')
        self.scanMonitor()

        rc = self.getIconPos('please_leave_me_alone_template', 0.8)
        if rc is None:
            print('No please_leave_me_alone_template found...')
            return
        self.tap(rc, 'please_leave_me_alone_template')
        self.scanMonitor()

    def feed(self):
        rc = self.getIconPos('indicator_template', 0.9)
        if rc is None:
            rc = self.getIconPos('double_indicator_template', 0.8)
        else:
            print('try to use accelerate card...')
            self.useAccelerateCard()
        #still has food left
        if rc:
            print('Still has food left...')
            return

        for _ in range(3):
            self.crib_pos = self.getIconPos('crib_template', 0.7)
            if self.crib_pos:
                break
            self.scanMonitor(3)

        if self.crib_pos is None:
            errorMsg('Make sure your screen of phone is on...')

        self.tap(self.crib_pos, 'feed-gemfield-chicken')

    def getMoreFood(self):
        now = datetime.datetime.now()
        if now.hour not in farm_hour_candidates:
            print('Will not get food since the forest time is coming...')
            return
        if now.minute not in farm_minute_candidates:
            print('Will not get food since just did earlier...')
            return

        rc = self.getIconPos('farm_friends_template', 0.8)
        if rc is None:
            print('No friends found')
            return
        self.have_slept = True
        self.tap(rc, 'farm-friends')
        for _ in range(50):
            self.scanMonitor(0.1)
            rc = self.getIconPos('farm_medal_template', 0.8)
            if not rc:
                break
            rc = self.getIconPos('farm_thief_flag_template', 0.8)
            if not rc:
                self.swipe(self.width // 2, self.height - 250, self.width // 2, self.height // 2, 600 )
                continue

            self.getFoodFromFriend(rc)
        self.back(1)

    def getFoodFromFriend(self, rc):
        self.tap(rc, 'enter-friend-farm-page')
        self.scanMonitor(5)

        rc = self.getIconPos('thief_template', 0.9)
        if rc:
            self.notifyFriend(rc)
        else:
            rc = self.getIconPos('robber_template', 0.9)
            if rc:
                self.notifyFriend(rc)
        self.back(1)

    def notifyFriend(self,rc):
        self.tap(rc, 'thief/robber-in-friend-farm')
        self.scanMonitor(1)
        rc = self.getIconPos('farm_message_template', 0.9)
        if not rc:
            return
        self.tap(rc, 'send-message-to-friend')

    def playFarm(self):
        self.checkFarm()
        self.expelThief()
        self.expelRobber()
        self.feed()
        self.getMoreFood()

    def checkForest(self):
        for i in range(5):
            self.scanMonitor(1)
            if self.getIconPos('back_from_forest_template', 0.9, is_left=True):
                return
            #suppose we are in homepage
            rc = self.getIconPos('forest_icon_template', 0.8)
            if rc:
                self.tap(rc, 'enter-self-forest-page', 8)
            else:
                self.launchAlipay(i)
        errorMsg('Cannot locate your zhifubao app correctly.')

    def findMoreFriends(self):
        for i in range(5):
            self.swipe(self.width // 2, self.height - 250, self.width // 2, self.height // 2, 400 )
            self.scanMonitor(0.5)
            rc = self.getIconPos('more_friends_template', 0.9)
            if not rc:
                continue
            self.tap(rc, 'check-more-friends')
            break

    def getOwnEnergy(self):
        for _ in range(10):
            self.scanMonitor(0.5)
            rc = self.getIconPos('energy_hand_day_template', 0.7)
            if rc:
                self.tap(np.subtract(rc, (50,70)), 'energy-hand')
            else:
                break

    #current screen
    def getEnergy(self):
        self.scanMonitor(0.1)
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
        self.tap(rc, 'enter-friend-forest-page')
        self.scanMonitor(3)
        for _ in range(6):
            rc = self.getIconPos('energy_hand_day_template', 0.8)
            rc2 = self.getIconPos('help_reap_template', 0.8)
            if not rc and not rc2:
                break
            if rc:
                self.tap(np.subtract(rc, (50,70)), 'energy-hand')
            if rc2:
                self.tap(np.subtract(rc2, (50,70)), 'helping-heart')

            self.scanMonitor(0.5)

        self.back(0)
        self.scanMonitor(0.1)

    def useAccelerateCard(self):
        rc = self.getIconPos('tools_icon_template', 0.8)
        if not rc:
            print("Impossible: but cannot find tools icon.")
            return

        self.tap(rc, 'click-tools-icon')
        self.scanMonitor(3)
        rc = self.getIconPos('accelerate_card_template', 0.8)
        if not rc:
            print("Impossible: but cannot find accelerate card icon.")
            return

        self.tap(rc, 'click-accelerate-card')
        self.scanMonitor()

        #1 has no card
        #2 already used
        #3 has card
        rc = self.getIconPos('use_accelerate_card_template', 0.9)
        if rc:
            self.tap(rc, 'click use_accelerate_card', 10)
        else:
            print("You cannot use accelerate card for now!")

        if self.backToFarm():
            return
        errorMsg('Could not back to Zhifubao homepage.')

    def playForest(self):
        self.checkForest()
        self.getOwnEnergy()
        self.findMoreFriends()
        for _ in range(40):
            self.getEnergy()
            if self.getIconPos('no_friends_template', 0.8):
                print('end of friends list')
                break
            self.swipe(self.width // 2, self.height - 250, self.width // 2, self.height // 2, 500)

        if self.backToHome():
            return
        errorMsg('Could not back to Zhifubao homepage.')

    def backToHome(self):
        for i in range(6):
            self.scanMonitor(0.5)
            #check app homepage
            rc = self.getIconPos('forest_icon_template', 0.9)
            if rc:
                print("Back at alipay homepage...")
                return True
            self.launchAlipay(i)

        return False

    def backToFarm(self):
        for i in range(6):
            self.scanMonitor(0.5)
            rc = self.getIconPos('crib_template', 0.9)
            if rc:
                print("We have back to ant farm applet homepage...")
                return True
            #check app homepage
            rc = self.getIconPos('ant_farm_icon_template', 0.9)
            if rc:
                self.tap(rc, 'enter ant farm applet')
            else:
                launchAlipay(i)
        return False

class Antforest(Ant):
    def play(self):
        while True:
            self.playForest()
            randSleep()

class Antfarm(Ant):
    def play(self):
        while True:
            self.playFarm()
            if self.have_slept:
                self.have_slept = False
                continue
            randSleep()

class Antdefault(Ant):
    def play(self):
        counter = 0
        while True:
            now = datetime.datetime.now()
            counter += 1
            self.playFarm()
            is_breakfast = now.hour == 7 and now.minute <= 35
            if is_breakfast or counter == 1:
                self.back()
                self.playForest()
                continue
            if self.have_slept:
                self.have_slept = False
                continue
            randSleep()

class Antall(Ant):
    def play(self):
        counter = 0
        while True:
            now = datetime.datetime.now()
            counter += 1
            self.playFarm()
            is_breakfast = now.hour == 7 and now.minute <= 35
            is_snacks = now.hour in forest_hour_candidates and now.minute in forest_minute_candidates
            if is_breakfast or is_snacks or counter == 1:
                self.back()
                self.playForest()
                continue
            if self.have_slept:
                self.have_slept = False
                #back to homepage then reenter
                self.back()
                continue
            randSleep()

if __name__ == "__main__":
    MODE_MAP = {'default': Antdefault,
                'farm': Antfarm,
                'forest': Antforest,
                'all': Antall}
    parser = argparse.ArgumentParser()
    parser.add_argument('--logdir', default=None, type=str,
            help='dir to save screenshot logs')
    parser.add_argument('--mode', default='default', type=str,
            choices=MODE_MAP.keys(), help='4 running modes ("default" if unspecified)')
    parser.add_argument('--template', default='meizumax', type=str,
            help='dir for templates')
    args = parser.parse_args()

    ant = MODE_MAP[args.mode](args.logdir,
            '{}_template_icons'.format(args.template))
    ant.play()
