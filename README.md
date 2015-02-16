PiperBot
========

A multithreaded, multi-server IRC bot written in Python.

Pre-requisites
--------------

 * Python (version >= 3.3)
 * MongoDB for the mongo backend.
 
Running
-------

To run PiperBot, edit the `settings.json` file with your own settings, and do

```
python3.3 piperbot.py settings.json
```

Plugins
-------

List of available plugins and their funtion

### `general`
General functions of the bot.
  - `@command("reverse")` : Reverse piped text
  - `@command("echo")` : Print piped text
  - `@command("caps")` : UPPERCASE piped text
  - `@command("lower")` : lowercase piped text
  - `@command("rot13")` : Ceaser shift 13 piped text
  - `@command("binary")` : Attempt to print a number in binary notation
  - `@command("hex")` : Attempt to print a number in hexadecimal notation
  - `@command("list")` : List the loaded plugins
  - `@command("sed")` : Does a sed replace on text. Searches for a match for the
	1st operand of the regex in previous messages seen reverse chronologically.

### `markov`
Talks.
