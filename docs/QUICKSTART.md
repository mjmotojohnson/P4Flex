################################################################################
# Perforce P4 Flex QuickStart Guide
################################################################################

****************************************
   Introduction 
****************************************
The challenge for developers who work with large volumes of data such as 
multimedia assets, video game art, and firmware designs, etc, is the ability 
to get a quick copy of source and build assets. By using NetApp Snapshot 
and FlexClone technologies  a new workspace can be created in minutes instead of hours.

I want to introduce you to Perforce P4 Flex, NetApp's methodology for DevOps. P4 Flex
utilizes NetApp's FlexClone technology to save TB of Developer workspaces and
save developers hours of time by reducing the time to checkout and build their
workspaces.  NetApp's own internal DevOps team has been using FlexClone technology
in thier software build/release flow for over 7 years and we have recently packaged up 
P4 Flex into an Toolkit for easy adoption by our customers.
 
P4 Flex is a methodology for DevOps which utilizes NetApp?s SnapShot and FlexClone 
technologies to dramatically save developer checkout and build time while also 
significantly decreasing storage usage. The P4 Flex Toolkit utilizes the 
NetApp Manageabilitys SDK to automate the steps required to create and manage 
developer FlexClone workspaces.  The best thing is P4 Flex fits into most DevOps 
environments with little to no changes.  

The P4 Flex broker is so easy, that within 2 hours , you can see both the time 
and storage savings found by utilizing NetApp technologies.  The P4 Flex broker can accelerate 
dev-to-production cycles, and minimize the resources needed for every dev/test environment, 
lowering the toll on the storage system and allowing you to run more such systems in 
parallel. It also makes cleanup much faster and tighter. 

A few examples: 
- NetApp's internal SW organization has been using FlexClones in their Dev flow for over 7 year.  
  Our figures show that using FlexClones saves roughly 100 man years per year.

- A Silicon Valley network chip manufacturer was able to reduce their checkout and build time 
  from about 55 minutes to 5 minutes and at the save time save an average of 200GB 
  per developer workspace. 
 
****************************************
  Scope 
****************************************
The P4 Flex Toolkit scripts are an open-source shared with the developer community to refine and customized. Each development environment is unique and may have requirements of security, control, workflow, etc. Thus this script is meant to be only as a starting reference which can be enhanced to support requirements of your specific development environment.

Support for this script is through the NetApp community forums. Questions and issues should be posted there for further guidance.  

****************************************
  Requirements  
****************************************
Requirements

In order to be able to utilize P4 Flex the following is required:

- Python 2.6 or later (Python 2.7 recommended)
- P4 Python 2.6 or later APIs (Python 2.7 recommended)
- ONTAP 8.2 or later (7-mode is not supported)
- NetApp Manageability Software Development Kit (NMSDK) 5.3.x or later


****************************************
  Support 
****************************************
Currently P4 Flex is only supported for Unix environments and NFS.

In order to be able to utilize P4 Flex Toolkit the following is required:


****************************************
## Assumptions ##
****************************************

To use P4 flex, the following are assumed.

SERVER:

- P4D Server is installed and running
- P4Broker installed
- LDAP is running or an existence of user accounts and authentication management.
- NetApp Cluster Mode Storage Data ONTAP 8.x is used with FlexClone and NFS license enabled
 
CLIENT:

- NFS Client is running on host in order to NFS mount NetApp storage and volume 
- Netapp filer mounted on client box
- The "p4 client" is installed.

****************************************
## Components ##
****************************************

The p4 flex script is written in python and is run in behalf of the user by the p4broker. The p4 flex consists of the following files:

- p4flex_broker.cfg - p4 broker configuration file that defines the ports and location of flex.py script  
- p4flex.cfg - p4 flex configuration file that defines the variables needed to run p4 flex such as p4 admin user information and NetApp admin user information
- p4flex.py - python script that provides the functionality to create template, create clone and delete Perforce workspaces quickly


****************************************
## Setup and Installation
****************************************
    STEP 1: Download and install the NetApp Managability SDK 
	a. The SDK can be found on the mysupport.netapp.com 
	   Downloads -> Software -> NetApp Manageability SDK
	   Select "All Platforms" -> Go!
	   Select "NetApp Manageability SDK 5.5" -> View & Download

	   After clicking thru the EULA etc, you will get a file netapp-manageability-sdk-5.5.zip

        b. Unzip the NMSDK in /usr/local/lib
	   find a spare directoryt directory and unzip netapp-manageability-sdk-5.5.zip
	   %> cp -r netapp-manageability-sdk-5.5 /usr/local/lib/    (this is the location specified in p4flex.py)

    STEP 2: Download and install the Perforce broker components
	a. Download P4 Python APIs based on your Linux and architecture (ie. perforce-p4python-python*). 
           Follow instructions on how to setup the linux repositories to pull the APIs from Perforce 
           from the link below:
           http://package.perforce.com/

        b. Download the P4 broker (ie. perforce-broker) if not yet installed. 
           Use same same site defined above. 

        c. P4 Python APIs and p4 Broker use yum install or apt-install after repositories are set. For example, RHEL 7:
			sudo yum install perforce-p4python-python2.7
		
			sudo yum install perforce-broker


    STEP 3: Download the Perforce P4 flex scripts from Swarm
           P4 Flex scripts from Perforce workshop. Download all files or just the zip file.
           https://swarm.workshop.perforce.com/projects/netapp-p4flex/

    STEP 4.  
        a. Copy the broker.cfg in the same location as where the Perforce configuration files are 
           usually located (ie. /opt/perforce/servers/p4broker-master or /etc/perforce)
           OR: you can find a sample broker.cfg in the P4 Flex download at demo/broker.cfg

        b. Modify the broker.cfg. The parameters to modify in the broker.cfg include:
	- target = *port of p4d*;
	- listen = *port of p4broker*;
	- directory = *P4ROOT*;
	- execute = *location of flex.py script*;
   
     STEP 5. Start the p4broker using the broker.cfg as "perforce" or perforce admin user.
        There is a 'demo/start.sh' script which can be used to start the p4broker.
        The script is useful for understanding how to start and stop the service. 

	If running p4broker as a unix service, modify /etc/perforce/p4dctl.conf.d/p4broker-master.conf to point to the appropriate p4broker config file (broker.cfg).:
	
	```
	sudo p4dctl start p4broker-master
	```

	Manually:

	```
	p4broker -c /etc/perforce/p4flex/broker.cfg -d
	```
      STEP 6. Setup P4 access controls
        The P4 access controls provide a mechanism for controlling access to who can run certain P4 Flex 
        operations.  For instance you may want to restrict volume and snapshot creation to a 'build' user
        or a 'perforce' admin user.  But then you might allow any user to create and delete flexclones.

        NOTE: this QUICKSTART does not go into detail on how to setup Perforce admin permissions.  
        The following is just a simple example approach.
 
        Create a p4 super admin user.  The "flex" is a P4 super user and will be running the p4broker 
        commands. Thus as "perforce" or 'devops' or admin user of perforce process do the following:
   
		su - perforce
		export P4PORT=1667
		export P4USER=perforce
		p4 login
		p4 user -f flex
		p4 passwd flex
		p4 protect
		
		Add the following line before super user perforce in protections file:
				super user flex * //...
		
      STEP 7. Modify the flex.cfg file with information relating to P4 Flex and NetApp admin.  
        The flex.cfg file is read by the flex.py process and provides configuration information
        for accessing the NetApp filer and other parameters. The is a sample demo/flex.cfg file provided.

        You will need a IT/Storage/Perforce admin to help fill in the following information.
        The parameters to modify include:
	- port: *port of p4broker*
	- passwd: *password of "flex" admin*
	- server: *IP address or qualified name of NetApp filer data lif*
	- admin_user: *admin access nam to NetApp filer*
	- admin_passwd:*admin password of NetApp filer*
	- vserver: *name of vserver created that would have volume templates and clones*
	- aggr: *aggregate that would contain the volume templates and clones*
	- mount_base: *directory where the NetApp filer root will be mounted on*
	
	Optional:
	- snap: *prefix of snapshot name. default is flexSnap_*
	- clone: *prefix of clone name. default is flexClone_*

    

****************************************
  Setup sudo for user 'devops'
****************************************
    User 'devops' or similar user is the user who will own the master volume
    which gets cloned by users.  The 'devops' user or equivalent will need
    permissions to change the ownership 'chown' the files in the cloned
    volume.  

    Setup 'sudo' permission for trusted users - like devops
    As root use the 'visudo' command to edit the sudo permission.

    Add the following line - then exit.  
	# add sudo permissions for user 'devops'
	# this will enable user to run command without requiring a password.
	devops     ALL=(ALL)       NOPASSWD: ALL
	perforce   ALL=(ALL)       NOPASSWD: ALL

    NOTE: there might be more restrictive sudo settings.  For simplicity
    the above setting allow full sudo access.


****************************************
  Filers Export_policy - volumes need root superuser access
****************************************
In order for "sudo chown" to modify the clones owner:group settings, the
NetApp vserver export_policies must allow root super user permissions on the
volume and flexclones.  If you run sudo chown and you get a permission denied
message, then most likely the volumes export_policy restricts root superuser
operations.  Test that %> sudo chown <a file> works correctly.  If this
command does not work, then CeChownFile.pl will not work either.


****************************************
  ONTAPI filer permission setup
****************************************
    To enable filer access via the NetApp Manageability SDK vserver
    permissions must be setup to enable 'ontapi' and 'ssh' access permissions.

    Read the file ONTAPI_SETUP file in the P4 Flex/docs directory for full
    instructions.

    Example: CREATE A USER ACCOUNT "devops" FOR ONTAPI ON THE CLUSTER VSERVER
	cluster::> security login create -vserver clusterab -username devops \
                     -application ontapi -authmethod password -role rsa
	cluster::> security login create -vserver clusterab -username devops \
                     -application ssh -authmethod password -role rsa

        cluster::> security login show

****************************************
  IMPORTANT: Critical setup for Cluster Interface access
             If this is not done, you will get a login/connection error
****************************************
        cluster::> network interface modify -vserver <vserver> -lif <lif> -firewall-policy mgmt
        cluster::> vserver modify -vserver <vserver> -aggr-list <aggrname>



****************************************
  Setup Project Volumes
****************************************
    REFERENCE: <codeeasy dir>/doc/Project_Example.txt to see UNIX/volume/junction_path mappings

    This is just an example implementation to demonstrate how the FlexClone and junction_path mounts work.  
    RECOMMENDATION: get this implementation working, then customize the setup for your specific project structure.

    Step #1 Create top level project volume - ce_projects
       This will be the root of the junction_path

       vserver::> volume create -volume ce_projects -junction_path /ce_projects -policy codeeasy_exports \
                                -security-style unix -unix-permissions ---rwxrwxrwx <other options>

    Step #2 NFS mount top level project volume (or edit /etc/fstab or update automount)
       New volumes and flexclones will use junction paths relative to this mount point. 
       The following mounts using nfsv3

       UNIX %> sudo mount -t nfs vserver:/ce_projects /ce_projects -o nfsvers=3

       Change permissions so users can access this volume
            %> sudo chmod 777 /ce_projects
            %> cd /ce_projects
            %> ls 


    Step #4 Create continuous build area (jenkin) volume
       NOTE: the volume and junction_path names are different.  The volume name will be unique in the case there is a project_B_jenkin_build volume.
             Again this is just a suggested volume/flexclone/unix structure.

       vserver::> volume create -volume project_A_jenkin_build -junction_path /ce_projects/project_A/jenkin_build -policy codeeasy_exports \
                                -security-style unix -unix-permissions ---rwxrwxrwx <other options>

    Step #5 Check that the directory is mounted and read/writeable
       UNIX %> cd /ce_projects/project_A/jenkin_build
            %> cp <misc data into this directory as test case data to be cloned>
            


****************************************
  Setup and Test P4 Flex Script
****************************************

    ----------------------------------------
    Edit flex.cfg
    ----------------------------------------
    Open and edit the file demo/flex.cfg

    The flex.cfg file contains all the default values for UNIX and vserver
    setup.  The file is well commented, so read thru the file and edit each
    line as required to localize the script to your environment. 

    ----------------------------------------
    Test the P4 Flex Scripts 
    ----------------------------------------
    Make sure basic filer connections work.  The following example will connect to the filer
    and then list the available volumes.

    Example:
    %> p4 flex volumes
	INFO  (CeCreateSnapshot.pl): Connecting to storage controler/vserver
		vserver        = sv5-devops-01
		transport_type = HTTP
	INFO  (CeCreateSnapshot.pl): Storage Controller <sv5-devops-01> is running ONTAP API version:
	      NetApp Release 8.2.1RC2X6 Cluster-Mode: Wed Dec 18 19:14:04 PST 2013 

    Resolve Errors
    If the test option returns an error, most likely it is due to misconfigured options in the 
    flex.cfg file. Check that the vserver user login has both ontapi and ssh access permissions 
    enabled.  


****************************************
  Devops Flow Steps
****************************************

    Login as user 'devops'
	%> su - devops

    ----------------------------------------
    Setup Steps
    ----------------------------------------
    Step #0: Check if the 'p4 flex help' is working.
        %> p4 flex help

SYNOPSIS
    p4 flex [command] [command options]

DESCRIPTION
    Create Volume
      p4 flex volume -s <vol size[M, G]> <volume name>
    Delete Volume
      p4 flex volume -d <volume name>
    List Volumes
      p4 flex volumes
      p4 flex list_volumes
      p4 flex lv

    Create Snapshot
      p4 flex snapshot -V <volume volume> [-c client] <snapshot name>
    Delete Snapshot
      p4 flex snapshot -V <volume name> -d <snapshot name>
    List Available Snapshots (with parent volume)
      p4 flex snapshots      -V <volume name (optional)>
      p4 flex list_snapshots -V <volume name (optional)>
      p4 flex ls             -V <volume name (optional)>

    Create FlexClone (aka clone)
      p4 flex clone -V <volume> -S <snapshot name> -u <cloan owner (opt)> <clone name>
    Delete FlexClone
      p4 flex clone -d <clone name>
    List FlexClones
      p4 flex clones -V <volume name (optional)> [-a]
      p4 flex list_clones -V <volume name (optional)> [-a]
      p4 flex lc -V <volume name (optional)> [-a]


    Step #1A: Mount Junction Path
	      New volumes and flexclones will use junction paths relative to
	      this mount point. 
	
	%> sudo mount -t nfs <vserver>:<filer path>      <UNIX mount point>

	%> sudo mount -t nfs vserver:/ce_projects /ce_projects

        change permissions so users can access this volume
        %> sudo chmod 777 /ce_projects


    Step #1B: Compile sur and fast_chown scripts
	This step requires sudo previleges - which in this case user 'devops' has
	sudu permissions setup to perform various operations - which needs to be
	detailed (TBD). These scripts can also be compiled as root if needed.

	%> cd <P4 Flex dir>/demo
	%> make all

	This should build 'sur' and 'fast_chown' executables.  To clean and re-try
	the compile
	%> make clean all


    ----------------------------------------
    Continuous Integration Flow Steps
    ----------------------------------------
    Step #2: Create new volume (*** SKIP THIS STEP IF YOUR VOLUME ALREADY EXISTS ***)
	%> ./CeCreateVolume.pl -vol jenkins_build

	This will create a volume which is automatically mounted at /ce_projects/project_A/jenkin_build 
	because we specified a junction-path, user_id, group_id, and unix-permissions with the volume-create
	command, the new volume is mounted and permission set ready to go.

	NOTE: the default volume name can be set in the CeInit.pm file 
	      look for the variable $CE_DEFAULT_VOLUME_NAME 

    Step #3: Populate the test volume with project data
	This of course will be a Perforce or GiT checkout of some sort.  For the
	purposes of this initial testing without a RCS tool, we can just copy a
	bunch of files - of significant size - to the new volume.

	%> cp -R netapp-manageability-sdk-5.4 /ce_projects/project_A/jenkin_build/

    Step #4: Create a file list to be later when changing ownership of the flexclone

	%> ./CeFileListGen.pl -d /ce_projects/project_A/jenkin_build

	This step will create a file in the volume called /ce_projects/project_A/jenkin_build/filelist_BOM
	Again this file will be read by the CeChownList.pl script to change the
	flexclone directory and file ownership from the Daemon (aka build user)
	ownership to the new users ownership.

    Step #5: Create a Snapshot called project_A_snap_20150811
	%> p4 flex snapshot -V jenkin_build project_A_snap_20150811

	There should now be a new snapshot at /ce_projects/project_A/jenkin_build/.snapshot/project_A_snap_20150811

	If the default volume name is set in the CeInit.pm file, then the -vol <volume name> can be excluded from the command line.


****************************************
  Developer (aka normal user) Flow Steps
****************************************
    Switch back to normal user
	%> exit     (if logged in as devops)


    Step #1: Create a FlexClone based on the Snapshot created in step #5

	%> p4 flex clone -V jenkins_build -S project_A_snap_20150811 project_A_snap_20150811_clone

	There should now be a FlexClone volume mounted at UNIX path /ce_projects/project_A/users/<USER>/project_A_snap_20150811_clone
	Note that the permissions at this point on the files and directories are
	the same as that of the Snapshot from which it came.

	If the default volume name is set in the CeInit.pm file, then the -vol <volume name> can be excluded from the command line.

    Step #2: Change ownership of the FlexClone volume to that of the current user

	%> ./sur ./CeChownList.pl devops -d /ce_projects/project_A/users/<USER>/project_A_snap_20150811_clone -u jmichae1

	The FlexClone volume should now have the permission of the normal
	users - in this case user 'jmichae1'.  

    Step #3: Update Source Control setup
	Since this example does not use Perforce, SVN, GiT or CVS there is
	nothing to do.  

	Perforce - post FlexClone command
	    %> p4 client
	    %> p4 flush
	    --> You are all set and ready to develop as normal

	GIT or SubVersion (SVN)
	    You don't need to do anything.
	    --> You are all set and ready to develop as normal

	CVS
	    Modify the CVS/Root files recursively thru the volume to change username
	    %> find . name Root -type f | xargs -P 140 perl -pi -e 's/old_user/new_user/g'
	    --> You are all set and ready to develop as normal





****************************************
Understanding the chown flow 
****************************************
When a FlexClone is created, the clone retains the user and group permissions
of the person who owns the master volume.  In order to make the FlexClone
fully usable by the new owner, the files must be chown?ed.  The new clone
owner does not have permission to chown the files themselves, another user
with sufficient permissions must change the ownership of the files and
directories.

Since there are potentially millions of files and directories in the volume,
the time to 'chown' the volume can be quite significant - potentially hours.
The P4 Flex Toolkit contains optimized scripts for speeding up the process
of chown'ing the files.  The first speed up comes from the use of fast_chown.c
which uses lchown which runs faster then conventional UNIX chown.  Second the
process of finding the files to chown has been split from the process of
actually doing the chown command itself.  A script called CeFileListGen.pl is
provided to generate a file list very fast by essentially performing massively
parallel find commands. By splitting the find operation from the chown
operation, this allows the CeFileListGen.pl script to be run in the master
volume by the central build scripts. This means that the user does not see the
time to 'find' the files.  The FlexCloned volume will have a file called
filelist_BOM (bill of materials) which is a list of all the files in the
master volume.  Lastly a script called CeChownList.pl reads the filelistBOM
file and then using the xargs parallel option runs fast_chown on the each
file.  The result is a massive volume of files can be chowned in 10x faster.

****************************************
Sudo Permissions and the sur command
****************************************
The owner of the master volume - like a flow owner 'devops' will run the
scripts for doing things like creating volumes, snapshots, flex clones and
chowning files.  The 'devops' user requires sudo permissions to be able to do
things like chown.  By default a user can not change the ownership of a file
from themselves to another user without sudo permissions.  Its a security
thing - typically only root is allowed to change file ownership from one user
to another.  As a result the 'devops' or equivalent users must have the
following sudo options enabled.

Using the 'visudo' command   (%> visudo)  Add the following lines to the sudo
file
    # add sudo permissions for user 'devops'
    # this will enable user to run command without requiring a password.
    devops  ALL=(ALL) NOPASSWD: ALL

The sur.c program command is a script which is provided by the P4 Flex Toolkit
to enable a normal user to switch to user 'devops' to run commands like
creating a flex clone or chowning a volume.  The compiled program 'sur'
essentially does a 'setuid' then runs the called script.  
Example:
    %jmichae1> ~jmichae1/P4 Flex/src/sur devops CeChownList.pl -d $PWD -u jmichae1

In the above example sur will setuid to user devops, then call the
CeChownList.pl script to chown the files to user jmichae1.  Note that the UNIX
shell is current run as user jmichae1, so the sur command switches setuid to
user devops.  


