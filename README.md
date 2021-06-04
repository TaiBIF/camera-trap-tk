# Camera Trap Desktop

tkinter GUI

## Development

### Requirements

- Python 3.6+

**Dependency**
- Pillow
- tksheet
- requests
- boto3
- pyinstaller (for build win exe)

### Usage

1. Install packages

use poetry to manage python environment

```sh
$ poetry install
$ poetry shell
```

2. run

```sh
$ python ./src/app.py
```
use custom ini file

```sh
$ python ./src/app.py -i my-dev.ini
```

## Build

```sh
$ pyinstaller.exe --onefile -F .\src\app.py --clean
```

提供 config.ini file, 注意: `account_id`,
