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

current_platform = platform.system()
templates_dir = 'templates'
screenshot_img = '{}/current_gemfield_farm.png'.format(tempfile.gettempdir())
adb_screenshot_cmd = 'adb exec-out screencap -p > {}'.format(screenshot_img)
adb_lighter_cmd = 'adb shell input keyevent 221'
adb_darker_cmd = 'adb shell input keyevent 220'
adb_screen_stayon_cmd = 'adb shell svc power stayon usb'

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
        ##
        self.ant_farm_neighbour_flag_template = loadTemplate(os.path.join(self.templates_dir, 'ant_farm_neighbour_flag.png') )
        self.ant_farm_neighbour_template = loadTemplate(os.path.join(self.templates_dir, 'ant_farm_neighbour.png') )
        self.back_from_ant_farm_template = loadTemplate(os.path.join(self.templates_dir, 'back_from_ant_farm.png') )
        self.ant_farm_icon_template = loadTemplate(os.path.join(self.templates_dir, 'ant_farm_icon.png') )
        self.thief_flag_template = loadTemplate(os.path.join(self.templates_dir, 'thief_flag.png') )
        ##
        self.forest_icon_template = loadTemplate(os.path.join(self.templates_dir,'forest_icon.png'))
        self.back_from_forest_template = loadTemplate(os.path.join(self.templates_dir,'back_from_forest.png'))
        ##
        self.more_friends_template = loadTemplate(os.path.join(self.templates_dir,'more_friends.png'))
        self.forest_energy_template = loadTemplate(os.path.join(self.templates_dir,'forest_energy.png'))
        self.forest_energy_ball_template = loadTemplate(os.path.join(self.templates_dir,'forest_energy_ball.png'))

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
        self.height, self.width = self.monitor.shape[:2]
        #delete the image
        os.remove(screenshot_img)
        
    def checkFarm(self):
        for i in range(3):
            if self.getBackIconPos():
                return
            #suppose we are in homepage
            rc = self.match(self.ant_farm_icon_template, 0.9, 'ant_farm_icon_template')
            if not rc:
                errorMsg('Open your zhifubao App')
                
            x,y = rc
            adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
                
            os.system(adb_tap_cmd)
            time.sleep(10)
            self.scanFarm()
        errorMsg('Cannot locate your zhifubao app correctly.')
        
    def setScreenStayon(self):
        print('preparing to keep screen on...')
        # os.system(adb_lighter_cmd)
        # os.system(adb_darker_cmd)
        os.system(adb_screen_stayon_cmd)

    def getBackIconPos(self):
        return self.match(self.back_from_ant_farm_template, 0.9, 'back_from_ant_farm_template', is_left=True)
        
    def getCribPos(self):
        rc = self.match(self.crib_template, 0.8, 'crib_template')
        return rc

    def getIndicatorPos(self):
        rc = self.match(self.indicator_template, 0.8, 'indicator_template')
        if rc is None:
            rc = self.match(self.double_indicator_template, 0.8, 'double_indicator_template')

        return rc

    def getThiefPos(self):
        return self.match(self.thief_template, 0.8, 'thief_template')

    def getRobberPos(self):
        return self.match(self.robber_template, 0.8, 'robber_template')
        
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
        warningMsg('preparing to feed gemfield chicken with {}...'.format(adb_tap_cmd))
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


    def match(self, template, threshold, op, is_left=False):
        monitor = cv2.cvtColor(self.monitor, cv2.COLOR_BGR2GRAY)
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
    
    def backhome(self, is_forest=False):
        adb_tap_cmd = 'adb shell input keyevent 4'
        print(adb_tap_cmd)
        os.system(adb_tap_cmd)
        time.sleep(1)
        

    def play(self):
        self.scanFarm()
        self.checkFarm()
        self.expelThief()
        self.expelRobber()
        self.feed()
        #time.sleep(getRandomSleep())
        time.sleep(5)

    def findMoreFriends(self):
        for i in range(3):
            swipe(self.width // 2, self.height - 10, self.width // 2, 10, 1000 )
            self.scanFarm()
            rc = self.getMoreFriendsIconPos()
            if not rc:
                continue
            x,y = rc
            adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
            print(adb_tap_cmd)
            os.system(adb_tap_cmd)
            time.sleep(5)
            break

    def getEnergyFromFriend(self, x, y):
        adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
        print(adb_tap_cmd)
        os.system(adb_tap_cmd)
        time.sleep(5)
        self.scanFarm()
        for i in range(6):
            rc = self.getEnergyBallPos()
            if not rc:
                break
            x,y = rc
            adb_tap_cmd = 'adb shell input tap {} {}'.format(x, y - 60)
            print(adb_tap_cmd)
            os.system(adb_tap_cmd)
            time.sleep(1)
            self.scanFarm()
        
        #back
        adb_tap_cmd = 'adb shell input keyevent 4'
        print(adb_tap_cmd)
        os.system(adb_tap_cmd)
        time.sleep(1)
        self.scanFarm()
        

    #current screen
    def getEnergy(self):
        for i in range(10):
            rc = self.getEnergyPos()
            if not rc:
                break
            x,y = rc
            self.getEnergyFromFriend(x,y)
    
    def getForestBackIconPos(self):
        return self.match(self.back_from_forest_template, 0.9, 'back_from_forest_template', is_left=True)

    def getMoreFriendsIconPos(self):
        return self.match(self.more_friends_template, 0.9, 'more_friends_template')

    def getEnergyPos(self):
        return self.match(self.forest_energy_template, 0.9, 'forest_energy_template')

    def getEnergyBallPos(self):
        return self.match(self.forest_energy_ball_template, 0.8, 'forest_energy_ball_template')
        
    def checkForest(self):
        for i in range(3):
            if self.getForestBackIconPos():
                return
            #suppose we are in homepage
            rc = self.match(self.forest_icon_template, 0.9, 'forest_icon_template')
            if not rc:
                errorMsg('Open your zhifubao App')
                
            x,y = rc
            adb_tap_cmd = 'adb shell input tap {} {}'.format(x,y)
                
            os.system(adb_tap_cmd)
            time.sleep(10)
            self.scanFarm()
        errorMsg('Cannot locate your zhifubao app correctly.')

    def playForest(self):
        self.scanFarm()
        self.checkForest()
        self.findMoreFriends()
        for i in range(30):
            self.scanFarm()
            self.getEnergy()
            swipe(self.width // 2, self.height - 10, self.width // 2, 300, 2000 )
            
        #back
        adb_tap_cmd = 'adb shell input keyevent 4'
        print(adb_tap_cmd)
        os.system(adb_tap_cmd)
        swipe(self.width // 2, 10 , self.width // 2, self.height - 10 , 1000 )
        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--logdir', default=None, type=str, help='You should specify the log dir.')
    args = parser.parse_args()
    
    chicken = AntFarm(args.logdir)

    counter = 0
    while True:
        counter += 1
        chicken.play()
        if counter % 100 == 17:
            chicken.backhome()
        # chicken.playForest()
        # chicken.backhome(True)

