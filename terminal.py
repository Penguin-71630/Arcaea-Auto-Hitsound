import subprocess, sys, os

# subprocess.call("run shell script here", shell=True)

def system(command: str, shell: str="/bin/bash"):
    subprocess.call(command, shell=True, executable=shell)

def coloredEcho(color: str, message: str):
    system("echo -e ${%s}\"%s\"${COLOREND}" % (color, message))

def startSTEP(currentSTEP: int):
    coloredEcho("BG_BLUE", "STEP {_step_}: {_stepMessage_}".format(
        _step_=currentSTEP,
        _stepMessage_=STEPS[currentSTEP - 1]
    ))

def sysInit():
    system('export COLOREND="\x1b[0m"')
    system('export BLACK="\x1b[30m"')
    system('export RED="\x1b[31m"')
    system('export GREEN="\x1b[32m"')
    system('export YELLOW="\x1b[33m"')
    system('export BLUE="\x1b[34m"')
    system('export PURPLE="\x1b[35m"')
    system('export CYAN="\x1b[36m"')
    system('export WHITE="\x1b[37m"')
    system('export GRAY="\x1b[90m"')
    system('export BG_BLACK="\x1b[40m"')
    system('export BG_RED="\x1b[41m"')
    system('export BG_GREEN="\x1b[42m"')
    system('export BG_YELLOW="\x1b[43m"')
    system('export BG_BLUE="\x1b[44m"')
    system('export BG_PURPLE="\x1b[45m"')
    system('export BG_CYAN="\x1b[46m"')
    system('export BG_WHITE="\x1b[47m"')
    system('export BG_GRAY="\x1b[100m"')
