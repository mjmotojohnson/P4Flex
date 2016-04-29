#!/usr/bin/env python
################################################################################
# P4FlexClone Broker script
#          This Perforce Broker script was developed by Perforce and NetApp to 
#          help demonstrate NetApp FlexClone technologies integrated via
#          P4 Broker calls.
#         
# Purpose: This Python based P4 Broker script adds additional commands to p4 
#          to enable the creation/deletion and management of NetApp filer 
#          volumes, snapshots and flexclones.
#          
#
# Usage:   %> p4 flex [command] [command options]
#
################################################################################

import os
import pwd
import sys
import subprocess
import getpass

# # add stream logging
# import logging
# logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-7.7s]  %(message)s")
# rootLogger = logging.getLogger()
# logPath  = "/ce_projects/perforce/main/logs"
# fileName = "logger"
# fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
# fileHandler.setFormatter(logFormatter)
# rootLogger.addHandler(fileHandler)
# 
# consoleHandler = logging.StreamHandler(sys.stdout)
# consoleHandler.setFormatter(logFormatter)
# rootLogger.setLevel('NOTSET')
# rootLogger.addHandler(consoleHandler)
# rootLogger.info('info message')
# logging.info('info message')
# logging.warning('warning message from mj')
# logging.error('got myself an error')

from mj_test import mj_test


mj_inst = mj_test()
mj_inst.mj_print("test me hard")



