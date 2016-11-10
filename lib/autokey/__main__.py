import os, sys
import faulthandler;faulthandler.enable()

from autokey.gtkapp import Application

def main(args=None):
    a = Application()
    a.main()

