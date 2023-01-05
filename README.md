# Introduction 
Pulls data from Edsembli and Atrieve which is dumped into an SQL Databsae.  The data is iterated through to create/modify/delete users accounts in Active Directory and uploads are created for Destiny Patrons 

# Getting Started
## Install Python
* Install the lastest version of python 3 (tested with Python 3.11.1) from https://python.org
* Install the required python libraries with pip install -r requirements.txt
* Install the chromedriver matching the version of Chrome you have on your computer.  This needs to be placed somewhere this is one of your system paths such as: %SystemRoot%\system32 or you need to add the location of it to this to your PATH in the Eviromental Variables (Only required for Atrieve Integration).  It can be downloaded from here: https://chromedriver.chromium.org/downloads

## Install Requirements
* Python 3.9 or above (tested with 3.11.1)
* Google Chrome
* Chromedriver (matching the installed version of Chrome)

# Build and Test
* Running from Visual Code
* or run python.exe .\Identity Automation\main.py'