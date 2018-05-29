# DuetMonitor

Inspired by https://gist.github.com/Kriechi/63c29ed4ad860744107ee4a1b5cf10a2 i've created this script

## Goals
* Send notifications to pushover when print is finished
* Send an image of the final print to Pushover
* Count energy used for the print
* Write print statistics to a CSV file for later use

## Installation
**NOTE:** Currently i'm running the script on a raspberry pi. Means the installation instruction is tested on linux using systemd only

* Put the script somewhere on the raspberry. e.g. ~/bin/
* Adopt *duetmonitor.cfg* and move it to ~/.duetmonitor.cfg
* Copy *duetmonitor.service* to /lib/systemd/system/
* Change permissions
  * 'chmod u+x ~/bin/duetmonitor.py'
  * 'sudo chmod 644 /lib/systemd/system/duetmonitor.service'
* Tell systemd about the new service => 'sudo systemctl daemon-reload'
* Activate service => 'sudo systemctl enable duetmonitor.service'
* Start service => 'sudo systemctl start duetmonitor.service'
