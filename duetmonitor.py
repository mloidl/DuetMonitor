#!/usr/bin/env python3

import os
import sys
import time
import configparser
import datetime
import json
import requests
import http.client
import urllib
import csv

printimage = '/tmp/printimage.jpg'

def main(argv):
    print('DuetMonitor started.')

    # check and initially load config
    global config
    readCheckConfig()

    printing = False
    filename = None
    energy_monitor_start = 0.0
    printDuration = 0

    global hostname
    global reprap_pass

    # main loop
    while True:
        try:
            reloadConfig()

            hostname = config.get('main', 'hostname')
            reprap_pass = config.get('main', 'password')

            requests.get('http://' + hostname + '/rr_connect?password=' + reprap_pass + '&time=' + datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
            status = json.loads(requests.get('http://' + hostname + '/rr_status?type=1').text)['status']
            if status == 'P' and not printing:
                printing = True
                startTime = datetime.datetime.now()
                filename = os.path.basename(json.loads(requests.get('http://' + hostname + '/rr_fileinfo').text)['fileName'])
                printDuration = 0
                if (useEnergyMonitor()):
                    energy_monitor_start = getCurrentEnergy()
                print('Print started:', filename)
            if status == 'I' and printing:
                print('Print finished:', filename)

                if useImage():
                    if useLightForImage():
                        # turn light on
                        switchLight(255)
                        # make sure it's on => wait 5sec
                        time.sleep(15)
                    # take a photo
                    files = getImage()

                    if useLightForImage():
                        # turn light off
                        switchLight(0)
                else:
                    files = None

                message = 'Print of {} finished!\nDuration: {}'.format(filename, datetime.timedelta(seconds=printDuration))
                energy_use = 0.0
                if (useEnergyMonitor()):
                    energy_use = float(getCurrentEnergy()-energy_monitor_start)
                    message += '\nEnergy used: {:.2f}Wh'.format(energy_use)

                r = requests.post("https://api.pushover.net/1/messages.json", data = {
                    "token": config.get('pushover', 'app_token'),
                    "user": config.get('pushover', 'user'),
                    "message": message
                },
                files = files)
                print(r.text)

                if os.path.isfile(printimage):
                    os.remove(printimage)

                if (writeStatistic()):
                    #(filename, start, end, duration, energy)
                    writeStatisticToFile(filename, startTime, datetime.datetime.now(), printDuration, energy_use)

                printing = False
                filename = None
            if status == 'P' and printing:
                # get printDuration of current file directly from printer
                printDuration = json.loads(requests.get('http://' + hostname + '/rr_fileinfo').text)['printDuration']
            requests.get('http://' + hostname + '/rr_disconnect')
        except Exception as e:
            print('ERROR', e)
            pass
        time.sleep(60)
        print('...')

def getImage():
    files = None
    try:
        img_data = requests.get(config.get('image', 'snapshot_url')).content
        with open(printimage, 'wb') as handler:
            handler.write(img_data)
        files = {
            "attachment": ("printimage.jpg", open(printimage, "rb"), "image/jpeg")
        }
    except Exception as ei:
        print('Could not get image', ei)
        files = None

    return files


def readCheckConfig():
    reloadConfig()

    if not checkConfig():
        return False

    print("Configuration read sucessfull")

def checkConfig():
    valid = True
    # hostname must be set
    if (config.get('main','hostname') is ''):
        print ("Duet hostname is not set")
        valid = False

    # password must be set
    if (config.get('main','password') is ''):
        print ("Duet password is not set")
        valid = False

    # pushover app_token must be set
    if (config.get('pushover','app_token') is ''):
        print ("Pushover app_token is not set")
        valid = False

    # pushover user must be set
    if (config.get('pushover','user') is ''):
        print ("Pushover user is not set")
        valid = False

    # check image settings
    if (useImage()):
        if (config.get('image', 'snapshot_url') is ''):
            print ("Images should be used but snapshot_url is not set")
            valid = False

    # check energy monitor settings
    if (useEnergyMonitor()):
        if (config.get('energy_monitor', 'energy_url') is ''):
            print ("Energy monitor should be used but energy_url is not set")
            valid = False

    # check statistic settings
    if (writeStatistic()):
        if (config.get('statistics', 'file') is ''):
            print ("Statistics should be written but file is not set")
            valid = False

    if (not valid):
        raise Exception('Configuration Error')

def switchLight(value):
    requests.get('http://' + hostname + '/rr_gcode?gcode=M106 P2 S' + str(value))

def reloadConfig():
    global config
    config = configparser.SafeConfigParser()
    config.read(['duetmonitor.cfg', os.path.expanduser('~/.duetmonitor.cfg')])

def useLightForImage():
    return config.getboolean('main', 'use_image_light', fallback=False)

def useImage():
    return config.getboolean('main', 'send_image', fallback=False)

def useEnergyMonitor():
    return config.getboolean('main', 'use_energy_monitor', fallback=False)

def writeStatistic():
    return config.getboolean('main', 'write_statistic', fallback=False)

def writeStatisticToFile(filename, start, end, duration, energy):
    print ("Write statistic to file called")
    csv_file = config.get('statistics', 'file')
    write_header = False

    if not os.path.isfile(csv_file):
        write_header = True


    #datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    with open(csv_file, 'a') as csvHandler:
        newFileWriter = csv.writer(csvHandler, delimiter=';')
        if write_header:
            newFileWriter.writerow(['filename', 'start', 'end', 'duration', 'energy'])

        newFileWriter.writerow([filename, start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S'), duration, '{:.2f}'.format(energy)])

    print ("Write statistic to file finished")


def getCurrentEnergy():
    try:
        return float(requests.get(config.get('energy_monitor', 'energy_url')).text)
    except Exception as ei:
        print ('Could not get current energy')

    return 0.0

if __name__ == "__main__":
    main(sys.argv)
