#  Testing AutoKey on Wayland
Wayland support is limited to GNOME-based desktops.  It relies on a custom GNOME Shell extension to provide the information it needs about desktop windows.

This version of AutoKey still supports X11 desktops.  You should be able to switch between Wayland and X11 desktop environments without any problems.  AutoKey looks at the XDG_SESSION_TYPE environment variable to determine whether or not it is running in Wayland.

Basic testing of this version of AutoKey has been done on:
- Ubuntu 24.04 (GNOME Shell 46.0) - under Wayland and X11
- Fedora 40 Workstation (GNOME Shell 46.6) - under Wayland and X11 
- Fedora 41 Workstation (GNOME Shell 47.2) - under Wayland only, X11 is deprecated in this release

## 1) Clone the development version of AutoKey
```
#  Clone the "wayland" branch from my fork of the AutoKey repository
mkdir -p ~/src
cd ~/src
git clone https://github.com/dlk3/autokey --branch wayland
```
**NOTE** Assuming the pull request with my updates gets merged into the develop branch of the master AutoKey repository, once that is done the code can be cloned from that repo as well, using this command:
```
git clone https://github.com/autokey/autokey --branch develop
```
## 2a) Install Ubuntu system prereqs:
```
sudo apt update
sudo apt install make build-essential libcairo2-dev python3-venv gnome-shell-extension-manager -y
cd ~/src/autokey
xargs -a apt-requirements.txt sudo apt install -y
```
## 2b) Install Fedora system prereqs:
```
sudo dnf -y group install c-development
sudo dnf -y install git make cmake dbus-glib-devel python3-devel cairo-devel gobject-introspection-devel cairo-gobject-devel
cd ~/src/autokey
xargs -a rpm-requirements.txt sudo dnf -y install
```
## 3) Install AutoKey
**NOTE** If you only ever run under X11 and don't need Wayland support you can skip the next four steps and jump down to the "3.5 Install AutoKey in a Python virtual environment" step.
###  3.1) Install the autokey-gnome-extension GNOME Shell extension
```
cd ~/src/autokey/autokey-gnome-extension
make
gnome-extensions install autokey-gnome-extension@autokey.zip
```
###  3.2) Make system configuration changes to enable use of the uinput interface
```
#  Add a new udev rule configuration file that grants the "input" user group access to the /dev/uinput kernel device (copy these three lines together as one into a terminal window and press enter)
sudo tee /etc/udev/rules.d/10-autokey.rules > /dev/null <<EOF
KERNEL=="uinput", SUBSYSTEM=="misc", OPTIONS+="static_node=uinput", TAG+="uaccess", GROUP="input", MODE="0660"
EOF
```
### 3.3) Reboot
The GNOME Shell extension and the UDEV changes we have made require a system reboot to come into effect.
```
sudo shutdown -r now
```
### 3.4) Enable the GNOME Shell extension and add your userid to the "input" user group
Run this script:
```
~/src/autokey/autokey-user-config
```
You will be prompted to log off and log back on again after running that script.
###  3.5) Install AutoKey in a Python virtual environment
Using a virtual environment is highly recommended to ensure that the modules installed to support AutoKey do not conflict with your default Python environment.
```
#  Create the virtual environment in the ~/venv directory and activate it
python3 -m venv ~/venv
source ~/venv/bin/activate

#  Install prerequisite Python modules into the virtual environment
pip install packaging pyasyncore evdev
cd ~/src/autokey
pip install -r pip-requirements.txt
```
### 3.6) Run AutoKey
```
#  Backup your existing autokey configuration files, this new version of autokey will modify them:
cp -R ~/.config/autokey ~/.config/autokey-backup

#  Run autokey
cd ~/src/autokey/lib
python3 -m autokey.gtkui -vc
```
After AutoKey has been terminated, the Python virtual environment can be deactivated by entering the command ```deactivate``` at the command prompt, or by exiting the terminal window.

On subsequent runs, start AutoKey with these commands:
```
source ~/venv/bin/activate
cd ~/src/autokey/lib
python3 -m autokey.gtkui -v
```
## 4) Installing the AutoKey icons
If you don't already have the AutoKey icons installed on your system, AutoKey will show up on the taskbar as an unknown three dot icon.  To install the AutoKey icons:
```
mkdir ~/.local/share/icons   #  If you don't already have this directory
cd ~/src/autokey/config/
cp -vr *.png *.svg Humanity ubuntu-mono-* ~/.local/share/icons/
```
**NOTE** By default, the GNOME desktop on Fedora does not have a taskbar.  There will be no AutoKey icon or any way to access the AutoKey main window until a GNOME Shell extension is added that displays a taskbar.  My favorite extension for this purpose is "AppIndicator and KStatusNotifierItem Support by 3v1n0" but there are other choices.  Go to https://extensions.gnome.org to find, install, and manage GNOME Shell extensions on your desktop.
## 5) Cleaning up after ourselves
To completely remove the test version of Autokey:
```
#  If you installed the AutoKey icon files in ~/.local/share/icons, then:
find ~/.local/share/icons -iwholename \*/autokey\* -delete

rm -fr ~/src/autokey
rm -fr ~/venv
gnome-extensions disable autokey-gnome-extension-autokey@autokey
gnome-extensions uninstall autokey-gnome-extension-autokey@autokey
sudo rm /etc/udev/rules.d/10-autokey.rules
sudo usermod -r -G input $USER
mv ~/.config/autokey-backup ~/.config/autokey
sudo shutdown -r now
```
