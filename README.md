# Personal Punch Clock
Personal Punch Clock is a bare-bones command-line punch clock.

## Installation
You must have Python 3.4 or newer installed.
Install the dependencies:
```shell
pip install -r requirements.txt
```
Rename the file `punch_clock.py` to `punch-clock`,
make it executable,
and copy it to a directory which your operating system searches
for executable files (e.g., `$HOME/bin`).


## Usage
Display your total work time and whether you are clocked in or out:
```shell
punch-clock
```

Punch in:
```shell
punch-clock --in
```

Punch out:
```shell
punch-clock --out
```

Delete the stored clock punches:
```shell
punch-clock --reset
```

## License
Personal Punch Clock is licensed under the Apache License, Version 2.0.
