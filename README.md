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
 * BeautifulSoup4 for sane html parsing (see [this](./doc/windows.md) for information on `lxml` for Windows)
 * PyPDF2 for reading PDF titles
 * patience it might not work completely...
 
Running
-------

To run PiperBot, edit the `settings.json` file with your own settings, and do

```
python3.4 piperbot.py settings.json
```

Piping
------

One of the main features of PiperBot is the piping functionality. Different
commands may be joined together, for example:

```
#echo Hello, World! || sed s/World/You/
```
Outputs: `Hello, You!`.

Commands should put their output in a variable called `message.data`. This
variable may be accessed from within seval.

```
#echo 12 || > int(message.data) * 2
```
Outputs: `24`.


Aliasing
--------

With such a large set of tools for building commands, it makes sense to alias
them into short hand commands for later calling. For example:

```
#alias ping = echo pong

#ping
```
Outputs: `pong`.

Aliases may be piped commands too.

```
#alias o = sed s/([aiue])/\1/i || sed s/[aiue]/o/g || sed s/[AIUE]/O/g
Hello, World
#o
```
Outputs: `Hollo, World`.



Plugins
-------

Notice: `#` is the default "command character". This is required for the 1st
invokation of pipable command. Commands after pipes shall not use `#` in their
calling.

```
#nicks || 
 > message.data + ["Pengwin","C"] || 
 karma || 
 filter message.data[1] != 0 || 
 > {"d":json.dumps(sorted(message.data,reverse=True,key=lambda x: x[1]))} || 
 burl https://graymalk.in/ircstats/karma-graph.html? || 
 shurl
```

Note also that new lines are being added. These are only for readablity.
Piperbot will not allow for line continuations, and you must strip new lines
when building commands.

List of available plugins and their funtion:

### `general`
General functions of the bot.
  - `#echo <text>` : echo format the text with any piped data, or just echo the 
    text
  - `#reverse <text>` : reverse piped data or the text
  - `#caps <text>` : UPPERCASE piped text
  - `#lower <text>` : lowercase piped text
  - `#rot13 <text>` : Ceaser shift 13 piped text
  - `#list` : List the loaded plugins
  - `#sed <sed pattern> <text>` : Does a sed replace on text. Searches for a
    `#match for the 1st operand of the regex in previous messages seen reverse
    `#chronologically.
  - `#help <command>` for more in-depth help on a command
  - lots more

### `markov`
Talks.
  - `#talk to <nick>` : Talk to someone
  - `#talk about <topic>` : Talk about a given topic

The bot will also respond if directly referenced in a message.
```
17:40 < graymalkin> PiperBot: hi
17:40 < PiperBot> graymalkin: on your tongue too
```

### `seval`

A meta circular evaluator, or a Python interpreter written in Python. A little
bit complicated!

`seval` may be invoked with `#>` or `#seval`.

Basic usage:
 - `#> 1+1`  : It will do some maths
 - `#> [x+1 for x in [1,2,3]]` : List comprehensions
 - `#> a = 5; b = a + 2;` : Local assignments
 - `#> lambda x: x*2` : Lambdas

A selection of standard python functions are available. For full documentation
see [here](./doc/seval.md).
