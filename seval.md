# Safe EVALuator

`seval` is a meta-circular Python Interpreter. It is written in Python, and it 
will interpret a strict subset of Python.

This gives users a python shell accessible over IRC, which is safe and won't
destroy your machine. Hopefully.

`seval` is implemented in
[this](https://github.com/graymalkin/piperbot/blob/master/plugins/seval.py)
file.

It has all the same opperations you'd find in ordinary Python maths, with the
exception of compound oporators like `+=` and `<<=`.

## Binary Operations
 - `a + b` 
 - `a - b` 
 - `a * b`
 - `a / b`
 - `a % b`
 - `a ** b`
 - `a << b`
 - `a >> b`
 - `a | b`
 - `a ^ b`
 - `a & b`
 - `a // b`

## Unary Operations
 - `~a`
 - `not a`
 - `+a`
 - `-a`

## Comparisons
`seval` supports Python style comparisions and inline `if` statements. E.g.

```python
pass() if a==b else fail()
```

 - `a == b` : a value equals b
 - `a != b` : a does not value equal b
 - `a < b` : a.compare(b) < 0 
 - `a <= b` : a.compare(b) <= 0
 - `a > b` : a.compare(b) > 0
 - `a >= b` : a.compare(b) >= 0
 - `a is b` : a reference equals b
 - `a is not b` : a does not reference equal b
 - `a in b` : a contains b
 - `a not in b` : a does not contain b

## Lists and Slicing
`seval` supports Python lists and slices.

```python
a = [1, 2, 3]
b = a[-1]
b == 2 
#True
```

`seval` also allows for ranges. These are lazily evaluated ranges, though.

```python
a = range(10)
a
# range(0,10)
[x for x in a]
# [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

## Compounding Statements

`seval` uses C style semicolons to allow for compound statements. e.g.

```python
a = 10; a = a*2; a
# 20
```

## Reading in data

PiperBot passes data around in `message.data`. This may be read from inside
`seval`.

```
#echo Foo || > message.data
```
Outputs: `'Foo'`.


```
#nicks || > message.data
```
Outputs: `['List', 'of', 'nicks', 'in', 'the', 'channel']`

You can build up quite interesting commands like this.

```
#nicks || karma || > json.dumps(sorted(message.data, key=lambda x: x[1], reverse=True))
```
Outputs: `[['List', 230], ['of', 134], ['sorted', 121], ['karma', 67], ['values', 12]]`

There are other plugins which will build that this kind of data into a URL and
even shorten it. From the example command given in the [README](./README.md):
```
#nicks || 
 > message.data + ["Pengwin","C"] || 
 karma || 
 filter message.data[1] != 0 || 
 > {"d":json.dumps(sorted(message.data,reverse=True,key=lambda x: x[1]))} || 
 burl https://graymalk.in/ircstats/karma-graph.html? || 
 shurl
```

Breaking this commands down:
 1. Take a list of all nicks
 1. Add "Pengwin" and "C", so they're always included even in channels they're 
    not present in
 1. Get the karma for each nick
 1. Strip the karma values of 0
 1. With `seval` output a dict where the karma data is sorted by the 2nd key 
    (the karma value) and made into a json string
 1. Build the dictionary into a URL
 1. Shorten the URL using a URL shortening service (bit.ly)

Yeilding a URL like this: http://bit.ly/1MuvngY

