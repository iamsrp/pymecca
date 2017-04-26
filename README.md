# pymecca
UNOFFICIAL Python code for controlling the Meccano Meccanoid

This is some simple Python code for controlling the Meccanoid over Bluetooth. It works on the Raspberry Pi 3. You will need to install the Bluetooth software on your Raspberry Pi and probably other Python infrastructure:
  * sudo apt-get install python-bluez
  * sudo apt-get install ipython
  * sudo apt-get install python-dev
  * sudo pip install pygatt

You will also need to determine the MAC address of your Meccabrain's Bluetooth connection. Something like "sudo hcitool lescan" should do the job.

This is an unofficial, and unsanctioned, API for controlling the Meccanoid robot.
