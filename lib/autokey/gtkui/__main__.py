import faulthandler
faulthandler.enable()

from autokey.gtkapp import UI


def main():
    a = UI()
    a.main()


if __name__ == '__main__':
    main()
