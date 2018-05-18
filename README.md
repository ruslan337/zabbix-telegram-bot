# zabbix-telegram-bot
Telegram-bot interface for zabbix
# Dependencies:
* Python library for Telegram Bot API - https://github.com/python-telegram-bot/python-telegram-bot <br />
* Zabbix API in Python - https://github.com/gescheit/scripts/tree/master/zabbix <br />
* Python HTTP requests library - http://docs.python-requests.org/en/master/ <br />

<b>You can install all dependencies running:</b><br />
* pip3 install python-telegram-bot <br />
* pip3 install requests
* pip3 install zabbix-api
# How to use
1) Clone this project, install dependencies
2) Copy file config_template.py to config.py, edit config.py
3) Edit zabbix-bot.service, copy it to /etc/systemd/system/
4) run systemctl daemon-reload, systemctl start zabbix-bot
# ToDo list:
* include logger
