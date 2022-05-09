## Introduction ##
AutoKey scripts accept most Python code. AutoKey also offers some custom API functions that can be used in scripts. For specific details on the custom functions available to AutoKey scripts, see the [API reference](https://autokey.github.io).

## Example scripts ##
These pages contain some example scripts and user-contributed scripts to demonstrate some of the basic and advanced capabilities of AutoKey's scripting service:
  * [Contents list of all these contributed files](https://github.com/autokey/autokey/wiki/Contents-of-contributed-script-files)
  * [Advanced Scripts](https://github.com/autokey/autokey/wiki/Advanced-Scripts)
  * [Basic Scripts](https://github.com/autokey/autokey/wiki/Basic-Scripts)
  * [Contributed Scripts 1](https://github.com/autokey/autokey/wiki/Contributed-Scripts-1)
  * [Contributed Scripts 2](https://github.com/autokey/autokey/wiki/Contributed-Scripts-2)
  * [Contributed Scripts 3](https://github.com/autokey/autokey/wiki/Contributed-Scripts-3)
  * [Mouse Control](https://github.com/autokey/autokey/wiki/Mouse-Control)

## Contributing scripts ##
Feel free to use the scripts for your own purposes. However, if you significantly modify them or come up with something new as a result of using them, please post them in [one of our community platforms](https://github.com/autokey/autokey/wiki/Community) so one of the wiki moderators can add them here for all to benefit.

All submitted scripts are publicly licensed as [GNU GPL v3](http://www.gnu.org/licenses/gpl.html)

## Porting your scripts from Python 2 to Python 3 ##
  * Changes were made to source code to keep the scripting API stable. The ``system.exec_command()`` returns a string. But if you use functions from the standard library, you will have to fix that, as your script runs on a Python 3 interpreter. For example, expect ```subprocess.check_output()``` to return a bytes object.
  * The [2to3](http://docs.python.org/dev/library/2to3.html) Python program can be used to automatically translate your source code from Python 2 to Python 3.
  * Some guides on porting code to Python 3:
    * http://python3porting.com/
    * http://diveintopython3.problemsolving.io/porting-code-to-python-3-with-2to3.html