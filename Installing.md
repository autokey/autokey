Installing AutoKey



General Information

First time installation:

AutoKey can be installed from a repository, a deb package or built from source. Carefully following the instructions for the appropriate method should seamlessly install AutoKey. For the details, see the sections Installing AutoKey from a Repository and Building and installing from a deb package.
Upgrades from previous versions:

If you already have AutoKey installed, you do not need to remove the previous version of AutoKey in order to upgrade.
You Must quit AutoKey and make sure the AutoKey icon is not in the Notification Area or System Tray prior to starting the installation.
You should backup ~/.config/autokey or at least copy the directory to somewhere in your home directory prior to doing an upgrade. That is the only thing that you need to back up. AutoKey will make an additional backup copy of your configuration file before it upgrades it to v0.80 format.
Again, as I said at the beginning, please follow the instructions very carefully for either method. A single typo or misspelling can cause the installation to fail.
Installing AutoKey from a Repository

Using a repository to install AutoKey in Ubuntu is easy. When installed from a repository, AutoKey will be automatically installed—with all dependencies and kept up to date by your package manager.
Note that most of the time either method of automatic installation from a repository described below will install the latest version—but not all of the time. If you want to be sure that you are installing the latest version then compare the listed version here, with the version offered from the repository sources described below. If the version shown there is more recent (higher number) than the ones in your repositories—and you want the newer version—you will have to download it and build the package from source (see: Installing AutoKey from source code).
There are two different repositories to choose from:
The Ubuntu Repositories

Since AutoKey is already available in the Ubuntu repositories, you can use any of the software installation programs that came with your version of Ubuntu to install AutoKey—the same way you install standard Ubuntu packages. Examples of software installation programs are: Synaptic, Adept, Ubuntu Software Center, apt or any other Ubuntu installation program that you prefer.
Using AutoKey's PPA

If you are new to Ubuntu, I am sure you are wondering what a PPA is. PPA stands for Personal Package Archive and is a way for individuals who have created programs for Ubuntu to create and maintain a repository that the software installation programs in Ubuntu can use to install them. This allows you to install their packages in the same way you install standard Ubuntu packages as well as automatically receive update notices. They are not checked or monitored by the creators of Ubuntu and they are not responsible for any problems—nor do they want to hear about them. You install software from PPAs at your own risk.
Using AutoKey's PPA is the best way to keep AutoKey updated. To use the PPA, you have to add it to your system's repository list. This can be done using the command line in a terminal (which probably seems intimidating, but is actually the easiest) or using your favorite Ubuntu software installer.
Both methods are described under the heading "Adding this PPA to your system" on AutoKey's PPA page.
Using the Command Line to Add the Repository:

The link Read about installing describes how to use the command line in a terminal to add the repository and the software key. Most problems you will have using this method will be from typos or not specifying your version of Ubuntu correctly.
NOTE: Before you use the instructions below, make sure you close any software installation program that may be running—or you will get an error message. To avoid errors, only one program at a time is allowed to use the repository.
The following commands only work if you are using Lucid (10.04) or a later version of Ubuntu.
Each command must be entered separately into a terminal and then the Enter key must be pressed to run it.
This command makes the PPA available to to your package management system.
sudo add-apt-repository ppa:cdekter/ppa
The next command downloads the list of currently available software for all of the software packages available from the repositories you have configured, including AutoKey's. This might take a few minutes to finish.
sudo apt-get update

Once this is done, your favorite software installation program "should" automatically be able to see and use the updates. If it does not, then use the Reload/Update Package Information icon or menu selection in your software installation program.
If you are using an earlier version of Ubuntu, the instructions for earlier versions are on the PPA page as well.
Using Your Favorite Installation Program

If you want to use your favorite software installer, on the PPA page, the instructions are under the sub-heading "Technical details about this PPA". Just click on the arrow to the left of the heading and the instructions will appear. Be sure to select your version in the text box to the right of the sub-heading "Display sources.list entries for:". The entries for the version you selected will appear in the box below.
Since each of the different software installation programs you might be using will have a different method of adding a repository, you will have to figure out how to use your personal preference by reading its documentation or man page.
Other Linux versions

For all Linux versions that do not include AutoKey in their packaging system, you will have to build a package from source. The latest source code can be found here.
Building from source will work on any Linux distro that has Python Distutils available (the setup infrastructure that AutoKey uses underneath .deb files, which are the files Ubuntu uses for its packaging system). This comes with the caveat that it will probably require some fiddling to get it working. In most cases the .deb files for Ubuntu probably will not work for other distros without modification since the paths inside the .deb file can and often do change from one distro to another and sometimes change between versions of the same distro.
If you build from source, the only way to be notified of any upgrades is to 'star' the project on the Google Code site which requires having a Google account. You will then be sent an email when a new version is uploaded.
Currently for Debian, Ubuntu, and many Ubuntu derivatives such as Linux Mint, running this command in the terminal will install AutoKey. Or you can use the software installer of your choice:
sudo apt-get install autokey

If you get an error message indicating that the file was not found, then your distro does not provide a binary package for AutoKey.
Distros such as Arch Linux and Fedora (and possibly others that I do not know about) have provided binary packages for installing AutoKey in the past and hopefully will continue to do so. Fedora is the only distro that I know of that has built rpm packages for AutoKey.
If you know of any other Linux distro that provides AutoKey binary package files in their repository, please post that distro's name on the AutoKey forum and, if possible, a link to the information about the package.
Problems or Questions

If you have a problem or questions (or just want to join in the discussion), join the AutoKey Users group and post your questions there. You can—and should—search this forum for information on how to do what you are having problems with as well as for information about any installation problem you are having, before you post your question.
If you have a problem that you want to post and request help with, please read the troubleshooting guide before you post your question and provide the information that it recommends. The troubleshooting guide and all other online documentation is located here.
Installing AutoKey from source code.

Requirements

Installing the python source code for AutoKey requires a full Debian package build. You cannot install AutoKey using only the setup.py script contained in the autokey-(version).tar.gz source file.
Before you try to build the Debian package, make sure that the packages build-essential and cdbs (the common build system for Debian packages) are installed on your system. Without these packages, you can not build the AutoKey Debian package.
The program cdbs and build-essential will be in your repository and can be installed using apt, Synaptic, etc.
Pre-Build Safety Issues:

If you are upgrading from an older version of AutoKey, before starting to build the .deb package and install the the new version of AutoKey, you should:
Turn off AutoKey if is currently running (i.e. using the Quit choice in the pop-up menu that appears when the AutoKey icon in the system tray is left clicked with the mouse).
Then, backup—BUT DO NOT DELETE—your ~/.config/autokey directory or at least copy the contents to somewhere safe on your hard drive.
If you are upgrading an existing version of AutoKey, your phrases and scripts will be automatically converted (if necessary) to the new version and installed ready for immediate use.
At this point you are ready to start the build process. There are 3 explanations of how to build and install the packages:
Version A, for experts (the short version).
Version B, for knowledgeable people who want an overview of the steps.
Version C, For those who don't know anything about installing or building software packages but want to learn.
Version A:
If you use Python and know how to build a Debian package this is all the information you need:
Download the version of your choice from the download page to your hard drive and extract the tarball.
Then, run these commands from inside the directory the extraction created:
dpkg-buildpackage -us -uc
cd ../
sudo dpkg -i autokey-gtk(version).deb autokey-common(version).deb
AutoKey is installed at this point and can be started in a terminal using autokey-gtk for normal use or autokey-gtk -l for full logging output in the terminal. You can also start it from your desktop's menu for selecting applications.
You can now delete the AutoKey files and directories in the directory you built the Debian packages in. They are no longer needed.
Version B:

If you know how to build a Debian package from Python source code, but don't do it often enough to remember all of the detailed steps, here they are:
Download the version of your choice from the download page to your hard drive.
Move or download the source code to a local directory of your choice.
Open a terminal window in that directory.
un-tar the source code tarball using tar xvzf <filename> or your file manager.
cd to the directory just created by the tar command, called autokey-x.xx.x (change x.xx.x to the version number on the filename you downloaded)
Type in this command and press enter:
dpkg-buildpackage -us -uc

Make sure the word "aborting" does not appear in the output after you type the command—if it does, it will usually be in the first 10 to 20 lines. If everything works correctly, the output from this command will be 8 or more screen-fulls long and the last line will be:
dpkg-buildpackage: full upload; Debian-native package (full source is included)

Type in:

cd ../ 
and press enter to move up to the directory the newly created *.deb files are in.
Type in this command and press Enter. It ALL needs to be on a single line in the terminal:
sudo dpkg -i autokey-gtk(version).deb autokey-common(version).deb

Replace (version) with the version numbers used in the newly created *.deb files. In the terminal window, the output for this command (if successful) will be around 15 lines long.

AutoKey is installed at this point and should be started in a terminal using autokey-gtk for normal use or autokey-gtk -l for full logging output in the terminal. You can also start it from the desktop's drop down menu for selecting applications.
Once the Icon appears in the system tray, you can left click on it, Open the Main Window and create scripts and phrases as well as configure it to start automatically every time you start up your computer.
You can now delete the AutoKey directory where you built the Debian packages. They are no longer needed.
Version C:

For those not familiar with installing or building software packages who want to learn, here are the detailed steps to build and install AutoKey:
First, download the version of your choice from the download page to your hard drive.
Then move the file to the directory that you use to build or compile other software, if you have one. If you do not have one, it is a good idea to create a new directory, anywhere in your home directory, to use to extract and uncompress the file and to build the .deb package in. I created a directory called install, but what you name it is not important.
You then need to open a terminal window and change to the directory where you wish to build the package. If you created a directory in your Download folder called install you would use this command to change to that directory:
cd ~/Downloads/install

in the terminal window.
Once the source code file is in position and your terminal is showing the right directory in its window you are ready to uncompress the source code file.
AutoKey's files are packaged with the program tar and compressed with the program gzip this results in a file with a name like; autokey-(version).tar.gz. These files are commonly called tarballs. (I guess because they were created with tar and everything was all wrapped up and compressed into a single ball containing many different files.)
The universal method of uncompressing .tar.gz files is to enter this command in the terminal window:
tar xvzf autokey(version).tar.gz

You will of course have to replace (version) with the version numbers on the package you downloaded.
Many file managers like Konqueror will let you right click on the file name and chose to extract the highlighted file from a list of different choices. Extract Here, if available, is usually the best choice. There are many different file managers and there is no way I could explain how to use all of them. So, if you want to use your file manager to uncompress and extract files, you will have to research how to do this yourself.
My only advice is to ALWAYS do the extraction in an empty directory. If something goes wrong it can be messy ....
When the tarball is uncompressed, it creates a new directory called autokey-x.xx.x (x.xx.x will be the version number of the AutoKey package you are building).
You now have to move to that directory using this cd command in the terminal:
cd autokey-x.xx.x

Change x.xx.x to the numbers of the new directory.

Once you are in the new AutoKey directory, enter the following command in the terminal window to build the AutoKey package. Press enter to start the build.
dpkg-buildpackage -us -uc

Make sure the word aborting does not appear in the output after you type the command—if it does, it will usually be in the first 10 to 20 lines. If it does appear, the package was not built and you can not continue. If everything works correctly, the output from this command will be 8 or more screen-fulls long and the last line will be:
dpkg-buildpackage: full upload; Debian-native package (full source is included)
Success .… You have just created the .deb package/file and can now proceed to the installation part.
In the terminal window enter the following command and press enter.
cd ../

This moves up one directory (out of the AutoKey directory that extracting the tarball created). This is where the package build process put the *.deb files it created.
Now we install the *.deb files. First we want to know what they are called. In the terminal type:
ls

and press enter. This will list all the files in the directory the terminal is in. You have to use the numbers from the *.deb files to replace the (version) place holder in the command in step 11 below.
It is really easy to mistype the following command or accidentally start the process before you get everything correct, so I suggest you use the command line's built in expansion feature to create the command. First copy and paste (or type in):
sudo dpkg -a autokey-g

in the terminal window and then press the Tab key.
This should expand to: sudo dpkg -i autokey-gtk(your version).deb with a space at the end. Then, at the end of this command, copy and paste (or type in):

autokey-c

making sure you do not overwrite the space and then press the Tab key, which will expand the filename and the end result in the terminal should look like this:
sudo dpkg -i autokey-gtk(your version).deb autokey-common(your version).deb

In the terminal, this should all appear in a single line.
Press enter to start the installation.
Once started, it will ask you for your login password. Once you have entered your password and pressed enter, it will start the installation process.
In the terminal, the output for this command (if successful) will be only around 15 lines long.
You are now finished with the installation.
Starting AutoKey:

You can start AutoKey from the terminal by typing autokey-gtk and pressing enter or you can start it from the desktop's drop down menu for selecting applications. Once the Icon appears in the system tray, you can left click on it and create scripts and phrases as well as configure it to start automatically every time you start up your computer.
Later, if you have problems, you can start AutoKey with full logging output using the command autokey-gtk -l and it will list every step it takes in the terminal window.
Installation Related Issues

Moving AutoKey scripts and phrases from computer to computer.

The individual folders (Top Level Folders) and file pairs containing information about the phrases and scripts are stored in the ~/.config/autokey/data folder. In each Top Level Folder, there are two files per each phrase or script. They both have the same name, but different extensions, and one of them is a "hidden" file (it has a period at the front of the name and can not be seen unless the file manager or the program you use in a terminal is told to display them). An example pair would be; .tt.json and tt.txt. The *.txt file contains the name of the script or phrase that is displayed in AutoKey. (see the section below How to re-import pre-v0.80 *.json files, for a definition of a .json file)
Make sure you include the "hidden" *.json files as well as the *.txt files when you transfer individual file pairs and/or complete folders—or the scripts and phrases will not work.
Duplicating or Cloning ALL your scripts and phrases to a new system. 

You do this by replacing the entire ~/.config/autokey/ folder and all its sub-folders in the "receiving" computer with the ~/.config/autokey/ folder from the "original" computer. This will make the "receiving" computer identical to the "original" computer.
Merging one system's scripts and phrases with a second computer. 

Merging is done by copying all of the contents of any sub-folder in the "original" computer's ~/.config/autokey/data folder to the sub-folder of your choice in the "receiving" computer's ~/.config/autokey/data folder.
A step by step description of merging is: copy the "contents" (i.e. files, not folders) of any one of the sub-folders (Top Level Folders) from the "original" computer's ~/.config/autokey/data folder into a sub-folder (i.e. existing or newly created Top Level Folder) in the "receiving" computer's ~/.config/autokey/data folder.
Once all of this is finished, when you close and restart AutoKey all of the transferred folders, scripts and phrases will appear in AutoKey's main menu along with all Top Level Folders, phrases and scripts that were in the "receiving" computer's sub-folder prior to the transfer.
Warning: If a filename in the "original" computer is identical to the one in the "receiving" computer—the one in the "receiving" computer will be overwritten. If they both have identical contents—this is not a problem. If they are not identical, then the original phrases/scripts in the "receiving" computer will be replaced by the new phases and scripts. You will usually get a warning that this is fixing to happen—except when you use programs like cp or mv from the console.
In a few rare cases, merges can cause duplicate script or phrase names in the main menu of the "receiving" computer. You can change the "description:" line in the *.txt file—in order to solve this type of file name conflict. Please make a backup of the individual files you are editing or of the entire directory, before you edit these files.
Copying specific phrases or scripts from one computer to another:

If you move the pair of files into one of the sub-folders in the "receiving" computer's ~/.config/autokey/data folder, when you restart AutoKey it will read and include that script or phrase. Note, that the above "Warning" about overwriting files applies here as well. You can copy as many of these "pairs" of files at one time as you want. Just remember that you have to restart AutoKey before they will be available.
How to re-import pre version 0.80.x *.json` files

A *.json file is a configuration file. In the case of version 0.80.x or later of AutoKey, each one contains the information about an individual script or phrase that you created. They are plain text (ASCII) files and, if edited, you MUST use a text editor like nano, gedit or kate. If you use a word processor to edit them, it will insert word processor codes that will make the *.json and *.txt files unusable.
The *.json files are "hidden" files (they have a period at the front of the name and can not be seen unless the file manager or the program you use in a terminal is told to display them) and have a matching *.txt file paired with them. Both the "hidden" *.json file and the *.txt file must be present for the phrase or script to work.
Versions of AutoKey prior to 0.80.x used a single *.json file to contain ALL information about ALL scripts and phrases. When upgrading, this single file has to be converted into matched pairs of files for each phrase or script and stored in a "Top Level Folder".
AutoKey version 0.08.x will automatically import and convert version 0.71.x or earlier autokey.json files to the new format.
The following instructions assume that you already have a running version of AutoKey 0.80.x installed.
Quit AutoKey and make sure the AutoKey icon is not in the Notification Area or System Tray.
If you have created scripts for version 0.80.x and you want to preserve your current scripts and phrases, "COPY" the ~/.config/autokey/data folder to somewhere else in your home directory for safekeeping.
Then, delete these two files in the original folder: ~/.config/autokey/autokey.json and ~/.config/autokey/autokey.json~
If you want to re-import the backup file of earlier versions of AutoKey that were automatically created by AutoKey during an upgrade to version 0.80.x, you need to rename ~/.config/autokey/autokey.json(old version) to ~/.config/autokey/autokey.json. In my case the file to be renamed was autokey.json0.71.2.
If you want to use a previous backup or copy of an "autokey.json" file that you made, or one from a different computer, "move" the current ~/.config/autokey/autokey.json to somewhere safe—or delete it if you do not want to save it. Then copy and paste in the version that you want to convert.
The first time you start AutoKey, it will automatically import the older autokey.json file and convert it to the new version 0.80 format as well as make a backup of it.
Now your newly converted and backed up scripts and phrases can be copied, moved, replaced or merged as described in the section, Moving AutoKey scripts and phrases from computer to computer above.

November 2011

Original author, Keith W. Daniels

Edited by Joseph Pollock