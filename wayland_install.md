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