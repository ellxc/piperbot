# PiperBot Examples

## Seval

Many seval functions are python 1 liners. These are terifically unreadable, so
here are some examples with explainations.


### Rainbow

```py
lambda x=None: ''.join(' ' if c == ' ' else ('\3' + str(n) + ('\2\2' + c if c in '0123456789' else c)) for (n, c) in zip(itertools.cycle([5,4,7,3,12,6,13]), x or 'rainbow'))
```

Rotate through each of the colour codes and prepend `\3` and the colour code to
each character of the string. If the charcater might interfer with the colour
code then add a `\2\2` following it.

This shows off that lambda functions may have default values, here x defaults to
`None`. This means that when you call `rainbow()` you'll get "rainbow" as a
default response.

This can be turned into an alias...

```
#alias rainbow = echo {} || > ''.join(' ' if c == ' ' else ('\3' + str(n) + ('\2\2' + c if c in '0123456789' else c)) for (n, c) in zip(itertools.cycle([5,4,7,3,12,6,13]), message.data or 'rainbow')) || echo
```

Note that I've stripped out the lambda, and I'm not calling the lambda which was
saved earlier. The reasoning for this is to keep the alias dependency free,
incase the lambda is klobbered or lost for whatever reason.


### size_str

```py
size_str = lambda x:
  '{:.02f}{}'.format( # Formats the number to 2 decimal places
    round((x/math.pow(1024, math.floor(math.log(x, 1024)))), 2), # Calculates the number
    [' B', ' KiB', ' MiB', ' GiB', 'TiB', ' PiB', 'EiB'][round(math.ceil(math.log(x, 1024)))]) # Calculates the unit
```

Convert a raw number of bytes into a human readable size string.
