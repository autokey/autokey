#  Testing AutoKey on Wayland
Wayland support is limited to GNOME-based desktops.  It relies on a custom GNOME Shell extension to provide the information it needs about desktop windows.

This version still supports X11 desktops.  You should be able to switch between Wayland and X11 desktop environments without any problems.

So far this update has been tested on Ubuntu 24.04 and Fedora 40 using GNOME Shell 46.

## Clone the development version of AutoKey
```
#  Clone the "wayland" branch from my fork of the autokey repository
mkdir -p ~/src/autokey
cd ~/src/autokey
git clone https://github.com/dlk3/autokey --branch wayland
```
## Install system-wide prerequisites
On Debian/Ubuntu systems do:
```
sudo apt update
sudo apt install make build-essential libcairo2-dev -y
cd ~/src/autokey
xargs -a apt-requirements.txt sudo apt install -y
```
On Fedora/Redhat systems do:
```
sudo dnf -y install git make dbus-glib-devel
cd ~/src/autokey
xargs -a rpm-requirements.txt sudo dnf -y install
```
**NOTE** If you only run under X11 and don't need Wayland support you can skip the next four steps and jump down to the "Install AutoKey in a Python virtual environment" step
##  Install the autokey-gnome-extension
```
cd ~/src/autokey/autokey-gnome-extension
make
gnome-extensions install autokey-gnome-extension@autokey.zip
```
##  Make system configuration changes
```
#  Add your userid to the "input" user group
sudo usermod -a -G input $USER

#  Add a new udev rule configuration file (copy these three lines together as one into a terminal window and press enter)
sudo tee /etc/udev/rules.d/10-autokey.rules > /dev/null <<EOF
KERNEL=="uinput", SUBSYSTEM=="misc", OPTIONS+="static_node=uinput", TAG+="uaccess", GROUP="input", MODE="0660"
EOF
```
## Reboot
The GNOME Shell extension and the UDEV changes we have made require a system reboot to come into effect.
## Enable the GNOME Shell Extension
```
gnome-extensions enable autokey-gnome-extension@autokey
```
##  Install AutoKey in a Python virtual environment
Using a virtual environment is highly recommended to ensure that your default Python environment is not corrupted by the modules installed to run AutoKey.
```
#  Create the virtual environment in the ~/venv directory and activate it
python3 -m venv ~/venv
source ~/venv/bin/activate

#  Install prerequisite Python modules into the virtual environment
pip install packaging pyasyncore evdev
pip install -r pip-requirements.txt
```
## Run AutoKey
```
#  Backup your existing autokey configuration files, this new version of autokey will modify them:
cp -R $HOME/.config/autokey $HOME/.config/autokey-backup

#  Run autokey
cd ~/src/autokey/lib
python3 -m autokey.gtkui -lc
```
## Specifying the name of your keyboard and mouse devices

When first run, autokey may display messages about it being unable to identify your keyboard or mouse device and terminate with an exception.  If it does this then you must manually configure these devices in your ```$HOME/.config/autokey/autokey.json``` file.

The debug output from autokey will contain a list of all of the devices it found.  This is what that looks like on my workstation:
```
2024-12-13 14:46:30,099 DEBUG - autokey.uinput_interface - Found device: Sleep Button
2024-12-13 14:46:30,099 DEBUG - autokey.uinput_interface - Found device: Power Button
2024-12-13 14:46:30,099 DEBUG - autokey.uinput_interface - Found device: Power Button
2024-12-13 14:46:30,100 DEBUG - autokey.uinput_interface - Found device: Logitech ERGO M575
2024-12-13 14:46:30,100 DEBUG - autokey.uinput_interface - Found device: Logitech K330
2024-12-13 14:46:30,100 DEBUG - autokey.uinput_interface - Found device: PC Speaker
2024-12-13 14:46:30,100 DEBUG - autokey.uinput_interface - Found device: Eee PC WMI hotkeys
2024-12-13 14:46:30,100 DEBUG - autokey.uinput_interface - Found device: HDA NVidia HDMI/DP,pcm=3
2024-12-13 14:46:30,100 DEBUG - autokey.uinput_interface - Found device: HDA NVidia HDMI/DP,pcm=7
2024-12-13 14:46:30,100 DEBUG - autokey.uinput_interface - Found device: HDA NVidia HDMI/DP,pcm=8
2024-12-13 14:46:30,100 DEBUG - autokey.uinput_interface - Found device: HDA NVidia HDMI/DP,pcm=9
2024-12-13 14:46:30,100 DEBUG - autokey.uinput_interface - Found device: HDA Intel PCH Rear Mic
2024-12-13 14:46:30,100 DEBUG - autokey.uinput_interface - Found device: HDA Intel PCH Front Mic
2024-12-13 14:46:30,100 DEBUG - autokey.uinput_interface - Found device: HDA Intel PCH Line
2024-12-13 14:46:30,100 DEBUG - autokey.uinput_interface - Found device: HDA Intel PCH Line Out Front
2024-12-13 14:46:30,100 DEBUG - autokey.uinput_interface - Found device: HDA Intel PCH Line Out Surround
2024-12-13 14:46:30,100 DEBUG - autokey.uinput_interface - Found device: HDA Intel PCH Line Out CLFE
2024-12-13 14:46:30,100 DEBUG - autokey.uinput_interface - Found device: HDA Intel PCH Front Headphone
2024-12-13 14:46:30,100 ERROR - autokey.uinput_interface - Unable to find mouse
```
My mouse is the "Logitech ERGO M575" device and my keyboard is the "Logitech K330" device.  I must edit ```$HOME/.config/autokey/autokey.json``` and update these two lines in the ```settings``` element:
```
        "keyboard": null,
        "mouse": null,
```
to make them look like this:
```
        "keyboard": "Logitech K330",
        "mouse": "Logitech ERGO M575",
```
Now I can run autokey and it will start up as expected.

## Cleaning up after ourselves
To completely remove the test version of Autokey:
```
rm -fr ~/src/autokey
rm -fr ~/autokey-test
gnome-extension disable autokey-gnome-extension-autokey@autokey
gnome-extension uninstall autokey-gnome-extension-autokey@autokey
sudo rm /etc/udev/rules.d/10-autokey.rules
sudo usermod -r -G input $USER
mv $HOME/.config/autokey-backup $HOME/.config/autokey
sudo shutdown -r now
```
