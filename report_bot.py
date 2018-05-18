#!/bin/python3

# Written by Ruslan Murzalin (rus_m_ok@mail.ru)

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# DEPENDENCIES:

# Zabbix API in Python - https://github.com/gescheit/scripts/tree/master/zabbix
# Python library for Telegram Bot API - https://github.com/python-telegram-bot/python-telegram-bot
# Python HTTP requests library - http://docs.python-requests.org/en/master/
# Python library to work with JIRA APIs - https://jira.readthedocs.io/en/master/

# You can install all dependencies running:
# pip3 install python-telegram-bot
# pip3 install requests
# pip3 install zabbix-api
# pip3 install jira

from config import *
from telegram.ext import Updater, CommandHandler, Job
from zabbix_api import ZabbixAPI
from datetime import datetime, time
import requests, urllib

def parse_host(user_host):
    monitored_hosts=zapi.host.get({'monitored_hosts' : True,'extendoutput' : True})
    result_host='-'
    hc=0
    user_host=user_host.upper()
    for host in monitored_hosts:
        i=0
        h=False
        hostname=host["name"].upper()
        for c in user_host:
            j=i
            h=False
            while (j<hostname.__len__()):
                if c==hostname[j]:
                    h=True
                    break
                j+=1
            i=j
        if h:
            result_host=host
            hc+=1
    if hc>1:result_host='-'
    return result_host

def parse_resource(resource):
    try:
        result_resource={"D":"Disk space usage /", "A":"ALL", "C":"CPU utilization", "M":"Memory usage", "P":"CPU load", "R":"Memory usage"}[resource.upper()[0]]
    except:
        result_resource="ALL"
    return result_resource

def parse_period(period):
    a=period.__int__()
    return a

def show_graph(bot, update):
    global cookie
    message=''
    is_valid=True
    req_period=0
    req_host=0
    req_resource=0
    args=update.message.text.split()
    args.append(3600)
    if update.message.text.split().__len__()>0:
        req_host=parse_host(args[1])
        try:
            req_resource=parse_resource(args[2])
        except:
            req_resource='ALL'
        try:
            req_period=parse_period(args[3])
        except:
            req_reriod=3600
        if req_host=='-': is_valid=False
    else:
        is_valid=False
    if is_valid:
        req_graph=zapi.graph.get({"hostids":req_host["hostid"], "filter":{"name":req_resource}})[0]
        req_gitem=zapi.graphitem.get({"graphids":req_graph["graphid"]})
        chart_url=zabbix_server+"/chart3.php?period=3600&name={0}".format(urllib.parse.quote_plus(req_graph["name"]))
        chart_url+='&width={0}&height={1}&graphtype={2}'.format(req_graph["width"],req_graph["height"],req_graph["graphtype"])
        cid=0
        for gitem in req_gitem:
            chart_url+='&items[{0}][itemid]={1}&items[{0}][sortorder]={2}&items[{0}][drawtype]={3}&items[{0}][color]={4}'.format(\
                        cid, gitem["itemid"], gitem["sortorder"], gitem["drawtype"], gitem["color"])
            cid+=1
        response=requests.get(chart_url, cookies=cookie, verify=True)
        res_graph=response.content
        ps=requests.post('https://api.telegram.org/bot{0}/sendPhoto'.format(token),params={"chat_id":update.message.chat_id}, files={"photo":res_graph})
    else:
        message="""command format is '/graph SERVERNAME RESOURCENAME [PERIOD]'
Where: 
- SERVERNAME is server name from '/lsser' command;
- RESOURCENAME is 'cpu', 'mem', 'disk';
- PERIOD is period of graph in seconds, default is 3600.
All parameters are case insensitive
"""
        bot.sendMessage(chat_id=update.message.chat_id, text=message, parse_mode="HTML")

def show_lsser(bot, update):
    monitored_hosts=zapi.host.get({'monitored_hosts' : True,'extendoutput' : True})
    result=""
    for host in monitored_hosts:
        result+=host["name"]+"\n"
    bot.sendMessage(chat_id=update.message.chat_id, text=result, parse_mode="HTML")

def show_list(bot, update):
    monitored_hosts=zapi.host.get({'monitored_hosts' : True,'extendoutput' : True})
    message=''
    for host in monitored_hosts:
        trigger_list=zapi.trigger.get({"hostids":host["hostid"], "filter":{"value":"1"}})
        if trigger_list.__len__()>0:
            message+="<b>------------"+host["name"]+"-----------</b>\n"
            for trigger in trigger_list:
                message+="<b>Error: "+trigger["error"]+"</b>\n"
                message+="--Date of last change: "+datetime.fromtimestamp(int(trigger["lastchange"])).strftime('%Y-%m-%d %H:%M:%S')+"\n"
                message+="--Priority: "+trigger["priority"]+"\n"
                message+="--Description: "+trigger["description"].replace("{HOST.NAME}", host["name"])+"\n"
                message+="\n"
    bot.sendMessage(chat_id=update.message.chat_id, text=message, parse_mode="HTML")

def show_help(bot, update):
    message="""USAGE of the commands
<b>list</b> - list active triggers (incidents)
<b>lsser [i][a]</b> - list servers. Option "i" - list inactive servers (unmonitored). Option "a" - list all servers. By default, only active(monitored) servers are listed.
<b>graph SEVERNAME RESOURCE [PERIOD]</b> - receive graphics of resource usage.
Where: 
- SERVERNAME is server name from '/lsser' command. you can write short name of server, ex: for TRZ-pf-2 you can type "pf2".
- RESOURCENAME is 'cpu', 'proc', 'mem', 'disk', 'all'. "cpu" is "CPU load", "proc" is "CPU utilization". You can type only first letters.
- PERIOD is period of graph in seconds, default is 3600. You can type use "h" for hours, "d" for days.
All parameters are case insensitive.
    """
    bot.sendMessage(chat_id=update.message.chat_id, text=message, parse_mode="HTML")

def report_alert(bot, job):
    message="<b>Daily report from {0} servers</b>\n".format(cityname)
    host_ids=[]
    for host in host_servers:
        for i in zapi.host.get({'filter':{'name':host}}):
            host_ids.append(i['hostid'])
    message+="\n<b>-- RAID --</b>\n"
    for i in host_ids:
        message+="\n-- "
        message+=zapi.host.get({'filter':{'hostid':i}})[0]['name']
        message+=" --\n"
        message+=zapi.item.get({'hostid':i,'filter':{'key_':'RAID-Stat'}})[-1]['lastvalue']
        message+="\n"
    message+="\n<b>-- Backups --</b>\n"
    for i in host_ids:
        tmp=zapi.item.get({'hostid':i,'filter':{'key_':'BACKUP-Stat'}})
        if tmp[-1]['hostid']==i:message+=tmp[-1]['lastvalue']
        message+="\n"
    message+="\n<b>-- Active triggers --</b>\n"
    monitored_hosts=zapi.host.get({'monitored_hosts' : True,'extendoutput' : True})
    for host in monitored_hosts:
        trigger_list=zapi.trigger.get({"hostids":host["hostid"], "filter":{"value":"1"}})
        if trigger_list.__len__()>0:
            message+="-- "+host["name"]+" --\n"
            for trigger in trigger_list:
                message+="<b>Error: "+trigger["error"]+"</b>\n"
                message+="--Date of last change: "+datetime.fromtimestamp(int(trigger["lastchange"])).strftime('%Y-%m-%d %H:%M:%S')+"\n"
                message+="--Priority: "+trigger["priority"]+"\n"
                message+="--Description: "+trigger["description"].replace("{HOST.NAME}", host["name"])+"\n"
                message+="\n"

    for i in allowed_chats:
        bot.sendMessage(chat_id=i, text=message, parse_mode="HTML")

zapi=ZabbixAPI(server=zabbix_server)
zapi.validate_certs=False
zapi.login(zabbix_user, zabbix_pass)

data = {"name":zabbix_user, "password":zabbix_pass, "enter":"Sign in"}
rc = requests.post(zabbix_server+'/', data=data)
cookie = rc.cookies

updater=Updater(token=token)
dispatcher=updater.dispatcher

job_queue = updater.job_queue
#daily_report_time_hour=15
#daily_report_time_minute=8
job_queue.run_daily(report_alert, time=time(daily_report_time_hour,daily_report_time_minute),name="DailySystemReports")
job_queue.start()

list_handler=CommandHandler('list', show_list)
help_handler=CommandHandler('help', show_help)
graph_handler=CommandHandler('graph', show_graph)
lsser_handler=CommandHandler('lsser', show_lsser)

dispatcher.add_handler(list_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(graph_handler)
dispatcher.add_handler(lsser_handler)
updater.start_polling()
