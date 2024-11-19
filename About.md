## About AutoKey
* [AutoKey](https://github.com/autokey/autokey) is a Python 3 automation utility for Linux and X11 with GTK and Qt versions.
* AutoKey allows you to write **actions** ([phrases](https://github.com/autokey/autokey/wiki/Phrases) and [scripts](https://github.com/autokey/autokey/wiki/Scripting)) that can perform text-expansion or run scripts for you automatically when you trigger them with hotkeys or typed abbreviations.
* AutoKey is fully customizable and you can use it to automate pretty much any computer behaviors or tasks that you can think of.
* The current version of AutoKey is available in the Debian and Ubuntu repositories, so you can install it with your package manager, although other [installation](https://github.com/autokey/autokey/wiki/Installing) options are also provided.
* AutoKey has an active [community](https://github.com/autokey/autokey/wiki/Community) on a variety of platforms. To get started, join us in our [wiki](https://github.com/autokey/autokey/wiki), our [support forum](https://groups.google.com/forum/#!forum/autokey-users), or our [Gitter platform](https://gitter.im/autokey/autokey).
* The project is active.
* New developers or random [contributions](https://github.com/autokey/autokey/wiki/Contributing) to the code in the form of pull requests are always welcome.
* AutoKey participates in [Opire's reward platform](https://github.com/autokey/autokey/wiki/Contributing#donations) as an optional way for anyone to provide incentives for development.
* [Issue reports](https://github.com/autokey/autokey/issues) and contributions to the discussions under existing issues are always welcome. Your feedback helps to improve AutoKey.
* If you're new to AutoKey, the [Beginners' Guide](https://github.com/autokey/autokey/wiki/Beginners-Guide) will get you started and the [FAQ](https://github.com/autokey/autokey/wiki/FAQ) page has answers to common questions.

## How AutoKey works
### About AutoKey actions
* AutoKey [phrases](https://github.com/autokey/autokey/wiki/Phrases) are like a very powerful auto-type/auto-correct feature. Phrases can contain text and also optionally some phrase-specific API calls in the form of [macros](https://github.com/autokey/autokey/wiki/Phrases#available-macros) that can perform automated actions. The contents of the phrase can be inserted in the active window or used as replacement for text that you've typed to trigger the phrase.
* AutoKey [scripts](https://github.com/autokey/autokey/wiki/Scripting) are written in Python and can emit keyboard and mouse events to perform most tasks that you can do manually with your keyboard and mouse. Most applications can't tell it's not you typing and clicking, so they can be controlled by AutoKey even if they don't have any provision for that. An API is provided to generate keyboard and mouse events and for some desktop/window-manager interactions. AutoKey scripts, for most common uses, can be written with a minimal knowledge of Python. However, if you do know more, you can easily put it to use to do just about anything.

### Trigger AutoKey actions
Actions can be triggered by a **hotkey** or when a specific **abbreviation** is typed:
* An **abbreviation** (which is a string of text) can be assigned to an action so that the action runs whenever you type that text in the active window.
* A **hotkey** (which can be a single key or a key-combination) can be assigned to an action so that the action runs whenever that hotkey is pressed in the active window.

### Customize AutoKey actions:
Actions can be customized to fine-tune their behavior:
* An **abbreviation** can be customized with a selection of options:
	* Remove the typed abbreviation.
	* Omit the trigger character.
	* Match the case of the phrase to the typed abbreviation.
	* Ignore the case of the typed abbreviation.
	* Trigger when typed as part of a word.
	* Trigger immediately without requiring a trigger character.
* A **window filter** can be defined for any action so that the hotkey or abbreviation that triggers the action will be ignored unless the currently-active window matches its filter.
