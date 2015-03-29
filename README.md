PiperBot
========

A multithreaded, multi-server IRC bot written in Python.

Pre-requisites
--------------

 * Python 3.4
 * MongoDB for the mongo backend.
 * dill for various things related to pickling and multiproccess
 * dateutil for reminders
 * requests for sane html stuff
 * lxml for sane html parsing
 * patience it might not work completely...
 
Running
-------

To run PiperBot, edit the `settings.json` file with your own settings, and do

```
python3.4 piperbot.py settings.json
```

Plugins
-------

List of available plugins and their funtion

### `general`
General functions of the bot.
  - `#echo <text>` : echo format the text with any piped data, or just echo the text
  - `#reverse <text>` : reverse piped data or the text
  - `#caps <text>` : UPPERCASE piped text
  - `#lower <text>` : lowercase piped text
  - `#rot13 <text>` : Ceaser shift 13 piped text
  - `#list` : List the loaded plugins
  - `#sed <sed pattern> <text>` : Does a sed replace on text. Searches for a match for the 1st operand of the regex in previous messages seen reverse chronologically.
  - `#help <command>` for more in-depth help on a command
  - lots more

### `markov`
Talks.

### `Seval`
a meta circular evaluator, or a python interpreter written in python.
bit complicated!
