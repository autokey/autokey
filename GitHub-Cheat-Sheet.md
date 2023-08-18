## About

This file provides the steps for doing some of the tasks you may want to do when contributing to the [AutoKey project](https://github.com/autokey/autokey). The information is divided into four sections:
* The **Basic GitHub Workflow** gives you an idea of what the workflow looks like.
* The **Local** section is for things you can do on the command-line.
* The **Remote** section is for things you can do on GitHub in your browser.
* The **Notes** section is for things that don't fit anywhere else.

The **Local** and **Remote** sections are alphabetized and do not necessarily present the entries in the order in which you would use them.

******************************************************************************************************************************

## Basic GitHub Workflow

These steps take you through the basic workflow for using GitHub in your browser to contribute to the AutoKey project in a beginner-friendly way.

1. Fork a remote repository:
   1. Go to the repository's main page.
   2. Click the **Fork** button in the top right corner.
   3. Choose an owner for the fork if you like (it will be you by default).
   4. Change the name of the fork if you like (it will be the original repository's name by default).
   5. Change the description if you like (it will be the original repository's description by default).
   6. **Uncheck** the **Copy the master branch only** box (*this is important*).
   7. Click the **Create fork** button. *Note that once the forking process is complete, you'll automatically be at the main page of your new forked repository.*
2. Open the branch you'd like to work on.
3. Create a new branch off of that branch with a name that lets you know what kind of change you're about to make. *Note that this will be a temporary branch that's for your use only and won't be copied to the remote repository that you forked.*
4. Make one or more changes to one or more files inside the new branch you just created with one of these methods:
	* Use the GitHub editor to make the changes, committing each one with a comment describing what you did.
	* Use the command line to clone your fork, make the changes, and push them to your fork.
5. Update the **CHANGELOG.rst** file to note the change(s).
6. Start a pull request with any **one** of these methods:
   * Click the **Compare & pull request** button above the file list.
   * Click the link in the note above the file list that tells you that this branch is ahead of the branch your changes will be made in.
   * Click **Pull requests** in the top menu and then click the **Compare and pull request** button.
   * Click **Pull requests** in the top menu and then click the **New pull request** button.
7. Check the information in the grey section at the top to make sure that:
   * the **base repository** is the remote repository that you forked
   * the **base** is the remote branch that you want to change
   * the **head repository** is your fork
   * the **head** or **compare** is the branch that contains your change(s)
8. Scroll down to review the change(s) you made to the file(s).
9. When you're satisfied with the settings and your changes, click the **Create pull request** button.
10. Verify that you have an **Able to merge** message from GitHub.
11. Type a meaningful title for the pull request into the top text box to give the remote repository's maintainer a quick idea of the reason for this pull request.
12. Type a detailed comment into the **Write** text box, if you like, letting the remote repository's maintainer know more about the change(s) that you've made.
13. Click the **Create pull request** button.
14. Once the remote repository's maintainer has merged the pull request into the remote repository (you'll be notified by email when that happens), you can delete the temporary branch you had created in your fork in step 3 above or delete the entire fork:
    1. Go to the remote repository's main page.
    2. Click the **Pull requests** entry in the menu.
    3. Click **Closed** in the heading above the list of pull requests on that page.
    4. Click on the name of your pull request.
    5. Scroll down to the **Pull request successfully merged and closed** section at the bottom.
    6. Click the **Delete branch** button in that section to delete the branch and keep the forked repository or, if you no longer want the forked repository, click the **settings** link in that section.
    7. The next time you open the branch in your fork in which these changes were made, GitHub will notify you at the top of the file listing that your branch is out-of-date. This is because the changes you made in the temporary branch have now been made in the **base** branch you chose in the remote repository and they now need to be made in your fork so the two repositories can be identical. To synchronize them:
        1. Click the **Sync fork** button to the right of that message.
        2. Click the **Update branch** button.

*As an example, if you created the **foo** branch off of the **develop** branch in your fork, changed the contents of its **readme.txt** file, did a pull request, chose **develop** as the **base**, and chose **foo** as the **head**, the **readme.txt** file in the remote repository's **develop** branch will be the file that changes. The remote repository will not get a copy of your **foo** branch and you'll be able to delete the **foo** branch once the pull request is merged into the remote repository.*

*If, instead of following the above steps and editing a file in your fork, you attempt to edit a file in a repository that you don't have push rights to (the AutoKey repository), when you commit the change(s), GitHub will automatically offer to create a branch with the default name of **patch-1** (or **patch-2**, etc., depending on whether other patch branches exist). You can edit the branch name if you like. That branch gets created in the repository you don't have push rights to (in this case, the AutoKey repository) when you do a pull request and it's accepted, and it's the branch that's used as the source for the pull request. Your fork will then get a copy of that branch the next time you sync the branches. If you then view the branches in your fork, you'll see that you own that branch. Once the pull request is accepted, you can delete the branch from your fork and it will be automatically deleted from the remote repository that you don't have push access to without a pull request.*

******************************************************************************************************************************

## Local

#### Local - clone a pull request
1. Open the repository's home page in your browser.
2. Click **Pull requests** in the toolbar.
3. Get the number of the pull request from its description in the list.
4. Open a terminal window in the directory in which you'd like to create the clone's subdirectory.
5. Enter this command, replacing **develop** with the name of the branch the code from the pull request is in and replace the example URL of the repository:
   ```
   git clone --branch develop --single-branch https://github.com/autokey/autokey.git
   ```
6. Press the **Enter** key to create the clone in a new subdirectory named after the repository.
7. Change to the directory you just created:
   ```
   cd autokey
   ```
8. Fetch the pull request by replacing **844** with your pull-request number:
   ```
   git fetch origin pull/844/head:pull_844
   ```
9. Change to the pull request's branch by replacing **844** with your pull-request number:
   ```
   git checkout pull_844
   ```
#### Local - clone a repository

1. Open the repository's main GitHub page in your browser (note that this can be one of your repositories or a remote repository not owned by you).
2. Click the **Code** button.
3. Click the clipboard icon to the right of the HTTPS URL.
4. Boot into your virtual machine.
5. Open a terminal window in the directory in which you'd like to create the clone's subdirectory.
6. Enter this command, replacing the example URL with the fork's URL: `git clone https://github.com/foo/bar.git`
7. Press the **Enter** key to create the clone in a new subdirectory named after the repository.

#### Local - clone a repository branch

1. Open the repository's main GitHub page in your browser (note that this can be one of your repositories or a remote repository not owned by you).
2. Click the **Code** button.
3. Click the clipboard icon to the right of the HTTPS URL.
4. Boot into your virtual machine.
5. Open a terminal window in the directory in which you'd like to create the clone's subdirectory.
6. Enter this command, replacing **mybranch** with the name of the branch you'd like to work on and replace the example URL with the fork's URL: `git clone --branch mybranch --single-branch https://github.com/foo/bar.git`
7. Press the **Enter** key to create the clone in a new subdirectory named after the repository.

#### Local - create a virtual machine

1. <details><summary>Click here to toggle VirtualBox installation instructions.</summary>

   ____
   One of the popular virtual-machine programs is VirtualBox. Below are basic instructions for installing it:

   1. Go to the [VirtualBox LinuxDownloads page](https://www.virtualbox.org/wiki/Linux_Downloads).
   2. Click your distribution's name in the list to download a .deb file.
   3. Click the **SHA256 checksums** link to download a list of SHA checksums.
   4. Click the **MD5 checksums** link to download a list of MD5 checksums.
   5. Open a terminal window in the download folder on your computer.
   6. Run this command to generate the SHA checksum for the **.deb** file you downloaded: `sha256sum virtualbox*.deb`
   7. Compare the result with the SHA checksum matching your Linux distribution in the **SHA256SUMS** file you downloaded to make sure they're identical. If they're not, delete the **.deb** file and go back to step ii above.
   8. Run this command to generate the MD5 checksum for the **.deb** file you downloaded: `md5sum virtualbox*.deb`
   9. Compare the result with the MD5 checksum matching your Linux distribution in the **MD5SUMS** file you downloaded to make sure they're identical. If they're not, delete the **.deb** file and go back to step ii above.
   10. Install VirtualBox by double-clicking the **.deb** file in your file manager or by running this command: `sudo dpkg -i Virtual*.deb`
   11. Install the dependencies for VirtualBox and configure VirtualBox with this command: `sudo apt-get install -f`
   12. Once VirtualBox is installed, you should find a shortcut to it in your main menu (possibly in the **System** section of your menu under the name of **Oracle VM VirtualBox**).
   ____

   </details>
2. Download an .iso file from a Linux distribution onto your host computer.
3. Put the ISO into your default machine folder (if you don't remember where that is, click the **File** menu in VirtualBox, choose **Preferences...** from the context menu, and look in the **Default Machine Folder** text box.
4. Open VirtualBox.
5. Click the **New** entry in the **Machine** menu or click the **New** button in the center panel.
6. Give your virtual machine a meaningful name.
7. Click the **ISO Image** drop-down arrow and choose the ISO you just downloaded.
8. Put a check-mark in the **Skip Unattended Installation** box.
9. Click the **Next** button.
10. Examine and optionally adjust your hardware settings.
11. Click the **Next** button.
12. Examine and optionally adjust the **Virtual Hard disk** settings.
13. Examine the **Summary** and click the **Next** button if you're satisfied. Otherwise, click the **Back** button and make changes.
14. Double-click the new virtual machine in the left pane of VirtualBox.
15. Follow the on-screen instructions to install the operating system in the virtual machine.

#### Local - delete a clone

You can do this as often as you like. After cloning a repository, if you've messed up the changes you've made to the files or if you're done working on the code, you can just delete the clone's directory inside of your virtual machine. This will have no effect on the repository you cloned it from.

#### Local - edit a clone

Make any changes you feel are needed in the local files in your clone. Note that this has no effect on the GitHub repository.

#### Local - prepare your computer or virtual machine for development

1. (Optional) Boot into the virtual machine.
2. Grab all available operating-system updates.
3. Update the **apt** database: `sudo apt update`
4. Install **pip3**: `sudo apt install python3-pip`
5. Install **tkinter**:  `sudo apt install python3-tk`
6. Install **Xvfb**: `sudo apt install python3-pytest-xvfb`
7. Install **tox**: `sudo apt install tox`
8. Create a [GitHub personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token).
9. Configure your git username by replacing **John** with your username: `git config --global user.name "John"`
10. Configure your git user email by replacing John Doe's email address with yours: `git config --global user.email "john.doe@example.com"`
11. (Optional) Configure your git editor as **nano** instead of the default of **vim**: `git config --global core.editor "nano"`
12. (Optional) Configure your git pushes to tracking so that they'll go wherever they're being tracked to go automatically based on your clone command: `git config push.default tracking`

#### Local - run tests on a clone

GitHub Actions can be run locally inside of your virtual machine.

1. Open the virtual machine.
2. Open the clone's directory in a terminal window.
3. Choose a testing command to run:
   * Run a lint test: `tox -e lint`
   * Run all tests for all platforms in all environments: `tox`
   * Run all tests for all platforms in the environment that tox is installed in: `tox -e test`
   * Run all tests for all platforms in all environments, recreating the virtual environments first: `tox -r`
   * Run all tests for all platforms in all environments, recreating the virtual environments first: `tox --recreate`
   * Run all tests for the specified platform in the specified environment: `tox -e py37-test`
   * Run all tests for the specified platforms in the specified environments: `tox -e 'py3{7,11}'-test`
   * Run all tests for all platforms iusing the version of Python in PATH: `tox -e py`
   * Run all tests for the specified platform in all environments: `tox -e py37`
   * Run individual tests on specified files that start with **test_**:
     * Run an individual test on the specified file: `tox -- tests/create_single_phrase.py`
     * Run an individual test on the specified file: `tox -- tests/engine_helpers.py`
     * Run an individual test on the specified file: `tox -- tests/test_common.py`
     * Run an individual test on the specified file: `tox -- tests/test_configmanager.py`
     * Run an individual test on the specified file: `tox -- tests/test_iomediator.py`
     * Run an individual test on the specified file: `tox -- tests/test_macro.py`
     * Run an individual test on the specified file: `tox -- tests/test_phrase.py`
     * Run an individual test on the specified file: `tox -- tests/test_phrase_runner.py`
   * Run the clean, coverage, and report tests: `tox -e clean,coverage,report`

##### Interpret the test results:

When interpreting the test results, note that tests can be marked by the developers with **skip** or **xfail** if they're expected to fail for some reason, as they might with a feature not implemented yet or a bug not fixed yet.

* Marking a test with **skip** will prevent that test from being run at all.
* Marking a test with **xfail** will run that test so you can check if it fails or not.

##### Interpret the **tox** output:

* **SKIPPED** means that a test marked with **skip** wasn't tested, as expected.
* **XFAIL** means that a test marked with **xfail** failed, as expected.
* **XPASS** means that a test marked with xfail passed.

#### Local - try out your built code

If you've got what seems like a good working copy of the code, it's time to build it into files that can be installed on a machine so you can try it out and see if it works.

**TODO:** Find out if there's any difference between doing the build from the zip file, the way we do here, and doing it from a a cloned copy of the fork.

1. Open your virtual machine.
2. Open a browser inside the virtual machine.
3. Go to the repository's main page on GitHub.
4. Choose the branch that you'd like to build.
5. Click the **Code** button.
6. Click **Download ZIP** from the drop-down menu.
7. Extract the zip file, creating a directory that contains the contents of the repository.
8. Open that directory in a terminal window.
9. Pick one:
   * Install AutoKey:
     ```
     pip3 install .
     ```
   * Build AutoKey:
     1. Build the packages in the parent directory: `dpkg-buildpackage -us -uc`
     2. Test the build:
        1. Change to the parent directory: `cd ..`
        2. Install the GTK version: `sudo dpkg --install autokey-gtk_<version>.deb autokey-common_<version>.deb`
        3. Install the Qt version: `sudo dpkg --install autokey-qt_<version>.deb autokey-common_<version>.deb`
        4. Install any missing dependencies: `sudo apt install -f`
        5. See if the build works, where it puts AutoKey, and any messages/errors it generates.
        6. If everything works, copy the `.deb` files it produced to a clean virtual machine and see if they'll install and work properly there.
        
        ***TODO:** An alternative may be to run `autokey/debian/build.sh` to build the **.deb** files, but I'm thinking that will be run automatically when following the steps above. I'll update this once I do a successful build.*

#### Local - update a clone
If you have a clone of your repository on your local system and you make a change to it on GitHub, you can update your clone with this command inside of a terminal window in the clone's directory: `git fetch`

******************************************************************************************************************************

## Remote

#### Remote - add a link to a URL in your main GitHub page

To put a link to your official documentation or any other website that you like in the right panel of your main GitHub page:

1. Go to your repository's main page.
2. Click the little gear next to **About** in the right panel.
3. Paste the URL into the **Website** box.
4. Save the change.

#### Remote - archive or unarchive a GitHub repository

**Archive a repository:**

1. Go to the main page of the repository.
2. Click the **Settings** in the menu.
3. Scroll down to the **Danger Zone** section.
4. Click **Archive this repository**.
5. Read the warnings.
6. Type the name of the repository.
7. Click **I understand the consequences, archive this repository.**

**Unarchive a repository:**

1. Go to the main page of the repository.
2. Click the **Settings** in the menu.
3. Scroll down to the **Danger Zone** section.
4. Click **Unarchive this repository.**
5. Read the warnings.
6. Type the name of the repository.
7. Click **I understand the consequences, unarchive this repository.**

#### Remote - create an interactive GitHub issue template form

The standard bug report on GitHub is ordinary Markdown. You can create a YAML issue template form that's interactive instead.

1. Create the `.github/ISSUE_TEMPLATE/bug.yaml` file while you're in the main branch of your repository. That will create the `.github` folder inside of the main branch, the `ISSUE_TEMPLATE` folder inside of that one, and the `bug.yaml` file inside of that one.
2. Populate the `bug.yaml` file with your YAML code.
3. Commit the change.

#### Remote - create or add a folder on GitHub

GitHub offers a way to create a folder, but you cannot create an empty folder, so the idea is that you create a file and specify a folder for it to go into as part of the creation process.
1. Open the branch you'd like to create a folder in.
2. Click the "**Add file**" button.
3. Type a new folder name followed by `/` followed by a new file name into the text box. *Note that if you regret the folder name you just typed in, typing `..` followed by `/` will remove it or you can use the backspace key to edit the parent folder's name.*
4. Click the "**Commit new file**" button to create the folder and file and enter the folder.

*Note that you can apparently drag a folder with at least one item inside of it from your computer into the GitHub repository page, but I haven't tested that.*

#### Remote - create or manage GitHub milestones

You can create and manage milestones (goals) for your GitHub project:

1. Open your GitHub repository's main page.
2. Click **Issues** in the menu.
3. Click the **Milestones** tab next to the **New issue** button.

#### Remote - create or manage GitHub saved replies

GitHub's saved replies offer you a way to store snippets of boilerplate text and use them in any comment box on GitHub.

1. Click on your GitHub profile image.
2. Click **Settings** in the drop-down menu.
3. Click **Saved replies** in the **Code, planning, and automation** section in the left pane.
4. Type a title for your saved reply into the **Saved reply title** text box.
5. Type a reply into the **Write** text box.
6. Preview your reply in the **Preview** tab and go back to the **Write** tab to edit it if you'd like to make changes.
7. Click the **Add saved reply** button to store the saved reply.

Now, you'll be able to click the little curved arrow above any comment field on GitHub and select that reply by its title in the drop-down list that opens.

#### Remote - do a pull request on GitHub

1. Fork a remote repository by visiting the its main page and clicking the **Fork** button in the top right of the page. *Note that once the forking process is complete, you'll automatically be at the main page of your new forked repository.*
2. Open the branch you'd like to work on.
3. Create a new branch off of that branch with a name that lets you know what kind of change you're about to make. *Note that this will be a temporary branch that's for your use only and won't be copied to the remote repository that you forked.*
4. Make one or more changes to one or more files inside the new branch you just created with one of these methods:
	* Use the GitHub editor to make the changes, committing each one with a comment describing what you did.
	* Use the command line to clone your fork, make the changes, and push them to your fork.
5. Update the **CHANGELOG.rst** file to note the change(s).
6. Start a pull request with any **one** of these methods:
   * Click the **Compare & pull request** button above the file list.
   * Click the link in the note above the file list that tells you that this branch is ahead of the branch your changes will be made in.
   * Click **Pull requests** in the top menu and then click the **Compare and pull request** button.
   * Click **Pull requests** in the top menu and then click the **New pull request** button.
7. Check the information in the grey section at the top to make sure that:
   * the **base repository** is the remote repository that you forked
   * the **base** is the remote branch that you want to change
   * the **head repository** is your fork
   * the **head** or **compare** is the branch that contains your change(s)
8. Scroll down to review the change(s) you made to the file(s).
9. When you're satisfied with the settings and your changes, click the **Create pull request** button.
10. Verify that you have an **Able to merge** message from GitHub.
11. Type a meaningful title for the pull request into the top text box to give the remote repository's maintainer a quick idea of the reason for this pull request.
12. Type a detailed comment into the **Write** text box, if you like, letting the remote repository's maintainer know more about the change(s) that you've made.
13. Click the **Create pull request** button.
14. Once the remote repository's maintainer has merged the pull request into the remote repository, you can delete the temporary branch you had created in your fork in step 3 above or delete the entire fork:
    1. Go to the remote repository's main page.
    2. Click the **Pull requests** entry in the menu.
    3. Click **Closed** in the heading above the list of pull requests on that page.
    4. Click on the name of your pull request.
    5. Scroll down to the **Pull request successfully merged and closed** section at the bottom.
    6. Click the **Delete branch** button in that section to delete the branch and keep the forked repository or, if you no longer want the forked repository, click the **settings** link in that section.
    7. The next time you open the branch in your fork in which these changes were made, GitHub will notify you at the top of the file listing that your branch is out-of-date. This is because the changes you made in the temporary branch have now been made in the **base** branch you chose in the remote repository and they now need to be made in your fork so the two repository's can be identical. To synchronize them:
        1. Click the **Sync fork** button to the right of that message.
        2. Click the **Update branch** button.

*As an example, if you created the **foo** branch off of the **develop** branch in your fork, changed the contents of its **readme.txt** file, did a pull request, chose **develop** as the **base**, and chose **foo** as the **head**, the **readme.txt** file in the remote repository's **develop** branch will be the file that changes. The remote repository will not get a copy of your **foo** branch and you'll be able to delete the **foo** branch once the pull request is merged into the remote repository.*

*If, instead of following the above steps and editing a file in your fork, you attempt to edit a file in a repository that you don't have push rights to (the AutoKey repository), when you commit the change(s), GitHub will automatically offer to create a branch with the default name of **patch-1** (or **patch-2**, etc., depending on whether other patch branches exist). You can edit the branch name if you like. That branch gets created in the repository you don't have push rights to (in this case, the AutoKey repository) when you do a pull request and it's accepted, and it's the branch that's used as the source for the pull request. Your fork will then get a copy of that branch the next time you sync the branches. If you then view the branches in your fork, you'll see that you own that branch. Once the pull request is accepted, you can delete the branch from your fork and it will be automatically deleted from the remote repository that you don't have push access to without a pull request.*

#### Remote - enable the GitHub issue tracker

1. Log into your GitHub account.
2. Select your repository.
3. Open the **Settings** tab.
4. Open the **Options** tab.
5. Scroll down to the **Features** section.
6. Activate the issue tracker by putting a check-mark in the **Issues** box.

#### Remote - fork a GitHub repository

1. Go to the repository's main page.
2. Click the **Fork** button in the top right corner.
3. Choose an owner for the fork if you like (it will be you by default).
4. Change the name of the fork if you like (it will be the original repository's name by default).
5. Change the description if you like (it will be the original repository's description by default).
6. **Uncheck** the **Copy the master branch only** box (*this is important*).
7. Click the **Create fork** button.

#### Remote - pin a gist or repository to your GitHub home page
If you'd like quick access to one of your gists or repositories from now on:

1. Go to your [GitHub](https://github.com) home page.
2. Click `Customize your pins` in the right center of your home page.
3. Put a check-mark in the box next to the gist or repository you'd like to pin.
4. Click the `Save pins` button.

#### Remote - edit a repository on GitHub (TODO: DELETE ME)
When your tests are done and you're satisfied with your local code, open the **develop** branch of your fork on GitHub and use the GitHub editor to make your changes to the file(s) on GitHub that you changed inside of the clone in your virtual machine.

#### Remote - revert a commit on GitHub

This must be done on the command line.

#### Remote - revert a pull request on GitHub

1. Open your repository on GitHub.
2. Click the "Pull requests" tab.
3. Click the pull request that you'd like to revert.
4. Click the "Revert" button. Note that this will create a new pull request that reverts the changes.
5. Merge the resulting pull request.

#### Remote - update the change log (TODO: DELETE ME)
Add one or more lines to the `CHANGELOG.rst` file in the **develop** branch of your fork on GitHub describing the change(s) you've made to the code.

#### Remote - delete a repository from GitHub

Once your code has been accepted and merged into a project, you can delete the fork. Deleting a fork will have no effect on the project it was forked from.

1. Go to your local repository's (the fork's) main page.
2. Click on **Settings** in the top menu.
3. Scroll to the bottom of the page to the **Danger Zone** section.
4. Click the **Delete this repository** button.
5. Type in your GitHub username and repository's name at the prompt.
6. Click on the **I understand the consequences, delete this repository** button.

#### Remote - search a GitHub repository's wiki for pages containing the specified string

All of these examples are searching for **foo** in the wiki and you can change that to whatever you'd like to search for:

* Put this into the search bar at the top left corner of Github: `user:autokey foo`
* Or put this into the search bar: `user: autokey repo:autokey foo`
* Or put this into the search bar: `repo:autokey/autokey foo`
* Or use this link: <https://github.com/search?type=Wikis&q=repo%3Aautokey%2Fautokey+foo>

#### Remote - search a repository's wiki for pages updated within the specified date range

To search by last-updated date, the **updated** qualifier matches wiki pages that were last updated within the specified date range. When you search for a date, you can use greater than, less than, and range qualifiers to further filter results. For more information, see the [Understanding|the search syntax](https://docs.github.com/en/search-github/getting-started-with-searching-on-github/understanding-the-search-syntax) page. Some example searches:

* Match wiki pages containing the word "foo" that were last updated after 2016-01-01: `foo updated:>2016-01-01`
* Match wiki pages that were last updated before 2016-01-01: `repo:autokey/autokey updated:<2016-01-01`
* Match wiki pages that were last updated after 2016-01-01: `repo:autokey/autokey updated:>2016-01-01`
* Match wiki pages that were last updated on or before 2016-01-01: `repo:autokey/autokey updated:<=2016-01-01`
* Match wiki pages that were last updated on or after 2016-01-01: `repo:autokey/autokey updated:>=2016-01-01`

******************************************************************************************************************************

## Notes

* The **.tox** directory grows each time the **tox** command is run. It can be [manually removed, removed internally if its output contains no errors, or destroyed and recreated each time](https://stackoverflow.com/questions/59563746/how-to-clean-a-tox-environment-after-running).
* Tagged releases merged into develop, beta, and master will automatically be built.
* `git fetch` downloads the changes from the remote repository to your local repository.
* `git pull` downloads the changes from the remote repository to your local repository and merges them into your current branch.

#### See also

* **apt packages**: replace **foo** with a package name: [https://packages.ubuntu.com/search?suite=jammy&arch=any&searchon=names&keywords=foo](https://packages.ubuntu.com/search?suite=jammy&arch=any&searchon=names&keywords=foo)
* **Exit codes for the `tox` command**: [https://docs.pytest.org/en/stable/reference/reference.html#exitcode](https://docs.pytest.org/en/stable/reference/reference.html#exitcode)
* **GitHub available images**: Do a search for **latest** on here to find out which version of Ubuntu is currently considered the latest: [https://github.com/actions/runner-images#available-images](https://github.com/actions/runner-images#available-images) Then check its current Python or other software versions, check for announcements, etc.
* **GitHub Python Versions Manifest**: Do a search for 22.04 and find all hits to let you know which are the lowest and highest versions of Python supported for that Ubuntu release: [https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json](https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json)
* **Python packages**: [https://pypi.org](https://pypi.org)
* **Ubuntu manifest - current**: [https://releases.ubuntu.com/22.04/ubuntu-22.04.2-desktop-amd64.manifest](https://releases.ubuntu.com/22.04/ubuntu-22.04.2-desktop-amd64.manifest)
* **Ubuntu manifests - all**: Click on any old or current release to find and download its manifest from: [https://old-releases.ubuntu.com/releases/](https://old-releases.ubuntu.com/releases/)
