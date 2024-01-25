from Settings import prayerFrameBgColor
from tkinter import Label
import json
from Settings import today, month, day, year, minsBeforeSalah, notPrayerFontSize,prayerFontSize, prayerLabelsPaddingX, otherPrayerLabelsPaddingX, adhaanCheckInterval, prayerPassedCheckInterval
from Jummah import firstJammah, secondJammah
from datetime import datetime, timedelta
from audioplayer import AudioPlayer
from threading import Thread
import schedule
import requests

def playNoise(soundFile):
    AudioPlayer("Sounds/" + soundFile + ".mp3").play(block=True)

class Prayers:
    def __init__(self, frame):
        self.frame = frame
        self.prayerLength = 5
        self.schedulerSet = False
        self.getPrayersScheduler = None
        self.prayerTimeObj = [[None for _ in range(5)] for _ in range (2)]
        self.prayerLabels = [[None for _ in range(5)] for _ in range (2)]
        self.getPrayers()
        self.adhaanAnnounce = False
        self.startAnnounceIndex = 0
        self.salahAnnounceIndex = 0
        self.salahAnnounce = False
        schedule.every(adhaanCheckInterval).seconds.do(self.announceAdhaanAndSalah)

    def salahsToDate(self):
        index = 0
        if self.prayers[1][1] != "":
            for i in range(1, 3):
                for j in range(1, 6):
                    salahsSplit = self.prayers[i][j].split(":")
                    if j == 1 or (j == 2 and (salahsSplit[0] == "12" or salahsSplit[0] == "11")):
                        self.prayerTimeObj[i-1][j-1] = datetime(year, month + 1, day + 1, int(salahsSplit[0]), int(salahsSplit[1]))
                    else:
                        self.prayerTimeObj[i-1][j-1] = datetime(year, month + 1, day + 1, int(salahsSplit[0]) + 12, int(salahsSplit[1]))
                    index+=1
    def getPrayers(self):
        try:

            self.data = json.load(open("times.json"))
            self.prayers = [
                ["", "Fajr", "Zuhr", "Asr", "Maghrib", "Isha"],
                ["Start",self.data[month][day]['Fajr_start'], self.data[month][day]['Zuhr_start'], self.data[month][day]['Asr_start2'], self.data[month][day]['Maghrib_start'], self.data[month][day]['Isha_start']],
                ["Jama'ah",self.data[month][day]['Fajr_jamaah'], self.data[month][day]['Zuhr_jamaah'], self.data[month][day]['Asr_jamaah'], self.data[month][day]['Maghrib_jamaah'], self.data[month][day]['Isha_jamaah']]
            ]
            self.salahsToDate()
            schedule.cancel_job(self.getPrayersScheduler)
            self.schedulerSet = False
        except Exception as e:
            print("Error!\n\n", e)
            self.prayers = [
                ["", "Fajr", "Zuhr", "Asr", "Maghrib", "Isha"],
                ["Start","", "", "", "", ""],
                ["End","", "", "", "", ""]

            ]

            if not self.schedulerSet:
                self.schedulerSet = True
                self.getPrayersScheduler = schedule.every(2).minutes.do(self.getPrayers)
        self.showPrayers()

    def showPrayers(self):
        height = len(self.prayers)
        width = len(self.prayers[0])

        for i in range(height):
            for j in range(width):
                if (i > 0 and i < self.prayerLength) and j != 0:
                    self.prayerLabels[i - 1][j - 1] = Label(self.frame, text=self.prayers[i][j], background=prayerFrameBgColor,font=("Arial", prayerFontSize), foreground="white")
                    self.prayerLabels[i - 1][j - 1].grid(row=i, column=j, ipadx=prayerLabelsPaddingX, sticky='NSWE')
                else:
                    font =notPrayerFontSize
                    
                    notPrayer = Label(self.frame, text=self.prayers[i][j], background=prayerFrameBgColor,
                                      font=("Arial", font), foreground="white")
                    notPrayer.grid(row=i, column=j, ipadx=otherPrayerLabelsPaddingX, sticky='NSWE')
        if self.prayers[1][1] != "":
            self.checkPrayerPassed()

    def checkPrayerPassed(self):
        if self.prayers[1][1] != "":
            for i in range(len(self.prayerTimeObj[0])):
                if (self.prayerTimeObj[0][i] < datetime.now()):
                    self.prayerLabels[0][i].config(background="green")
            for i in range(len(self.prayerTimeObj[1])):
                if (self.prayerTimeObj[1][i] > datetime.now()):
                    self.prayerLabels[1][i].config(background="orange")
                    break
            for i in range(len(self.prayerTimeObj[0])):
                if i == len(self.prayerTimeObj[1])-1:
                    continue
                if (self.prayerTimeObj[0][i + 1] < datetime.now()):
                    self.prayerLabels[0][i].config(background="red")
            for i in range(len(self.prayerTimeObj[1])):
                if (self.prayerTimeObj[1][i] < datetime.now()):
                    self.prayerLabels[1][i].config(background="red")

    def announceAdhaanAndSalah(self):
        if self.prayers[1][1] != "":
            for i in range(len(self.prayerTimeObj[0])):
                if (datetime.now() >= self.prayerTimeObj[0][i] and datetime.now() < (self.prayerTimeObj[0][i] + timedelta(minutes=1))) and not self.adhaanAnnounce:
                    self.adhaanAnnounce = True
                    self.startAnnounceIndex = i
                    self.checkPrayerPassed()
                    if i == 0:
                        Thread(target=playNoise, args=("adhaan-new",)).start()
                    else:
                        Thread(target=playNoise, args=("adhaan-new-long",)).start()
                    break
                if(datetime.now() >= (self.prayerTimeObj[1][i] - timedelta(minutes=minsBeforeSalah)) and datetime.now() <(self.prayerTimeObj[1][i]-timedelta(minutes=(minsBeforeSalah-1))) and not self.salahAnnounce):
                    self.salahAnnounce = True
                    self.salahAnnounceIndex = i
                    Thread(target=playNoise,args=("salah",)).start()
                    break
                if (datetime.now() >= self.prayerTimeObj[0][i] and datetime.now() < (self.prayerTimeObj[0][i] + timedelta(minutes=1))) or (datetime.now() >= self.prayerTimeObj[1][i] and datetime.now() < (self.prayerTimeObj[1][i] + timedelta(minutes=1))):
                    self.checkPrayerPassed()
            if not (datetime.now() >= self.prayerTimeObj[0][self.startAnnounceIndex] and datetime.now() < (
                    self.prayerTimeObj[0][self.startAnnounceIndex] + timedelta(minutes=1))):
                self.adhaanAnnounce = False
            if not (datetime.now() >= (self.prayerTimeObj[1][self.salahAnnounceIndex] - timedelta(minutes=minsBeforeSalah)) and datetime.now() <(self.prayerTimeObj[1][self.salahAnnounceIndex]-timedelta(minutes=(minsBeforeSalah-1)))):
                self.salahAnnounce = False