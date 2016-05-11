# P4 FLEX #

----------

## Introduction ##
The challenge for developers who work with large volumes of data such as multimedia assets, video game art, and firmware designs, etc, is the ability to get a quick copy of source and build assets. By combining the technologies of Perforce and NetApp, a new Perforce workspace can be created in minutes instead of hours.  Perforce in collaboration with NetApp has developed a p4 broker script written in python that allows users to create workspaces quickly using NetApp FlexClone technology.
 
## Scope ##
The P4 flex script is an open-source p4 broker script which is shared to the developer community to refine and customized. Each development environment is unique and may have requirements of security, control, workflow, etc. Thus this script is meant to be only as a starting reference which can be enhanced to support requirements of your specific development environment.

Support for this script is through the developer community forums in which both Perforce and NetApp are members. Questions and issues should be posted  there for further guidance.

## Requirements  ##

In order to be able to utilize P4 Flex the following is required:

- Python 2.6 or later
- P4 Python 2.6 or later APIs
- NetApp Manageability Software Development Kit (NMSDK) 5.3.x or later

## Support ##

Currently P4 Flex is only supported for Unix environments and NFS.

## Assumptions ##

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

## Components ##

The p4 flex script is written in python and is run in behalf of the user by the p4broker. The p4 flex consists of the following files:

- p4flex_broker.cfg - p4 broker configuration file that defines the ports and location of flex.py script  
- p4flex.cfg - p4 flex configuration file that defines the variables needed to run p4 flex such as p4 admin user information and NetApp admin user information
- p4flex.py - python script that provides the functionality to create template, create clone and delete Perforce workspaces quickly

## Setup and Installation ##

The setup and install is expected to be run by IT administrators who manages the Perforce and NetApp infrastructure. 

1. Download:
	 - P4 Python APIs based on your Linux and architecture (ie. perforce-p4python-python*). Follow instructions on how to setup the linux repositories to pull the APIs from Perforce from the link below:
		 - [http://package.perforce.com/](http://package.perforce.com)
	 - P4 broker (ie. perforce-broker) if not yet installed.  Use same same site defined above.
	 - NetApp Manageability SDK.  Download from this site:
		 - [http://mysupport.netapp.com/NOW/cgi-bin/software?product=NetApp+Manageability+SDK&platform=All+Platforms](http://mysupport.netapp.com/NOW/cgi-bin/software?product=NetApp+Manageability+SDK&platform=All+Platforms)
	 - P4 Flex script from Perforce workshop.
		 - [https://swarm.workshop.perforce.com/projects/netapp-p4flex/](https://swarm.workshop.perforce.com/projects/netapp-p4flex/files/)

	 
2. Install. 
	 - P4 Python APIs and p4 Broker use yum install or apt-install after repositories are set. For example, RHEL 7:
		
			sudo yum install perforce-p4python-python2.7
		
			sudo yum install perforce-broker
		

	 - Uzip NetApp Manageability in /usr/local/lib 
	 
			find a spare directoryt directory and unzip netapp-manageability-sdk-5.3.1.zip
			cp -r netapp-manageability-sdk-5.3.1 /usr/local/lib/    (this is the location specified in p4flex.py)

3.  Copy the broker.cfg in the same location as where the Perforce configuration files are usually located (ie. /opt/perforce/servers/p4broker-master or /etc/perforce)

4.  Modify the broker.cfg. The parameters to modify in the broker.cfg include:
	- target = *port of p4d*;
	- listen = *port of p4broker*;
	- directory = *P4ROOT*;
	- execute = *location of flex.py script*;
   
5. Start the p4broker using the broker.cfg as "perforce" or perforce admin user.

	If running p4broker as a unix service, modify /etc/perforce/p4dctl.conf.d/p4broker-master.conf to point to the appropriate p4broker config file (broker.cfg).:
	
	```
	sudo p4dctl start p4broker-master
	```

	Manually:

	```
	p4broker -c /etc/perforce/p4flex/broker.cfg -d
	```
6.  Create a p4 super admin user.  The "flex" is a P4 super user and will be running the p4broker commands. Thus as "perforce" or admin user of perforce process do the following:
   
		su - perforce
		export P4PORT=1667
		export P4USER=perforce
		p4 login
		p4 user -f flex
		p4 passwd flex
		p4 protect
		
		Add the following line before super user perforce in protections file:
				super user flex * //...
		
7.  Modify the flex.cfg file with information relating to P4 Flex and NetApp admin.  Information on parameters is provided by the Perforce and/or NetApp administrator.  The parameters to modify include:
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

8. Create a mount_base directory that is specified int flex.cfg file for instance "/p4" to mount the root directory of NetApp filer. Modify permissions such that users can access it.

		sudo mkdir /p4 
		sudo chmod 777 /p4

9. Mount the NetApp filer to mount_base (ie. /p4):
		
		sudo mount -t nfs -o vers=3 192.168.25.19:/ /p4

10. Modify /etc/sudoers to only provide permissions to perforce admin user to be able to do certain sudo commands. For example, add the following line in /etc/sudoers:

		perforce        ALL=(ALL)       NOPASSWD: ALL
11. On each user machines who will be using P4 flex, repeat steps 8-9 above which is to create the mount_base and mount the filesystem.

## Commands ##
Below is the output of "p4 flex help".  For examples of usage, please refer to the Workflow in the next section.

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

## Workflow  ##

For P4 flex commands to work, the following is required:

- P4 user and/or P4 admin are registered P4 users
- P4PORT should be set to the port of the p4broker
- P4USER is defined and logged on


1. P4 admin creates a template in which others can clone from which involves the following:
	- Create a volume  
	
		``` 
		p4 flex volume -s 1G projA
		``` 
	- Populate workspace with existing sources checked into Perforce

		``` 
		p4 sync
		```

	- Build

		```
		make
		```
	- Create a snapshot
		
		```
		p4 flex snapshot -V projA -c test snapA
		```

2. P4 users can list snapshots/templates available to clone and create a workspace

		p4 flex snapshots
 
3. P4 users can create a new Perforce writable clone workspace (wsA) from the template/snapshot volume projA and snapA

		p4 flex clone -V projA -P snapA wsA

4. When users are done with the workspace, P4 users can remove the cloned workspace, followed by the snapshots if they will not be used again. 

		p4 flex clone -d wsA
		p4 flex snapshot -V projA -d snapA

5. P4 flex admin is the only user allowed to delete the volume template since deleting volume will delete all snapshots/template.  This command will fail if there are cloned workspace associated with this volume.

		p4 flex volume -d projA

## Considerations ##
	
Using P4 Flex to create Perforce workspaces can improve developer productivity; however there are some things to consider and be aware of which include: 

- Cleanup of cloned workspaces in order to not leave numerous abandoned workspaces via ``` p4 flex clone -d ```
- If one employs a bisect workflow for continuous integration testing, make sure that the bisect workflows employs the 'p4 sync/flush –p' variant to prevent spamming the server
- There are limitation to the number of FlexClones that can be created per volume.  Please refer to the Data ONTAP documentation of your release.  For instance, in Data ONTAP 8.1, there is a limit of 32,767 Flex Clones per volume.
- Certain Perforce operation (ie, flush or sync) requires exclusive locks on several important db.* files to preserve atomicity.  Commands needing locks on any of the db.* files will be blocked until the command has completed. Running numerous flushes and sync operations can affect performance. However, using NetApp SAN protocols such as FCP and iSCSI for the Perforce database can alleviate this issue.

## Known Issues ##


- Possible security hole in P4broker.  Will be fixed in later release of P4broker. 


## References ##

P4Broker

- [http://www.perforce.com/perforce/doc.current/manuals/p4dist/chapter.broker.html](http://www.perforce.com/perforce/doc.current/manuals/p4dist/chapter.broker.html)

FlexClone - A Thorough Introduction to FlexClone

- [http://www.netap.com/us/media/tr-4164.pdf](http://www.netap.com/us/media/tr-4164.pdf)


Deployment and Implementation Guide: Perforce Software on NetApp Clustered Data ONTAP

- [http://www.netapp.com/us/media/tr-4164.pdf](http://www.netapp.com/us/media/tr-4164.pdf)

Data ONTAP Administration Manuals refer to the Documentation section from:

- [http://now.netapp.com](http://now.netapp.com)
