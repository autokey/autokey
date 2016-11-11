import os, sys
import faulthandler;faulthandler.enable()

from autokey.gtkapp import Application

def main():
    a = Application()
    a.main()

