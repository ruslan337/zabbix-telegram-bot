#!/bin/python3

token='123456789:123456789abc-defghijkLMNOPQRSTuvwxy' # Telegram Bot token
allowed_chats=('11111111',) # List of allowed chats for daily reports
zabbix_server='http://zabbix-host/zabbix' # Zabbix URL
zabbix_user='bot-idiot' # Zabbix user
zabbix_pass='bot-idiot' # Zabbix users password
daily_report_time_hour=17 # What time should daily reports run (hour)
daily_report_time_minute=17 # What time should daily reports run (minute)
cityname="Komek" # Name of city
host_servers=() # List of host servers. Need if you have some daily reports.
