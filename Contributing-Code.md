Autokey is currently undergoing large changes on its `develop` branch. If you are writing code for anything other than small bugfixes, you should base off that branch. It is very far ahead of `master`, and has tidier code.

`develop` is the only branch with a working test framework, which you should do your best to use for code you contribute. Currently test coverage is very low, but that should not be an excuse for making it worse---please include tests for your code. Feel free to ask for help with writing tests in your PR comments.

Finally, please read [CONTRIBUTERS.rst](https://github.com/autokey/autokey/blob/develop/CONTRIBUTORS.rst) on that same branch.

--- BlueDrink9, 2020-10-06

[![Open Source Helpers](https://www.codetriage.com/autokey/autokey/badges/users.svg)](https://www.codetriage.com/autokey/autokey)

## Basic GitHub Workflow

These steps take you through the basic workflow for using GitHub in your browser to contribute to the AutoKey project.

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
    7. The next time you open the branch in your fork in which these changes were made, GitHub will notify you at the top of the file listing that your branch is out-of-date. This is because the changes you made in the temporary branch have now been made in the **base** branch you chose in the remote repository and they now need to be made in your fork so the two repository's can be identical. To synchronize them:
        1. Click the **Sync fork** button to the right of that message.
        2. Click the **Update branch** button.

*As an example, if you created the **foo** branch off of the **develop** branch in your fork, changed the contents of its **readme.txt** file, did a pull request, chose **develop** as the **base**, and chose **foo** as the **head**, the **readme.txt** file in the remote repository's **develop** branch will be the file that changes. The remote repository will not get a copy of your **foo** branch and you'll be able to delete the **foo** branch once the pull request is merged into the remote repository.*

*If, instead of following the above steps and editing a file in your fork, you attempt to edit a file in a repository that you don't have push rights to (the AutoKey repository), when you commit the change(s), GitHub will automatically offer to create a branch with the default name of **patch-1** (or **patch-2**, etc., depending on whether other patch branches exist). You can edit the branch name if you like. That branch gets created in the repository you don't have push rights to (in this case, the AutoKey repository) when you do a pull request and it's accepted, and it's the branch that's used as the source for the pull request. Your fork will then get a copy of that branch the next time you sync the branches. If you then view the branches in your fork, you'll see that you own that branch. Once the pull request is accepted, you can delete the branch from your fork and it will be automatically deleted from the remote repository that you don't have push access to without a pull request.*
