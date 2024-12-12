import faulthandler
faulthandler.enable()

from autokey.gtkapp import Application


def main():
    a = Application()
    a.main()


if __name__ == '__main__':
    main()
