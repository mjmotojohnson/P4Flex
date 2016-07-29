#!/bin/sh -f
################################################################################
# Perforce and Perforce Broker start-up script
#
# NOTE: this script should be run as the perforce helix admin
#
################################################################################

#--------------------------------------- 
# STOP p4 and p4 broker daemon processes
#--------------------------------------- 

# shutdown the p4 process.  note: this may generate a warning if p4 is not running.
p4 -p 1666 admin stop

# kill off the p4broker process. note: this will generate a warning if the 
# p4broker is not running.
killall -u ec2-user p4broker


#--------------------------------------- 
# START p4 and p4 broker daemon processes
#--------------------------------------- 

# start the perforce helix process using port 1666 
# the perfoce file/log/journal depot is specified by the -r <path> option.
# create a log file calle 'log' and -d indicates p4d should run as a daemon
# process.

# note there are no special requirements for the p4 flex broker.  so modify
# the p4d command line as appropriate for your application.
p4d -p 1666 -r /ce_projects/perforce/p4_repos -Llog -d


# start the p4 broker.  The configuration file 'broker.cfg' specifies the
# options for loading the p4 flex broker script.  The -d option indicates the
# p4broker should run as a daemon process.
/sbin/p4broker -c p4flex_broker.cfg -d 


#--------------------------------------- 
# DEBUG HELP
#--------------------------------------- 
# Check that the processes are running properly
#  %> ps -ef | grep p4
#    ec2-user   8377      1  0 Apr25 ?        00:00:00 p4d -p 1666 -r /ce_projects/perforce/p4_depot -Llog -d
#    ec2-user   8379      1  0 Apr25 ?        00:00:00 /sbin/p4broker -c broker.cfg -d -v server=1




