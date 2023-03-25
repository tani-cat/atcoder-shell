# AtCoder Shell

This is the shell library to execute AtCoder submission on your commandline, for Python/PyPy user.

## Basic operation

If you want to know more information about commands, execute `acsh help`.
(Note that the command results are output in Japanese.)

### 1. Installation

```shell
pip install acshell
```

### 2. Login

```shell
acsh login
# acsh lg
```

Your account credentials are stored for a certain period of time.

### 3. Create "Contest folder"

```shell
acsh load agc001
# acsh ld agc001
```

The "contest folder" of specified contest is created where you are currently. Each task folder is generated in the contest folder.

### 4. Write your code

Implement the answers in the file like `agc001_a.py` created in the folder for each task.

### 5. Run your codes with published testcases

Confirm the formats of the command arguments below.

```shell
acsh test [task] [num] [lang]
acsh check [task] [lang]
# acsh t
# acsh c
```

| option | required | value format |
| :-- | :-: | :-- |
| task | Yes | task code such as `A`, `B` |
| num | Yes (in `test`) | number of testcase as integer |
| lang | x | language(`python` or `pypy`) |

### 6. Submit your codes

Confirm the formats of the command arguments below. Unlike the test running, you have to specify which language you submit codes as.

```shell
acsh submit [task] [lang]
# acsh s
```

| option | required | value format |
| :-- | :-: | :-- |
| task | Yes | task code such as `A`, `B` |
| lang | **Yes** | language(`python` or `pypy`) |

### 7. Confirm results of your submission

```shell
acsh recent  # for recent submission
acsh status  # for your contest scores
# acsh rc
# acsh rs
```

## Additional Operations

### Setup your cheat sheets

Follow the steps below to use your own prepared cheat-sheet codes,
Please check the arguments with the `acsh help` command.

#### Setup

1. open the config folder by executing `acsh edit-cheat` / `acsh ec`.
2. write your cheat sheets, and place the folder opened.

#### Usage

1. execute `acsh add-cheat <task_code> <cheat_name (without extension)>` so add the specified cheat file in the task folder.
2. write `from <filename> import <func/class name>` in your code.
3. The cheat files will be merged with main code file when you submit.

### Setup initial codes

If you want to set a template code, add `initial.py` in the cheat-sheet setup shown above.

### Pyenv management

If you want to run codes by pypy, you should use pyenv for python version management.

1. Install the latest version of `3.8.*` and `pypy3.7-7.3.*`.
2. execute the command below.

```shell
pyenv A B C
```

- A: The Python version you usually use
- B: The version of installed `3.8.*`
- C: The version of installed `pypy3.7-7.3.*`
