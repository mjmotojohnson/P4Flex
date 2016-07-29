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
import logging
logging.basicConfig(filename='p4flex.py.log',level=logging.DEBUG)
logging.debug('starting p4flex.ply')

from P4 import P4, P4Exception

#---------------------------------------- 
# load NetApp manageability SDK APIs (NMSDK)
#---------------------------------------- 
# the NMSDK can be downloaded from www.support.netapp.com
# installation path    ***** CUSTOMIZE ME *****
sys.path.append("/usr/local/lib/netapp-manageability-sdk-5.5/lib/python/NetApp")
from NaServer import *



if sys.version_info[0] >= 3:
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser


# ---------------------------------------------------------------------------
# Singleton class (of sorts) for loading configuration
# ---------------------------------------------------------------------------
class Config:
    def __init__(self, file):
        self.config = ConfigParser()
        try:
            self.config.read(file)
        except:
            print("Could not read config file: %s" % file)
            sys.exit(2)
            
    def get(self, key):
        parts = key.split(".")
        try:
            value = self.config.get(parts[0], parts[1])
        except:
            print("Could not access config: %s" % key)
            sys.exit(2)
        return value

# read the p4flex.cfg file and load the values into 'config' data structure
# the p4flex.cfg file contains key=value pairs for configuring both the P4
# environment as well as the NetApp filer configurations. 
dir = os.path.dirname(os.path.realpath(__file__))
config     = Config(dir + "/p4flex.cfg")
FLEX_SNAP  = config.get("p4.snap")
FLEX_CLONE = config.get("p4.clone")

# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# NetApp Server connection as 'admin' user
# ---------------------------------------------------------------------------
class NaFlex:
    def __init__(self):
	# load Netapp filer configuration values (from the p4flex.cfg file)
        self.server      = config.get("NaServer.server")
        self.port        = config.get("NaServer.port")
        self.user        = config.get("NaServer.admin_user")
        self.passwd      = config.get("NaServer.admin_passwd")
        self.vserver     = config.get("NaServer.vserver")
        self.transport   = config.get("NaServer.transport")
        self.style       = config.get("NaServer.style")
        self.server_type = config.get("NaServer.server_type")
        self.aggr        = config.get("NaServer.aggr")
        self.mount_base  = config.get("NaServer.mount_base")
        self.mount_users = config.get("NaServer.mount_users")

    #--------------------------------------- 
    # initialize access to NetApp filer
    #--------------------------------------- 
    def get(self):

        # Creates a new object of NaServer class and sets the default value for the following object members:
	#   the cluster interface name/ip should be provided as the server.  
        #   syntax: ($clusterserver, $majorversion, $minorversion)
        s = NaServer(self.server, 1 , 15)
        s.set_server_type(self.server_type)

	# set communication style - typically just 'LOGIN'
        resp = s.set_style(self.style)
        if (resp and resp.results_errno() != 0) :
            r = resp.results_reason()
            print ("Failed to set authentication style " + r + "\n")
            sys.exit (2)

	# pass username/password for vserver ontapi application access
        s.set_admin_user(self.user, self.passwd)
	# set API transport type - HTTP is the default
        resp = s.set_transport_type(self.transport)
        if (resp and resp.results_errno() != 0) :
            r = resp.results_reason()
            print ("Unable to set HTTP transport " + r + "\n")
            sys.exit (2)
            
	# specify which vserver to access
        s.set_vserver(self.vserver)
	# set communication port
        s.set_port(self.port)

	# return storage object
	return s


    #--------------------------------------- 
    # Creates the volume based on name and size
    #--------------------------------------- 
    def volume_create(self, name, size, junction_path, uid, gid):
	api = NaElement("volume-create")
        api.child_add_string("containing-aggr-name", self.aggr)
        api.child_add_string("size", size)
        api.child_add_string("volume", name)
        api.child_add_string("user-id", uid)
        api.child_add_string("group-id", uid)

        # add junction_path
        api.child_add_string("junction-path", junction_path)

        xo = self.get().invoke_elem(api)
        if (xo.results_status() == "failed"):
            raise NAException(xo.sprintf())

    #--------------------------------------- 
    # Create a snapshot of specified volume
    #--------------------------------------- 
    def snapshot_create(self, volname, snapname):
	api = NaElement("snapshot-create")
        api.child_add_string("volume", volname)
        api.child_add_string("snapshot", snapname)

	# initialize exit message
	exit_msg = ""

	# invoke snapshot create
        xo = self.get().invoke_elem(api)
        if (xo.results_status() == "failed"):
	    exit_msg += "ERROR Failed to create snapshot\n"
	    exit_msg += "      Reason: %s" % xo.results_reason()

	# return exit message - no message if successful
	return exit_msg

    #--------------------------------------- 
    # Deletes a snapshot from specified volume
    #--------------------------------------- 
    def snapshot_delete(self, volname, snapname):
	api = NaElement("snapshot-delete")
        api.child_add_string("volume", volname)
        api.child_add_string("snapshot", snapname)

	# initialize exit message
	exit_msg = ""

	# invoke snapshot delete
        xo = self.get().invoke_elem(api)
        if (xo.results_status() == "failed"):
	    exit_msg += "ERROR failed to delete snapshot"
	    exit_msg += "      Reason:" + xo.results_reason()

	# return exit message - no message if successful
	return exit_msg


    #--------------------------------------- 
    # function: volume existence check (returns true/false)
    #--------------------------------------- 
    def volume_exists(self, volume_name):

	# get list of volumes
        netapp = NaFlex()
	vols = netapp.vlist()

	# create list of existing volumes
	list=""
	for v in vols:
	    vol2match = v.child_get_string("name")
	    #print("DEBUG: %s\n" % vol2match)

	    # check if my volume_name is in the list of volumes
	    if volume_name == vol2match: 
	       return True
	    else:
	       next

	# volume not found
        return False

    #--------------------------------------- 
    # function: snapshot existence check (returns true/false)
    #--------------------------------------- 
    def snapshot_exists(self, volume_name, snapshot_name):

	# get list of volumes
        netapp = NaFlex()

        # Get First Set of records
        api = NaElement("snapshot-list-info")
        api.child_add_string("volume", volume_name)

        xo = self.get().invoke_elem(api)

        if (xo.results_errno() != 0) :
            raise NAException(xo.sprintf())

        # # get snapshot list
        snapshotlist = xo.child_get("snapshots")
	 
	# test if snapshot exists or not
        if ((snapshotlist != None) and (snapshotlist != "")) :
            # iterate through snapshot list
            snapshot_list = snapshotlist.children_get()
            for ss in snapshot_list:
                sname = ss.child_get_string("name")
                #print("snapshot:%s" % (sname))
		if snapshot_name == sname:
		    # snapshot exists, return True
		    return True
		else:
		    # no match - try next snapshot
		    next
	    # if we get to the end of the loop, then we didn't match
	    return False
        else:
            #print("No snapshots for volume " + vname)
	    return False

        
    #--------------------------------------- 
    # Creates a flexclone based on volume/snapshot pair
    #--------------------------------------- 
    def clone_create(self, cvolname, psnapname, pvolname, junct_path):

	# check to verify that the volume and snapshot exist before cloning
	if not self.volume_exists(pvolname):
	    print("action: REJECT")
	    print("message: ERROR volume <\"%s\"> does not exist\n" % pvolname)
	    return

	# check to verify that the volume and snapshot exist before cloning
	if not self.snapshot_exists(pvolname, psnapname):
	    print("action: REJECT")
	    print("message: ERROR snapshot <\"%s\"> does not exist\n" % psnapname)
	    return

        api = NaElement("volume-clone-create")

	# parent volume and snapshot pair to flexclone
        api.child_add_string("parent-volume", pvolname)
        api.child_add_string("parent-snapshot", psnapname)

	# specify flexclone name to create
        api.child_add_string("volume", cvolname)

	# specify junction_path - this is essentially where the clone will be
	# mounted in the file system.
        api.child_add_string("junction-active", "true")
        api.child_add_string("junction-path",   junct_path)

	# force the flexclone to use thin provisioning even if the parent
	# volume is thick previsioned. without this, the clone will not have
	# any space savings. it will take the same reserved space as the parent.
        api.child_add_string("space-reserve",   "none")

	# initialize exit message
	exit_msg = ""

	# invoke volume-clone-create command and check status
        xo = self.get().invoke_elem(api)
        if (xo.results_status() == "failed"):
	    exit_msg += "ERROR failed to create flexclone volume"
	    exit_msg += "      Reason:" + xo.results_reason()
	    exit_msg += "      volume-clone-create -parent-volume %s " % pvolname
	    exit_msg +=       "-parent-snapshot %s " % psnapname 
	    exit_msg +=       "-volume %s\n" % cvolname

	# return exit message - no message if successful
	return exit_msg

    #--------------------------------------- 
    # Deletes the volume by unmounting, offlining and then deleting volume 
    #--------------------------------------- 
    def delete(self, volname):

        # Check to make sure volume passed in is not vserver root or node volume
        # Root and node volumes are required to keep info on state of vserver and node
        api = NaElement("volume-get-iter")

        # Build the input values for the api query call
        xi1 = NaElement("query")
        api.child_add(xi1)
        xi2 = NaElement("volume-attributes")
        xi1.child_add(xi2)
        xi3 = NaElement("volume-id-attributes")
        xi2.child_add(xi3)
        xi3.child_add_string("name", volname)

        xo = self.get().invoke_elem(api)
        if (xo.results_status() == "failed"):
            raise NAException(xo.sprintf())

        vlist = xo.child_get("attributes-list")
        vsattrs = None
        if (vlist != None):
            vol = vlist.child_get("volume-attributes")
            vsattrs = vol.child_get("volume-state-attributes")

        if (vsattrs != None):
            isvroot = vsattrs.child_get_string("is-vserver-root")
            isnroot = vsattrs.child_get_string("is-node-root")
            if ((isvroot == "true") or (isnroot == "true")):
                raise NAException("Not authorized to delete vserver root-volume %s. Go directly to the NetApp Filer to conduct this operation" % (volname))

        # Unmount 
        api = NaElement("volume-unmount")
        api.child_add_string("force", "false")
        api.child_add_string("volume-name", volname)
        
        xo = self.get().invoke_elem(api)
        if (xo.results_status() == "failed"):
            raise NAException(xo.sprintf())

        # Offline
        api = NaElement("volume-offline")
        api.child_add_string("name", volname)
        
        xo = self.get().invoke_elem(api)
        if ((xo.results_status() == "failed") and (xo.results_errno() != "13042")):
            raise NAException(xo.sprintf())

        # Delete
        api = NaElement("volume-destroy")
        api.child_add_string("name", volname)

        xo = self.get().invoke_elem(api)
        if (xo.results_status() == "failed"):
            raise NAException(xo.sprintf())
    

    #--------------------------------------- 
    # Reports the list of volumes 
    #--------------------------------------- 
    def volume_list(self):
	vol_list = []

	# for each volume element
	for tattr in self.vGetcDOTList("volume-get-iter"):
	    print "hello"
	    #tattr.sprintf()
	    # get the volume id attrbutes
	    vol_id_attrs = tattr.child_get("volume-id-attributes")
 
	    # get the volume name
	    if vol_id_attrs:
		vol_list += vol_id_attrs-child_get_string("name")

	#return vol_list
	return "hello"


    #--------------------------------------- 
    # Reports the list of volumes 
    #--------------------------------------- 
    def vlist (self):
        list = []
        
        # Get First Set of mrecs (100) records
        mrecs = "100"
        api = NaElement("volume-get-iter")
        api.child_add_string("max-records", mrecs)
        xo = self.get().invoke_elem(api)

        if(xo.results_status() == "failed"):
            raise NAException(xo.sprintf())

        # Set up to get next set of records
        tag = xo.child_get_string("next-tag")
  
        # Add vollist results to list and then Get Following set of records
        # Break from loop when the vollist is None or next-tag is None
        while True:
	    # get list of volume-info attributes
	    vollist = dict()
            vollist = xo.child_get("attributes-list")

            if (vollist == None): 
                break
            
            for vol in vollist.children_get():

		volpname = ""
		# get volume attributes (which includes volume name)
                vol_id_attrs = vol.child_get("volume-id-attributes")

		# determin volume name
		if vol_id_attrs:
		    volname = vol_id_attrs.child_get_string("name")

		    # MJ_DEBUG BIG DEMO Hack
		    if str(volname) == str("ce_projects"):
			continue
		    if str(volname) == str("perforce"):
			continue
		    if str(volname) == str("p4voliscsi_SAS"):
			continue

		    junc_path = vol_id_attrs.child_get_string("junction_path")

		    if str(vol_id_attrs.child_get_string("junction-path")) == "None":
			continue
                
                volstateattrs = vol.child_get("volume-state-attributes")
                if (volstateattrs != None):
                    state  = volstateattrs.child_get_string("state") 
                    isroot = volstateattrs.child_get_string("is-vserver-root")
                    
                volcattrs = vol.child_get("volume-clone-attributes")
                if (volcattrs != None): 
                    volpattrs = volcattrs.child_get("volume-clone-parent-attributes")
                    if (volpattrs != None):
                        volpname = volpattrs.child_get_string("name")

                # Only print out volume if volume is online and has a juction_path, not a clone, and not vserver root volume
                #if (state == "online") and (str(junc_path) != "None") and (volpname == "") and (isroot != "true"):
                if (state == "online") and (volpname == "") and (isroot != "true"):
		    list.append(vol_id_attrs);
			

	    # get next set of records
            api = NaElement("volume-get-iter")
            api.child_add_string("max-records", mrecs)
            api.child_add_string("tag", tag)
            xo = self.get().invoke_elem(api)
            if(xo.results_status() == "failed"):
                raise NAException(xo.sprintf())

            # Get next tag which indicates if there are more records
            tag = xo.child_get_string("next-tag")
            if (tag == None):
                break
            
        return list



    #--------------------------------------- 
    # Print out volume name and their snapshots
    #--------------------------------------- 
    def slistall(self):

	# get list of volumes
	volume_list = self.vlist()

	# list to hold snapshot values
	snapshot_list = []

        # Get first set of records defined by mrecs
        mrecs = "100"
        api = NaElement("snapshot-get-iter")
        api.child_add_string("max-records", mrecs)
        xo = self.get().invoke_elem(api)

        if(xo.results_status() == "failed"):
            raise NAException(xo.sprintf())

        # Set up tag to get next set of records
        tag = xo.child_get_string("next-tag")
        sslist=""
        
        # Need to go thru this loop at least once before checking for next tag
        # Break out of loop if snaplist is None or next-tag is None
        while True:
            # Get list of snapshot-info attributes
            snaplist = dict()
            snaplist = xo.child_get("attributes-list")

            if (snaplist == None):
                break

            # Go thru list and print out volume and snapshot name
            for snap in snaplist.children_get(): 
		# check if volume is in filtered volume list
                vol_name  = snap.child_get_string("volume")

		# check that snap volume is in the list of filtered volumes
		valid_vol = False
		for volume in volume_list:
		    if vol_name == volume.child_get_string("name"):
			valid_vol = True

		# if valid volume not found, skip it
		if not valid_vol:
		    continue


		# get snapshot name
                snap_name = snap.child_get_string("name")

                # skip reporting of weekly snapshots
                if 'weekly' in snap_name:
                   continue
                # skip reporting of daily snapshots
                if 'daily' in snap_name:
                   continue
                # skip reporting of hourly snapshots
                if 'hourly' in snap_name:
                   continue

                snapshot_list.append( snap )
                
            # Get next set of records
            api = NaElement("snapshot-get-iter")
            api.child_add_string("max-records", mrecs)
            api.child_add_string("tag", tag)
            xo = self.get().invoke_elem(api)
            if(xo.results_status() == "failed"):
                raise NAException(xo.sprintf())

           # Tag indicates if there are more records
            tag = xo.child_get_string("next-tag")

            # Break out of loop.  Tag of None indicates no more records
            if (tag == None):
                break


        return snapshot_list

    #---------------------------------------  
    # list flexclones
    #---------------------------------------  
    def list_flexclones(self):

	junction_path_map = dict()
	comment_field_map = dict()
	vol_usage_map     = dict()
	vol_dedup_saved   = dict()
	vol_dedup_shared  = dict()


        # Get First Set of mrecs (100) records
        mrecs = "100"
        api = NaElement("volume-get-iter")
        api.child_add_string("max-records", mrecs)
        xo = self.get().invoke_elem(api)

        if(xo.results_status() == "failed"):
            raise NAException(xo.sprintf())

        # Set up to get next set of records
        tag = xo.child_get_string("next-tag")
  
        # Add vollist results to list and then Get Following set of records
        # Break from loop when the vollist is None or next-tag is None
        while True:
	    # get list of volume-info attributes
	    vollist = dict()
            vollist = xo.child_get("attributes-list")

            if (vollist == None): 
		break

	    # loop thru list of volumes to get specific volume attribute data
	    for tattr in vollist.children_get():
		vol_id_attrs = tattr.child_get("volume-id-attributes")
	    
		if vol_id_attrs:
		    volume_name   = vol_id_attrs.child_get_string("name")
		    junct_path    = vol_id_attrs.child_get_string("junction-path")
		    comment_field = vol_id_attrs.child_get_string("comment")
	    
		    # store junction_path for later
		    junction_path_map[volume_name] = junct_path
		    # if the comment field is empty, just put UNKNOWN as the value
		    if comment_field:
			comment_field_map[volume_name] = comment_field
		    else:
			comment_field_map[volume_name] = "UNKNOWN"
	    
		    vol_space_attrs = tattr.child_get( "volume-space-attributes" );
		    if vol_space_attrs:
			vol_usage = vol_space_attrs.child_get_string( "size-used" );
			if vol_usage:
			    vol_usage_map[volume_name] = vol_usage;
			    #print "DEBUG: vol usage: $volume_name $vol_usage_map{$volume_name}\n";

		    vol_sis_attrs = tattr.child_get( "volume-sis-attributes" )
		    if vol_sis_attrs:
			dedup_saved  = vol_sis_attrs.child_get_string( "percentage-total-space-saved" )
			dedup_shared = vol_sis_attrs.child_get_string( "deduplication-space-shared" )
		    if dedup_saved:
			vol_dedup_saved[volume_name]  = dedup_saved
			vol_dedup_shared[volume_name] = dedup_shared


	    # get next set of records
            api = NaElement("volume-get-iter")
            api.child_add_string("max-records", mrecs)
            api.child_add_string("tag", tag)
            xo = self.get().invoke_elem(api)
            if(xo.results_status() == "failed"):
                raise NAException(xo.sprintf())

            # Get next tag which indicates if there are more records
            tag = xo.child_get_string("next-tag")
            if (tag == None):
                break


	#---------------------------------------- 
	# create report header
	#---------------------------------------- 
	list = "\nList FlexClones\n";
		#123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890 
	list += "%-25s %-30s %-34s " % ("Parent Volume", "Parent-Snapshot", "FlexClone");
	list += "%15s"               %  "Parent Vol";
	list += "%15s"               %  "FlexClone Vol";
	list += "%15s"               %  "Split Est";
	list += "%25s"               %  "FlexClone Act";
	#list += "%15s"               %  "Clone Owner";
	list += "  %s \n"            %  "Junction-path";
	list += "---------------------------------------------------------------------------------------";
	list +=	"---------------------------------------------------------------------------------------------------\n"; 

        #---------------------------------------- 
        # get FlexCone info iteratively - it will return a list
        #---------------------------------------- 

        # Get First Set of mrecs (100) records
        mrecs = "100"
        api = NaElement("volume-clone-get-iter")
        api.child_add_string("max-records", mrecs)
        xo = self.get().invoke_elem(api)

        if(xo.results_status() == "failed"):
            raise NAException(xo.sprintf())

        # Set up to get next set of records
        tag = xo.child_get_string("next-tag")
  
        # Add vollist results to list and then Get Following set of records
        # Break from loop when the vollist is None or next-tag is None
        while True:
	    # get list of volume-info attributes
	    vollist = dict()
            vollist = xo.child_get("attributes-list")

            if (vollist == None): 
		break


	    # for each clone entry
	    for vol_data in vollist.children_get():
	    #printf($vol_data->sprintf());
		volume_name    = vol_data.child_get_string( "parent-volume"  );
		clone_name     = vol_data.child_get_string( "volume"         );
		snapshot       = vol_data.child_get_string( "parent-snapshot");
		flexclone_used = vol_data.child_get_string( "used"           );
		split_est      = vol_data.child_get_string( "split-estimate" );
		comment_field  = comment_field_map[clone_name];
		if comment_field == "":
		    comment_field  = "USER_UNKNOWN" 

        	# parent volume: space used - represent data used in MB
        	vol_usage = vol_usage_map[volume_name]
        	parent_used = float(vol_usage)/1024/1024;
        
        	# split estimate value is returned in blocks rather than bytes
        	split_est   = float(split_est)*4096; # blocks => Bytes
        
        	# storage used by the FlexClone
        	flexclone_actual = abs(float(flexclone_used)-float(split_est));
        
        	# calculate % savings
        	savings          = (float(flexclone_actual)/float(flexclone_used))*100;
        	compression      = (1 - float(flexclone_actual) / float(flexclone_used)) * 100;
        
        	# FlexClone volume: space used - represent data used in MB
        	flexclone_used   = float(flexclone_used) / 1024 / 1024;
        
        	# FlexClone calculated actual: space used - represent data used in MB
        	flexclone_actual = float(flexclone_actual)/1024/1024;
        
        	# split estimate value is returned in blocks rather than bytes
        	split_est        = float(split_est)/1024/1024; # date in MiB

        	# determine juction-path info
        	jpath       = vol_data.child_get_string( "junction-path"  );
        	# test if the value returned correctly
        	if jpath:
        	    # perfect the look up worked correctly
		    dummyval = 0;
        	elif junction_path_map[clone_name]:
        	    # ok lookup didn't work, but it was found by method #2
        	    jpath = junction_path_map[clone_name]
        	else:
        	    # no junction path found
        	    jpath = "Not Mounted"; 
        	
        	# print results
        	list += "%-25s %-30s %-35s " % (volume_name, snapshot, clone_name);
        	list += "%11.2f MB "         %  parent_used;
        	list += "%11.2f MB "         %  flexclone_used;
        	list += "%11.2f MB "         %  split_est;
        	list += "%11.2f MB"          %  flexclone_actual;
        	list += " (%6.2f"            %  savings; 
		list += "%)";
               #list += " (%5.2f"            %  compression; print "%)";
        #	list += "%15s"               %  comment_field;
        	list += "  %s\n"             %  jpath;

	    # get next set of records
            api = NaElement("volume-get-iter")
            api.child_add_string("max-records", mrecs)
            api.child_add_string("tag", tag)
            xo = self.get().invoke_elem(api)
            if(xo.results_status() == "failed"):
                raise NAException(xo.sprintf())

            # Get next tag which indicates if there are more records
            tag = xo.child_get_string("next-tag")
            if (tag == None):
		break

	return list


    #--------------------------------------- 
    # Reports list of clones with their corresponding parent volume and parent snapshot
    #--------------------------------------- 
    def clist(self):
        # Get first set number of records defined by mrecs
        mrecs = "100"
        api = NaElement("volume-clone-get-iter")
        api.child_add_string("max-records", mrecs)
        xo = self.get().invoke_elem(api)

        if(xo.results_status() == "failed"):
            raise NAException(xo.sprintf())

        # Set up to get next set of records
        tag = xo.child_get_string("next-tag")
        print("\n")
        print("List FlexClones\n")
        
        # Need to go thru this loop at least once before checking for next tag
        while True:
            # Get list of snapshot-info attributes
            clonelist = dict()
            clonelist = xo.child_get("attributes-list")

            if (clonelist == None):
                break

            for clone in clonelist.children_get(): 
                print("clone: %s:%s:%s" % (clone.child_get_string("parent-volume"), clone.child_get_string("parent-snapshot"), clone.child_get_string("volume")))
                
            # Get next set of records
            api = NaElement("volume-clone-get-iter")
            api.child_add_string("max-records", mrecs)
            api.child_add_string("tag", tag)
            xo = self.get().invoke_elem(api)
            if(xo.results_status() == "failed"):
                raise NAException(xo.sprintf())

           # Tag indicates if there are more records
            tag = xo.child_get_string("next-tag")

            # Break if no more records
            if (tag == None):
                break

    #--------------------------------------- 
    # Function: vGetcDOTList()
    # Func: Note that Perl is a lot more forgiving with long object lists than ONTAP is.  As a result,
    #	    we have the luxury of returning the entire set of objects back to the caller.  Get all the
    #	    objects rather than waiting.
    #--------------------------------------- 
    def vGetcDOTList(self, zapiCall):
        
        # Get First Set of mrecs (100) records
        MAX_RECORDS = "100"
	done        = 0
	tag         = 0
	exit_msg    = ""
        list        = dict()

	# loop thru calling the command until all tags are processed
        while not done:

	    api = NaElement(zapiCall)
	    # if a tag exists, pass it to the zapi command
	    if tag:
		api.child_add_string("tag", tag)
	    else:
		# not tag exists - probably the first time the command is called
		api.child_add_string("max-records", MAX_RECORDS)

	    # invode command
	    zapi_results = self.get().invoke_elem(api)

	    if(zapi_results.results_status() == "failed"):
		exit_msg += "ERROR: ONTAP API call %s failed: " % zapiCall
		exit_msg += zapi_results.results_reason() 
		return exit_msg

	    # Set up to get next set of records
	    tag = zapi_results.child_get_string("next-tag")

	    # get list of attributes
            list_attrs = zapi_results.child_get("attributes-list")

	    # not get children from and add them to the list
            if list_attrs: 
		list_items = list_attrs.children_get
		if list_items:
		    list.append(list_items)
            
            if not tag :
                done = 1
            
	return list

class NAException(Exception):
    def __init__(self, e):
        self.error = e

# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Perforce connection as 'flex' user
# this user is specified in the p4flex.cfg file.  Only this user can create/remove
# volumes and snapshots.
# ---------------------------------------------------------------------------
class P4Flex:
    def __init__(self):
        self.port   = config.get("p4.port")
        self.user   = config.get("p4.user")
        self.passwd = config.get("p4.passwd")
        
    def getP4(self):
        p4 = P4()
        p4.user     = self.user
        p4.port     = self.port
        p4.connect()
        p4.password = self.passwd
        p4.run_login()
        return p4
# ---------------------------------------------------------------------------
   
       

# ---------------------------------------------------------------------------
# Parse the Broker's request and provide access to the user's environment
# ---------------------------------------------------------------------------
class Broker:
    def __init__(self):
        self.args = {}
        # Comment out stdin and uncomment block below for debug.
        lines = sys.stdin.readlines()
        # lines = []
        # with open("in.txt") as f:
        #    lines = f.readlines()

        for line in lines:
            parts = line.split(": ")
            self.args[parts[0]] = parts[1].rstrip()  
    
    def getP4(self):
        p4 = P4()
        p4.user   = self.args['user']
        p4.port   = self.args['clientPort']
        p4.client = self.args['workspace']
        p4.connect()
        
        # Use flex account to login user
        s4 = P4Flex().getP4()
        s4.run_login(self.args['user'])
        return p4
    
    def getPort(self):
        return self.args['clientPort']
    
    def getUser(self):
        return self.args['user']
    
    def getClient(self):
        return self.args['workspace']
    
    def getCommand(self):
        if 'Arg0' in self.args:
            return self.args['Arg0']
        else:
            return None
    
    def getOptions(self):
        c = 1
        opts = []
        while True:
            key = 'Arg' + str(c)
            c += 1
            if key in self.args:
                opts.append(self.args[key])
            else:
                break
               
        join = "" 
        list = []
        for opt in opts:
            if join:
                opt = join + opt
                join = ""
            if opt.startswith('-') and len(opt) == 2:
                join = opt
            else:
                list.append(opt)
        if join:
            list.append(opt)
        return list
# ---------------------------------------------------------------------------

     

# ---------------------------------------------------------------------------
# Handle Broker request and invoke the registered 'flex' command
# ---------------------------------------------------------------------------
class Flex:
    def __init__(self):
    
        # Process Broker arguments
        self.call = Broker()
        self.command = self.call.getCommand()
        self.args = self.call.args
        self.opts = self.call.getOptions()
   
        # Build table p4 flex [command] : function
        self.cmdFn = {
            'volume':         self.volume,
            'lv':             self.list_volumes,
            'list_volumes':   self.list_volumes,
            'volumes':        self.list_volumes,
            'snapshot':       self.snapshot,
            'ls':             self.list_snapshots,
            'list_snapshots': self.list_snapshots,
            'snapshots':      self.list_snapshots,
            'clone':          self.clone,
            'lc':             self.list_clones,
            'list_clones':    self.list_clones,
            'clones':         self.list_clones,
            'help':           self.help
            };
            
        if not self.isnfs(NaFlex().mount_base):
            print("action: REJECT")
            print("message: \"%s\"" % "NetApp NFS volume is not mounted.")
            return

        # Call command
        if self.command in self.cmdFn:
            self.cmdFn[self.command]()
        else:
            self.usage()     
    
    
    #---------------------------------------  
    # Create/Delete Volume
    #---------------------------------------  
    def volume(self):

	message  = self.print_banner()

	#---------------------------------------  
	#       CUSTOMIZE SECURITY CONTROLS AS NEEDED
	#---------------------------------------  
	#       Check for 'admin' permission - the assumption is that only certain
	#       p4 users are allowed to create new volumes.  For now the code is
	#       commented out, which essentially allows any user to create volumes
	#       if not self.permission():
	#           print("action: REJECT")
	#           message += "ERROR: You don't have permission for this operation.\n"
	#           print("message: \"%s\"" % message)
	#           return
        
        # Get options (set defaults) 
        vname         = ""
        size          = "1G"
        volume_owner  = ""
        junction_path = ""

	# parse the command line options
        for o in self.opts:
            if o.startswith('-d'):
                del_name = o[2:]
                self.vol_del(del_name)
                return
            if o.startswith('-s'):
                size = o[2:]
            if o.startswith('-j'):
                junction_path = o[2:]
            if o.startswith('-u'):
		# if running sudo, user name is not set right in python
		# allow user to pass in a value
                volume_owner = o[2:]
            else:
                vname = o
            
        if not vname:
            print("action: REJECT")
	    message += "ERROR: No flex volume name provided"
            print("message: \"%s\"" % message)
            return
        
        # NetApp connection
        netapp = NaFlex()

	#--------------------------------------- 
	# determine junction path  (mount point)
	#--------------------------------------- 
	# put the new volume at the end of the pre-mounted root directory
	# this will make it so the new volume will automatically be mounted

	# NOTE: volumes will be created by project admins, so they will be mounted to the
	# mount_base directory as specified in the cfg file
	if not junction_path:
	    junction_path = netapp.mount_base + "/" + vname 

	#--------------------------------------- 
	# get current users name and
	# make sure user has a directory at mount point
	#--------------------------------------- 
	# clone_owner is not passed on the cmd line, then just take
	# the value from the OS.  Note if run as sudo, this will not the
	# the current user, but instead the user to launch sudo
	if not volume_owner:
            volume_owner = self.call.getUser()

        # get user id and group id. These are used to set proper ownership of
	# the new volume
        uid = pwd.getpwnam(volume_owner).pw_uid
        gid = pwd.getpwnam(volume_owner).pw_gid

        
        # Create NetApp volume
        try:  
            netapp.volume_create(vname, size, junction_path, uid, gid)

            # Set file ownership of newly created volume.
            #self.chown(user, junction_path)

            print("action: RESPOND")
	    message += "INFO: Successfully created volume " + vname + "\n"
            message += "      Mounted on " + junction_path + "\n\n"
            print("message: \"%s\"" % message) 
                  
        except NAException as e:
            print("action: RESPOND")
            message += "\nNetApp Error: " + e.error
            print("message: %s" % message)

        except Exception as e:
            # If got unexpected error, delete the volume created
            message += "Unexpected Error: " + str(e)
            try:
                netapp.delete(vname)
            except NAException as e:
                error += '\nNetApp Error: ' + e.error
		print("action: RESPOND")
		print("message: \"%s\"" % error)

    #---------------------------------------  
    # Print program header
    #---------------------------------------  
    def print_banner(self):
        netapp = NaFlex()

	banner  = "------------------------------------------------------------\n"
	banner += "Perforce/NetApp P4FlexClone Broker\n"
	banner += "------------------------------------------------------------\n\n"
	banner += "INFO: Successfully connected to NetApp filer\n"
	banner += "      Cluster I/F: %s \n"   % netapp.server
	banner += "      SVM:         %s \n\n" % netapp.vserver

	return banner


    #---------------------------------------  
    # List Volumes
    #---------------------------------------  
    def list_volumes(self):
        # NetApp connection
        netapp = NaFlex()

        # List the volumes
        try:  
	    msg_header  = self.print_banner()
            msg_header += "%-40s     Junction Path\n"        % "Volume Name"
            msg_header += "%-40s     ----------------------------------------\n" % "----------------------------------------" 
            vols = netapp.vlist()

	    msg_body = ""
            for v in vols:
		if str(v.child_get_string("junction-path")) == "None":
		    continue

                msg_body += "%-40s     %s\n" % (v.child_get_string("name"), v.child_get_string("junction-path"))

	    if msg_body == "":
		msg_body = "No volumes found"

	    message = msg_header + msg_body
                
            print("action: RESPOND")                  
            print("message: \"%s\"" % message)

        except NAException as e:
            print("action: RESPOND")
            error = '\nNetApp Error: ' + e.error
            print("message: \"%s\"" % error)

 
    #---------------------------------------  
    # Create/Delete Snapshot
    #---------------------------------------  
    def snapshot(self):
	logging.debug("DEBUG: def snapsho: sub routine called")

        #--NetApp/Perforce connection as Flex
        netapp = NaFlex()
        p4 = P4Flex().getP4()

	message  = self.print_banner()

        # Get options (set defaults)
        volume_name   = ""
        snapshot_name = ""


        from_client_name = self.call.getClient()
	logging.debug("DEBUG 1: from_client_name = %s\n", from_client_name)
        for o in self.opts:
            if o.startswith('-V'):
                volume_name = o[2:]
            if o.startswith('-d'):
		# delete snapshot function
                snapshot_name = o[2:]
                self.snap_del(volume_name, snapshot_name)
                return 
            if o.startswith('-c'):
                from_client_name = o[2:]
            else:
                snapshot_name = o

	logging.debug("DEBUG: def snapshot: from_client_name = %s\n", from_client_name)
                
        if not volume_name:
            print("action: REJECT")
	    message += "ERROR No volume name provided.\n"
            print("message: \"%s\"" % message)
            return
        
        if not snapshot_name:
            print("action: REJECT")
	    message += "ERROR No snapshot name provided.\n"
            print("message: \"%s\"" % message)
            return
        
        if ':' in snapshot_name:
            print("action: REJECT")
	    message += "ERROR Flex clone name must not use ':'"
            print("message: \"%s\"" % message)
            return     
        
	#---------------------------------------  
	#       CUSTOMIZE SECURITY CONTROLS AS NEEDED
	#---------------------------------------  
	#       Check for 'admin' permission - the assumption is that only certain
	#       p4 users are allowed to create/delete snapshots.  For now the code is
	#       commented out, which essentially allows any user to create/delete snapshots
	#       if not self.permission():
	#           print("action: REJECT")
	#           message += "ERROR You don't have permission for this operation."
	#           print("message: \"%s\"" % message)
	#           return        

        # check to verify that the volume and snapshot exist before cloning
        if (netapp.snapshot_exists(volume_name, snapshot_name) == True):
            print("action: REJECT")
	    message += "ERROR snapshot <\"%s\"> already exists.\n" % snapshot_name
            print("message: \"%s\"" % message)
            return
        
        
        # Create NetApp snapshot
        try:
	    # call netapp api to create snapshot
            exit_msg = netapp.snapshot_create(volume_name, snapshot_name)

	    # check exit status
            if exit_msg == "":
		print("action: RESPOND")
		message += "INFO: Successfully created snapshot %s\n" % snapshot_name
		print("message: \"%s\"" % message)
	    else:
		print("action: REJECT")
		message += exit_msg
		print("message: \"%s\"" % message)
        
        except NAException as e:
            print("action: RESPOND")
            message += '\nNetApp Error: ' + e.error
            print("message: \"%s\"" % message)
              
#MJ_MOD
        # Create Perforce workspace for snapshot
        try:  
            from_client = p4.fetch_client(from_client_name)
            root = from_client['Root']
            logging.debug("DEBUG: def snapshot: root = %s\n", root)
            
            # Clone client workspace
            flex_client_name = FLEX_SNAP + volume_name + ':' + snapshot_name
            p4.client = flex_client_name
            flex_client = p4.fetch_client("-t", from_client_name, flex_client_name)
            logging.debug("DEBUG: def snapshot: flex_client_name = %s\n", flex_client_name)
            
            # Set workspace options: root to mounted volume
            path = netapp.mount_base + "/" + volume_name
            flex_client['Root'] = path
            flex_client['Host'] = ""
            logging.debug("DEBUG: def snapshot: flex_client['Root'] = %s\n", path)
 
            #flex_client['Options'] = flex_client['Options'].replace(" unlocked", " locked")
            p4.save_client(flex_client)
            
            # Populate have list
            p4.run_sync("-k", "//" + flex_client_name + "/...@" + from_client_name)
            
            print("action: RESPOND")
            print("message: \"Created flex snapshot %s\"" % snapshot_name)
            
        except P4Exception:
            print("action: RESPOND")
            error = '\n'.join(p4.errors)
            error += '\n'.join(p4.warnings)
            print("message: \"%s\"" % error)
 
        finally:
            p4.disconnect()

   

    #---------------------------------------  
    # check if user has permissions to run a command
    #---------------------------------------  
    def permission(self):

        try:
	    # Perforce connection as Caller
	    p4 = self.call.getP4()
            for p in p4.run_protects():
                if (p['perm'] == 'admin') or (p['perm'] == 'super'):
                    return True    
            return False
        
        except P4Exception:
            print("action: RESPOND")
            error = '\n'.join(p4.errors)
            error += '\n'.join(p4.warnings)
            print("message: \"%s\"" % error)
            
        finally:
            p4.disconnect()              


    #---------------------------------------  
    # List snapshots
    #---------------------------------------  
    def list_snapshots(self):

	# make call to get list of snapshots
        netapp = NaFlex()
	sslist = netapp.slistall()

        try:  
            print("action: RESPOND")
	    list  = self.print_banner()
            list += "%-40s     Snapshot Name\n"          % "Volume Name"
            list += "%-40s     --------------------\n" % "--------------------"
            for s in sslist:
		# check if volume is in list of filtered volumes
		volume_name = s.child_get_string("volume")

		list += "%-40s     " % volume_name 
		list += "%s" % s.child_get_string("name")
		list += "\n"

            print("message: \"%s\"" % list)

        except NAException as e:
            print("action: RESPOND")
            error = '\nNetApp Error: ' + e.error
            print("message: \"%s\"" % error)


   
    #---------------------------------------  
    # Clones a new FLEX_CLONE workspace from the parent flexSnap_
    #---------------------------------------  
    def clone(self):
        # Get options 
        vname         = ""
        sname         = ""
        cname         = ""
        clone_owner   = ""
        junction_path = ""

	# process command options
        for o in self.opts:
            if o.startswith('-d'):
		# delete clone option selected
                del_name = o[2:]
                self.clone_delete(del_name)
                return
            if o.startswith('-V'):
		# volume name
                vname = o[2:]
            if o.startswith('-S'):
		# snapshot name
                sname = o[2:]
            if o.startswith('-u'):
		# if running sudo, user name is not set right in python
		# allow user to pass in a value
                clone_owner = o[2:]
            if o.startswith('-j'):
                junction_path = o[2:]
            else:
		# flexclone name
                cname = o

	message  = self.print_banner()
        
	# validate that volume, snapshot and clone names were properly passed 
        if not vname:
            print("action: REJECT")
	    message += "ERROR: No volume name provided\n"
            print("message: \"%s\"" % message)
            return
        
        if not sname:
            print("action: REJECT")
	    message += "ERROR: No snapshot name provided\n"
            print("message: \"%s\"" % message)
            return
        
        if not cname:
            print("action: REJECT")
	    message += "ERROR: No flexclone name provided\n"
            print("message: \"%s\"" % message)
            return
        
        if ':' in cname:
            print("action: REJECT")
	    message += "ERROR: Flexclone name must not use ':'"
            print("message: \"%s\"" % message)
            return  

        
        # NetApp/Perforce connection as Caller
        netapp = NaFlex()
        p4 = self.call.getP4()


	#--------------------------------------- 
	# get current users name and
	# make sure user has a directory at mount point
	#--------------------------------------- 
	# clone_owner is not passed on the cmd line, then just take
	# the value from the OS.  Note if run as sudo, this will not the
	# the current user, but instead the user to launch sudo
	if not clone_owner:
            clone_owner = self.call.getUser()


	#--------------------------------------- 
	# determine junction path  (mount point)
	#--------------------------------------- 
	# put the new volume at the end of the pre-mounted root directory
	# this will make it so the new volume will automatically be mounted

	# NOTE: clones will be created by users, so they will be mounted to the
	# mount_user vs the mount_base
	if not junction_path:
	    junction_path = netapp.mount_users + "/" + clone_owner + "/" + cname 

        # not always true - but for now, lets assume they are the same.
	unix_path = junction_path;

	# create banner message
	message  = self.print_banner()


	#---------------------------------------- 
        # Create NetApp clone from snapshot
	#---------------------------------------- 
        try:
	    # call subroutine to create flexclone on the filer
            exit_msg = netapp.clone_create(cname, sname, vname, junction_path)
        
	    # check exit status
            if exit_msg == "":
		message += "INFO: Successfully created flexclone volume %s\n" % cname
		message += "      mounted at: %s\n" % junction_path
	    else:
		print("action: RESPOND")
		message += "\nERROR: Failed to create flexclone volume %s\n" % cname
                message += exit_msg
		print("message: \"%s\"" % message)

        except NAException as e:
            print("action: RESPOND")
	    error  = "ERROR while trying to create flexclone volume."
            error += '\nNetApp Error: ' + e.error
	    message += error
            print("message: \"%s\"" % message)

	#---------------------------------------- 
	# p4 config setup for new clone
	#---------------------------------------- 
# MJ_ADD_CODE_CLONE              
        try:  
            # Verify parent client exists
            parent_client_name = FLEX_SNAP + vname + ":" + sname
            logging.debug("DEBUG: def clone: parent_client_name = %s\n", parent_client_name)

            list = p4.run_clients("-e", parent_client_name)
            if len(list) != 1:
                print("action: REJECT")
                print("message: \"Flex parent %s does not exist.\"" % parent_client_name)
                return
                        
            # Clone client workspace
            clone_client_name = FLEX_CLONE + cname
            logging.debug("DEBUG: def clone: clone_client_name = %s\n", clone_client_name)

            p4.client = clone_client_name
            clone_client = p4.fetch_client("-t", parent_client_name, clone_client_name)
            clone_client['Root'] = unix_path
            #clone_client['Options'] = clone_client['Options'].replace(" unlocked", " locked")
            p4.save_client(clone_client)
            
            # Generate P4CONFIG file
            logging.debug("DEBUG: def clone: unix_path = %s\n", unix_path)
            self.p4config(unix_path, clone_client_name)
        
            # Populate have list
            p4.run_sync("-k", "//" + clone_client_name + "/...@" + parent_client_name)
            
            # Set file ownership
            user = self.call.getUser()
            self.chown(user, unix_path)
        
            msg = clone_client_name + ". Mounted on " + unix_path + "."
            print("action: RESPOND")
            message += "Created flex clone client %s\n" % msg 
            print("message: \"%s\"" % message)
        
        except P4Exception:
            print("action: RESPOND")
            error = '\n'.join(p4.errors)
            error += '\n'.join(p4.warnings)
	    message += error
            print("message: \"%s\"" % message)
            
        finally:
            p4.disconnect()

              
	#---------------------------------------- 
	# Set file ownership
	#---------------------------------------- 
        try:  
	    chown_cmd_string = self.chown(clone_owner, junction_path)
	    message += "\nINFO: To change flexclone ownership to user <%s>\n" % str(clone_owner)
	    message +=   "      execute the following command:\n"
	    message +=   "      %s\n" % str(chown_cmd_string)
            print("action: RESPOND")
            print("message: \"%s\"" % message) 


        except P4Exception:
            print("action: RESPOND")
            message += '\n'.join(p4.errors)
            message += '\n'.join(p4.warnings)
            print("message: \"%s\"" % message)
            
        finally:
            p4.disconnect()

    
    #---------------------------------------  
    # check if user has permissions to run a command
    #---------------------------------------  
    def chown(self, user, junction_path):

	# directory containing this script
	config_dir = os.path.dirname(os.path.realpath(__file__))

        # Checks need to be done in case of failure
        uid = pwd.getpwnam(user).pw_uid
        gid = pwd.getpwnam(user).pw_gid

	# call CeChownList.pl to change file ownership
        # Examples:
        #         create a filelist called /my_path/dir_to_scan/filelist.BOM
        # 	        %> CeChownList.pl -user user_larry -d /my_path/dir_to_chmod/ -f /my_path/filelist_BOM
	cmd_line  = "sudo "
	cmd_line += config_dir + "/CeChownList.pl "
	cmd_line += " -user " + user
	cmd_line += " -d "    + junction_path
	cmd_line += " -f "    + junction_path + "/filelist_BOM"

	#subprocess.call(" "+cmd_line, shell=True )
	return cmd_line


        #try:
        #    # execute the system call to change ownership
        #    print("action: RESPOND")
        #    message  = self.print_banner()
        #    message += "DEBUG_MSG: CeChownList  <%s>" % cmd_line 
        #    print("message: \"%s\"" % message)
        #    
        #except NAException as e:
        #    print("action: RESPOND")
        #    message = "\nNetApp Error: " + e.error
        #    print("message: %s" % message)

    #---------------------------------------  
    # check if user has permissions to run a command
    #---------------------------------------  
    def isnfs(self, path):
        # Check if path is nfs mounted.
        fstype = subprocess.check_output('stat -f -L -c %T ' + path, shell=True)
        if (fstype == 'nfs\n'):
            return True
        return False

    #---------------------------------------  
    # Report list of flexclones
    #---------------------------------------  
    def list_clones(self):
        # Get options
        all = False 
        for o in self.opts:
            if o == "-a":
                all = True

	netapp = NaFlex()

	message = self.print_banner()
        
        try:  
            print("action: RESPOND")
	    message += netapp.list_flexclones()
            print("message: \"%s\"" % message)

        except P4Exception:
            print("action: RESPOND")
            error = '\n'.join(p4.errors)
            error += '\n'.join(p4.warnings)
	    message += error
            print("message: \"%s\"" % message)
            


    #---------------------------------------  
    # delete snapshot
    #---------------------------------------  
    def snap_del(self, volume_name, snapshot_name):

        # NetApp/Perforce connection as Flex
        netapp = NaFlex()
        p4 = P4Flex().getP4()

	message  = self.print_banner()

	# check that volume and snapshot names were passed to this function
        if not volume_name:
            print("action: REJECT")
            message += "No volume name provided\n"
            print("message: \"%s\"" % message)
            return

        if not snapshot_name:
            print("action: REJECT")
            message += "No snapshot name provided\n"
            print("message: \"%s\"" % message)
            return


	# check to verify that the volume and snapshot exist before cloning
	if not netapp.volume_exists(volume_name):
	    print("action: REJECT")
            message += "ERROR volume <\"%s\"> does not exist\n" % volume_name
            print("message: \"%s\"" % message)
	    return

	# check to verify that the volume and snapshot exist before cloning
	if not (netapp.snapshot_exists(volume_name, snapshot_name) == True):
	    print("action: REJECT")
            message += "ERROR snapshot <\"%s\"> does not exist\n" % snapshot_name
            print("message: \"%s\"" % message)
	    return
    
    
        # Delete Perforce snapshot
        try:
	    # call netapp api to delete snapshot
            exit_msg = netapp.snapshot_delete(volume_name, snapshot_name)

	    # check exit status
            if exit_msg == "":
		print("action: RESPOND")
		message += "INFO: Successfully deleted snapshot %s\n" % snapshot_name
		print("message: \"%s\"" % message)
	    else:
		print("action: REJECT")
		message += exit_msg
		print("message: \"%s\"" % message)
    
        except P4Exception:
            print("action: RESPOND")
            error = '\n'.join(p4.errors)
            error += '\n'.join(p4.warnings)
	    message += error
            print("message: \"%s\"" % message)            

            
    #---------------------------------------  
    # delete flexclone volume
    #---------------------------------------  
    def clone_delete(self, cname):               

	message  = self.print_banner()

        if not cname:
            print("action: REJECT")
	    message += "ERROR: No Flexclone name provided"
	    print("message: \"%s\"" % message)
            return

	# MJ_DEBUG: add clone name checking function
        ## verify that the flexclone exists before trying to delete it
        #if not netapp.volume_exists(volume_name):
        #    print("action: REJECT")
        #    print("message: ERROR flexclone volume <%s> does not exist\n" % volume_name)
        #    return
        
        # NetApp/Perforce connection as Caller
        netapp = NaFlex()
        #p4 = self.call.getP4()
        
        # If client delete succeed, Delete NetApp clone
        try:
            print("action: RESPOND")                  
            netapp.delete(cname)
	    message += "\nSuccessfully deleted FlexClone: %s\n\n" % cname
            print("message: \"%s\"" % message)
        
        except NAException as e:
            print("action: REJECT")
	    error  = self.print_banner()
            error += '\nNetApp Error: ' + e.error
	    message += error
            print("message: \"%s\"" % message)
            return
        
        except Exception as e: 
            print("action: REJECT")
            error = '\nUnexpected error: ' + str(e)
	    message += error
            print("message: \"%s\"" % message)
            return
            
            
    #---------------------------------------  
    # delete volume
    #---------------------------------------  
    def vol_del(self, vname):               

	# create banner message
	message  = self.print_banner()

        if not vname:
            print("action: REJECT")
	    message += "ERROR: No volume name provided.\n"
            print("message: \"%s\"" % message)
            return
        
        # NetApp/Perforce connection as Flex
        netapp = NaFlex()
        p4 = P4Flex().getP4()
        
        # Delete Perforce workspaces
        try:
            clones = p4.run_clients("-e", FLEX_SNAP + vname + "*")
            
            list = ""
            for c in clones:
                client_name = c['client']
                p4.run_client("-f", "-d", client_name)
                list += "   deleted client: %s\n" % client_name
            
            print("action: RESPOND")
            message += "INFO: Successfully deleted volume %s\n" % vname
            message += list
            print("message: \"%s\"" % message)
            
        except P4Exception:
            print("action: RESPOND")
            error = '\n'.join(p4.errors)
            error += '\n'.join(p4.warnings)
	    message += error
            print("message: \"%s\"" % message)
            
        finally:
            p4.disconnect()
            
        # If client delete succeed, Delete NetApp volume
        try:
            netapp.delete(vname)
        
        except NAException as e:
            print("action: REJECT")
            error = '\nNetApp Error: ' + e.error
	    message += error
            print("message: \"%s\"" % message)
            return
        
        except Exception as e: 
            print("action: REJECT")
            error = '\nUnexpected error: ' + str(e)
	    message += error
            print("message: \"%s\"" % message)
            return
    
    #---------------------------------------  
    # P4 config info??
    #---------------------------------------  
    def p4config(self, path, client):
        p4config = os.getenv('P4CONFIG', '.p4config')
        p4port = self.call.getPort()
        p4user = self.call.getUser()
        p4config_file = path + "/" + p4config
        
        logging.debug("DEBUG: def p4config_file: open for writing = %s\n", p4config_file)
        #fh = open(path + "/" + p4config, "w")
        fh = open(p4config_file, "w")
        fh.write("# Generated by p4 flex.\n");
        fh.write("P4PORT=" + p4port + "\n");
        fh.write("P4USER=" + p4user + "\n");
        fh.write("P4CLIENT=" + client + "\n");
        fh.close()
        
    #---------------------------------------  
    # Display help information
    #---------------------------------------  
    def help(self):
        help = (
            "P4 FlexClone Usage Information\n\n"
            "    P4 Broker functions for creating and managing NetApp FlexClones\n\n"
            "\n"
            "SYNOPSIS\n"
            "    p4 flex [command] [command options]\n"
            "\n"
            "DESCRIPTION\n"
	    "    Create Volume\n"
            "      p4 flex volume -s <vol size[M, G]> [-u <volume owner>] [-j <junction_path>] <volume name>\n"
	    "    Delete Volume\n"
            "      p4 flex volume -d <volume name>\n"
	    "    List Volumes\n"
            "      p4 flex volumes \n"
            "      p4 flex list_volumes \n"
            "      p4 flex lv\n"
	    "\n"
	    "    Create Snapshot\n"
            "      p4 flex snapshot -V <volume volume> [-c client] <snapshot name>\n"
	    "    Delete Snapshot\n"
            "      p4 flex snapshot -V <volume name> -d <snapshot name>\n"
	    "    List Available Snapshots (with parent volume)\n"
            "      p4 flex snapshots      -V <volume name (optional)>\n"
            "      p4 flex list_snapshots -V <volume name (optional)>\n"
            "      p4 flex ls             -V <volume name (optional)>\n"
	    "\n"
	    "    Create FlexClone (aka clone)\n"
            "      p4 flex clone -V <volume> -S <snapshot name> [-u <clone owner>] [-j <junction_path>] <clone name>\n"
	    "    Delete FlexClone\n"
            "      p4 flex clone -d <clone name>\n"
	    "    List FlexClones\n"
            "      p4 flex clones -V <volume name (optional)> [-a]\n"
            "      p4 flex list_clones -V <volume name (optional)> [-a]\n"
            "      p4 flex lc -V <volume name (optional)> [-a]\n"
            "\n"
            "EXAMPLES\n"
            "    Create a new 10GB volume called 'android_builds'\n"
	    "      %> p4 flex volume -s 10G android_builds\n"
            "    Create a new 20GB volume called 'android_nightly_builds'\n"
            "      junctioned at a specific location and with a different directory name.\n"
	    "      %> p4 flex volume -s 20G -j /ce_project/android/android_builds android_nighly_builds\n"
	    "\n"
	    "    Create a snapshot for volume 'android_builds' called 'android_builds_snap1'\n"
	    "      %> p4 flex snapshot -V android_builds android_builds_snap1\n"
	    "\n"
	    "    Create a flexclone called 'android_builds_snap1_clone1' based on a snapshot 'android_builds_snap1' from volume 'android_builds'\n"
	    "      %> p4 flex clone -V android_builds -S android_builds_snap1 android_builds_snap1_clone1\n"
	    "\n"
	    "    List the available volumes, snapshots and clones\n"
	    "      %> p4 flex list_volumes     or  %> p4 flex lv\n"
	    "      %> p4 flex list_snapshots   or  %> p4 flex ls\n"
	    "      %> p4 flex list_clones      or  %> p4 flex lc\n"
	    "\n"
	    "    Delete clone, snapshot and volume\n"
	    "      %> p4 flex clone    -d android_builds_snap1_clone1\n"
	    "      %> p4 flex snapshot -V android_builds -d android_builds_snap1_clone1\n"
	    "      %> p4 flex volume   -d android_builds\n"
	    "\n"
	    " Additional Notes:\n"
	    "    Snapshots: can only be deleted IF the snapshot is not in use.  If a FlexClone based on the snapshot exists, then the snapshot\n"
	    "               can't be deleted, until all flexclones associated with the snapshot are deleted.\n"
	    "    Volumes:   can only be deleted IF all snapshot/flexclone pairs based on the volume are deleted.\n\n"
        )
        print("action: RESPOND")
        print("message: \"%s\"" % help)
        
    #---------------------------------------  
    # report invalid command options passed to p4 flex [command]
    #---------------------------------------  
    def usage(self):
        usage = (
            "ERROR: Invalid or missing command. %> p4 flex [command]\n"
            "       For help including a list of options and examples;\n"
	    "         %> p4 flex help\n"
        )
        print("action: RESPOND")
        print("message: \"%s\"" % usage)

# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    flex = Flex()

    
    
    

