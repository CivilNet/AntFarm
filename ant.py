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
import json
import urllib.request
from config import *

ENABLE_ALIYUN_OSS=True
#pip install oss2
try:
    import oss2
except:
    print("Note: you have no oss2 installed, disable notification function")
    ENABLE_ALIYUN_OSS=False

current_platform = platform.system()
TMPLATES_DIR = '{}_template_icons'.format('not_exist')
screenshot_img = '{}/current_gemfield_farm.png'.format(tempfile.gettempdir())
adb_screenshot_cmd = 'adb exec-out screencap -p > {}'.format(screenshot_img)
adb_screen_stayon_cmd = 'adb shell svc power stayon usb'
adb_back_cmd = 'adb shell input keyevent 4'
farm_minute_candidates = [0,1,20,21,30,40,41]
farm_hour_candidates = [0,1,2,3,4,5,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
forest_hour_candidates = [0,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
forest_minute_candidates = [30,31]

def upload2oss(local_path):
    oss_url = None
    if not ENABLE_ALIYUN_OSS:
        return oss_url

    oss_path = '{}.png'.format(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    try:
        auth = oss2.Auth(OSS_KEY_ID, OSS_KEY_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET)
        bucket.put_object_from_file(oss_path, local_path)
        oss_url = '{}/{}'.format(OSS_URL_TEMPLATE, oss_path)
    except Exception as e:
        print("Error: ",str(e))
    return oss_url

def upload2dingding(msg, local_path=screenshot_img):
    if not DINGDING_WEBHOOK:
        return

    oss_url = upload2oss(local_path)
    if oss_url is None:
        oss_url = "404"

    my_data = {
        "msgtype": "markdown",
        "markdown": {
            "title": "CivilNet/AntFarm ERROR",
            "text": "### gemfield看看你的鸡:  \n >{} \n> ![screenshot]({})".format(msg, oss_url)
        },
        "at": {"isAtAll": True} 
    }

    header = {
        "Content-Type": "application/json",
        "Charset": "UTF-8"
    }
    try:
        send_data = json.dumps(my_data).encode("utf-8")
        request = urllib.request.Request(url=DINGDING_WEBHOOK, data=send_data, headers=header)

        response = urllib.request.urlopen(request)
        print(response.read())
    except Exception as e:
        print("Error: ",str(e))

def errorMsg(msg):
    print('Error: {}'.format(msg) )
    upload2dingding(msg)
    raise Exception("critical error that I have to shutdown...")

def warningMsg(msg):
    print('Warning: {}'.format(msg) )
    upload2dingding(msg)
    
def getRandomSleep():
    return random.randint(30,90)

class Ant(object):
    def __init__(self, logdir):
        self.template_dict = {}
        self.logdir = logdir
        self.step = 0
        self.have_slept = False
        self.monitor = None
        self.crib_pos = None
        self.initTemplate()
        self.setScreenStayon()

        if self.logdir and not os.path.isdir(self.logdir):
            os.makedirs(self.logdir)

    def tap(self, rc, msg='tap'):
        x,y = rc
        adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
        print('TAP {} icon with {}...'.format(msg, adb_tap_cmd))
        os.system(adb_tap_cmd)

    def swipe(self, start_x, start_y, end_x, end_y, duration):
        adb_swipe_cmd = 'adb shell input swipe {} {} {} {} {}'.format(start_x, start_y, end_x, end_y, duration)
        os.system(adb_swipe_cmd)

    def back(self, time_sleep=2):
        print("back and sleep {} seconds...".format(time_sleep))
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

        print('<======= scan farm {} times on {} ========>'.format(self.step, datetime.datetime.now()))
        self.monitor = cv2.imread(screenshot_img)
        self.height, self.width = self.monitor.shape[:2]
        #delete the image
        #print(screenshot_img)
        #os.remove(screenshot_img)

    def getIconPos(self, template_name, threshold, is_left=False):
        return self.match(self.template_dict[template_name], threshold, template_name, is_left)

    def checkFarm(self):
        for _ in range(5000):
            self.scanMonitor(1)
            #check homepage
            rc = self.getIconPos('zhifubao_icon_template', 0.9)
            if rc:
                self.tap(rc, 'launch zhifubao app')
                time.sleep(5)
                continue
            #check update notification
            rc = self.getIconPos('update_template', 0.9)
            if rc:
                self.tap(rc, 'close-update-notification')
                time.sleep(2)
                continue
            #need to close prompt window first
            rc = self.getIconPos('close_donate_icon_template', 0.9)
            if not rc:
                rc = self.getIconPos('close_icon_template', 0.8)
            if rc:
                self.tap(rc, 'close-donate-window')
                time.sleep(2)
                continue
            #check crib
            if self.getIconPos('crib_template', 0.9):
                return
            #suppose we are in homepage
            rc = self.getIconPos('ant_farm_icon_template', 0.9)
            if not rc:
                self.back(2)
                continue

            self.tap(rc, 'enter-self-farm-page')
            time.sleep(8)
        errorMsg('Cannot locate your zhifubao app correctly.')

    def expelThief(self):
        for i in range(3):
            rc = self.getIconPos('thief_template', 0.8)
            if rc is None:
                print('No thief found...')
                break
            print('Found thief {}'.format(i))
            self.tap(rc, 'expel-the-thief')
            self.scanMonitor(2)

            rc = self.getIconPos('please_leave_me_alone_template', 0.8)
            if rc is None:
                print('No please_leave_me_alone_template found...')
                continue
            self.tap(rc, 'please_leave_me_alone_template')
            self.scanMonitor(2)
            

    def match(self, template, threshold, op, is_left=False, thresh=False):
        monitor = cv2.cvtColor(self.monitor, cv2.COLOR_BGR2GRAY)
        if thresh:
            monitor = cv2.adaptiveThreshold(monitor,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
            cv2.imwrite('gemfield_{}.jpg'.format(self.step),monitor)
        w, h = template.shape[::-1]
        res = cv2.matchTemplate(monitor, template, cv2.TM_CCOEFF_NORMED)
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
        self.scanMonitor(2)

        rc = self.getIconPos('please_leave_me_alone_template', 0.8)
        if rc is None:
            print('No please_leave_me_alone_template found...')
            return
        self.tap(rc, 'please_leave_me_alone_template')
        self.scanMonitor(2)
        
    def feed(self):
        rc2 = self.getIconPos('double_indicator_template', 0.80)
        if rc2:
            print('Still using double hand to eat food...')
            return

        rc2 = self.getIconPos('small_double_indicator_template', 0.75)
        if rc2:
            print('Though has guest in home, still using double hand to eat food...')
            return 

        rc2 = self.getIconPos('small_double_indicator2_template', 0.75)
        if rc2:
            print('Though has guest in home, still using double hand to eat food...')
            return

        rc = self.getIconPos('indicator_template', 0.90)
        if rc:
            print('try to use accelerate card...')
            self.useAccelerateCard()
            return

        rc = self.getIconPos('indicator2_template', 0.82)
        if rc:
            print('try to use accelerate card by 2...')
            self.useAccelerateCard()
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
            print('Will not get food since it is not the right time...')
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
        time.sleep(4)
        for _ in range(50):
            self.scanMonitor(0.1)
            rc = self.getIconPos('farm_medal_template', 0.8)
            if not rc:
                break
            rc = self.getIconPos('farm_thief_flag_template', 0.8)
            if not rc:
                self.swipe(self.width // 2, self.height - 100, self.width // 2, self.height // 1.5, 600 )
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
        for _ in range(500):
            self.scanMonitor(1)
####
            #check homepage
            rc = self.getIconPos('zhifubao_icon_template', 0.9)
            if rc:
                self.tap(rc, 'launch zhifubao app')
                time.sleep(5)
                continue
            #check update notification
            rc = self.getIconPos('update_template', 0.9)
            if rc:
                self.tap(rc, 'close-update-notification')
                time.sleep(2)
                continue
            #need to close prompt window first
            rc = self.getIconPos('close_donate_icon_template', 0.9)
            if not rc:
                rc = self.getIconPos('close_icon_template', 0.8)
            if rc:
                self.tap(rc, 'close-donate-window')
                time.sleep(2)
                continue
####
            if self.getIconPos('back_from_forest_template', 0.9, is_left=True):
                return
            #suppose we are in homepage
            rc = self.getIconPos('forest_icon_template', 0.8)
            if not rc:
                self.back(2)
                continue

            self.tap(rc, 'enter-self-forest-page')
            time.sleep(8)
            
        errorMsg('Cannot locate your zhifubao app correctly.')

    def findMoreFriends(self):
        for i in range(5):
            self.swipe(self.width // 2, self.height - 100, self.width // 2, self.height // 2, 400 )
            self.scanMonitor(0.5)
            rc = self.getIconPos('more_friends_template', 0.9)
            if not rc:
                continue
            self.tap(rc, 'check-more-friends')
            time.sleep(4)
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

    def reapNotice(self):
        self.scanMonitor(0.5)
        rc = self.getIconPos('help_reap_notification_template', 0.8)
        if not rc:
            return
        self.tap(rc, 'help-reap-notification')

    def reapOrHelp(self, rc):
        self.tap(rc, 'enter-friend-forest-page')
        self.scanMonitor(3)
        for _ in range(6):
            rc = self.getIconPos('energy_hand_day_template', 0.8)
            rc2 = self.getIconPos('help_reap_template', 0.8)
            if not rc and not rc2:
                break
            if rc:
                x,y = rc
                rc = (x-50, y-70)
                self.tap(rc, 'energy-hand')
            if rc2:
                x,y = rc2
                rc2 = (x+40, y+40)
                self.tap(rc2, 'helping-heart')
                self.reapNotice()
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
        self.scanMonitor(2)

        #1 has no card
        #2 already used
        #3 has card
        rc = self.getIconPos('use_accelerate_card_template', 0.9)
        if rc:
            self.tap(rc, 'click use_accelerate_card')
            time.sleep(10)
        else:
            print("You cannot use accelerate card for now!")

        self.backToFarm()

    def playForest(self):
        self.checkForest()
        self.findMoreFriends()
        for _ in range(40):
            self.getEnergy()
            if self.getIconPos('no_friends_template', 0.8):
                print('end of friends list')
                break
            self.swipe(self.width // 2, self.height - 100, self.width // 2, self.height // 2, 500)

        if self.backToHome():
            return
        errorMsg('Could not back to Zhifubao homepage.')

    def backToHome(self):
        for _ in range(6):
            self.scanMonitor(0.5)
            #check app homepage
            rc = self.getIconPos('forest_icon_template', 0.9)
            if rc:
                print("We have back to alipay homepage...")
                return True

            #check android homepage
            rc = self.getIconPos('zhifubao_icon_template', 0.9)
            if rc:
                self.tap(rc, 'launch zhifubao app')
                time.sleep(5)
                continue
            #tap back
            self.back(1)

        return False

    def backToFarm(self):
        for _ in range(6):
            self.scanMonitor(0.5)
            rc = self.getIconPos('crib_template', 0.9)
            if rc:
                print("We have back to ant farm applet homepage...")
                return True
            #check app homepage
            rc = self.getIconPos('ant_farm_icon_template', 0.9)
            if rc:
                self.tap(rc, 'enter ant farm applet')
                time.sleep(5)
                continue

            #check android homepage
            rc = self.getIconPos('zhifubao_icon_template', 0.9)
            if rc:
                self.tap(rc, 'launch zhifubao app')
                time.sleep(5)
                continue
            #tap back
            self.back(1)
        return False

class Antforest(Ant):
    def play(self):
        while True:
            self.playForest()
            time.sleep(getRandomSleep())

class Antfarm(Ant):
    def play(self):
        while True:
            self.playFarm()
            if self.have_slept:
                self.have_slept = False
                continue
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
            if self.have_slept:
                self.have_slept = False
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
            is_snacks = now.hour in forest_hour_candidates and now.minute in forest_minute_candidates
            if is_breakfast or is_snacks or counter == 1:
                self.back(2)
                self.playForest()
                continue
            if self.have_slept:
                self.have_slept = False
                #back to homepage then reenter
                self.back(2)
                continue
            time.sleep(getRandomSleep())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--logdir', default=None, type=str, help='You should specify the log dir.')
    parser.add_argument('--mode', default='default', type=str, help='There have 4 modes: forest|farm|default|all')
    parser.add_argument('--template', default='meizumax', type=str, help='specify various mobile phone template dir')
    args = parser.parse_args()
    if args.mode not in ['default','farm','forest','all']:
        errorMsg('Usage: {} --mode <forest|farm|default|all>'.format(sys.argv[0]))

    TMPLATES_DIR = '{}_template_icons'.format(args.template)

    ant = eval('Ant{}'.format(args.mode))(args.logdir)
    while True:
        try:
            ant.play()
        except Exception as e:
            print('GEMFIELD: {}. But will try again...'.format(str(e)))
            time.sleep(10)
