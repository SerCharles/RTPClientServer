'''
描述：pyqt主客户端
'''

from tkinter import *
import tkinter.messagebox as MessageBox
from PIL import Image, ImageTk
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import socket, threading, sys, traceback, os
import random
import time
from math import *

from RtpPacket import RtpPacket
from Constants import Constants

def ChangeSize(event):
    print("kebab")

if __name__ == "__main__":

    root = Tk()
    lb = Label(root, text='hello Place')
    # lb.place(relx = 1,rely = 0.5,anchor = CENTER)
    # 使用绝对坐标将Label放置到(0,0)位置上
    lb.place(x=0, y=0, anchor=NW)
    root.bind("<Escape>", ChangeSize)
    root.mainloop()