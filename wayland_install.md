# wayland testing
Currently wayland support is largely limited (and only tested on) to gnome based distributions as it relies on a gnome-shell extension to provide information about windows.

Tested on fresh install of Ubuntu 24.04 (Gnome Shell 46). Please note that the gnome extension was just updated. It is only compatible with Gnome Shell 45+. Check your gnome shell version with `gnome-shell --version`

Instructions assume that `git`, `pip` and `venv` are already installed

```sh
sudo apt update
sudo apt install gnome-shell-extension-manager make build-essential libcairo2-dev -y
git clone https://github.com/sebastiansam55/autokey-gnome-extension
cd autokey-gnome-extension
make
gnome-extensions install autokey-gnome-extension@sebastiansam55.shell-extension.zip

cd ..
git clone https://github.com/autokey/autokey --branch develop
cd autokey
xargs -a apt-requirements.txt sudo apt install -y

python3 -m venv ~/venv
source ~/venv/bin/activate

pip install packaging pyasyncore evdev
pip install -r pip-requirements.txt

# add user to input group
sudo usermod -a -G input $USER

# add udev rule
sudo tee /etc/udev/rules.d/10-autokey.rules > /dev/null <<EOF
KERNEL=="uinput", SUBSYSTEM=="misc", OPTIONS+="static_node=uinput", TAG+="uaccess", GROUP="input", MODE="0660"
EOF
sudo udevadm control --reload-rules
sudo udevadm trigger
```
Reboot!

```sh
# now you can run autokey and it will work
gnome-extensions enable autokey-extension@sebastiansam55

cd autokey/lib
python3 -m autokey.gtkui -lc
```

# dlk - wayland testing on Fedora 40
```
#  Install system-wide prereqs:
sudo dnf -y install gnome-extensions-app git make

#  Add your userid to the "input" user group
sudo usermod -a -G input $USER

#  Add a new udev rule configuration file (copy these three lines together as one into a terminal window and press enter)
sudo tee /etc/udev/rules.d/10-autokey.rules > /dev/null <<EOF
KERNEL=="uinput", SUBSYSTEM=="misc", OPTIONS+="static_node=uinput", TAG+="uaccess", GROUP="input", MODE="0660"
EOF
```
The system must be rebooted to pick up the UDEV change, but we'll do the next step before we reboot so that we only have to reboot once ...

sebastiansam55's autokey-gnome-extension does not install due to inconsistant file naming in the ```metadata.js``` and zip files.  I have created a version that installs successfully in my fork of the autokey repo on github:
```
#  Clone the "wayland" branch from my fork of the autokey repository
mkdir -p ~/src/autokey
cd ~/src/autokey
git clone https://github.com/dlk3/autokey --branch wayland

#  Install the autokey-gnome-extension
cd ~/src/autokey/autokey-gnome-extension
make
gnome-extensions install autokey-gnome-extension@autokey.zip
```
Gnome has to be restarted to pick up this new extension, so we'll reboot now to pickup the UDEV changes from earlier and to restart Gnome:
```
sudo shutdown -r now
```
After logging back in continue with:
```
#  Enable the Gnome extension
gnome-extensions enable autokey-gnome-extension@autokey

#  Create a Python virtual environment in which to test autokey
python -m venv ~/autokey-test
source ~/autokey-test/bin/activate

#  Install autokey's prereqs in the virtual environment
cd ~/src/autokey
pip install packaging pyasyncore evdev
pip install -r pip-requirements.txt

#  Backup your existing autokey configuration files, this new version of autokey will modify them:
cp -R $HOME/.config/autokey $HOME/.config/autokey-backup

#  Run autokey
cd ~/src/autokey/lib
python -m autokey.gtkui -lc
```
After exiting autokey you can terminate the Python virtual environment and return to your workstation's default Python environment by entering the ```deactivate``` command or simply closing the terminal window.  

To run autokey again in subsequent sessions all that is necessary is:
```
source ~/autokey-test/bin/activate
cd ~/src/autokey/lib
python -m autokey.gtkui -lc
```
## dlk - specifying the name of your keyboard and mouse devices

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

## dlk - cleaning up after ourselves
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
