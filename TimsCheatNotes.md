## Flexclone Perforce Workspaces
The following notes describe the process of creating a Perforce workspace that incorporates a NetApp, flexcloned NFS mount for the workspace's client root. The high-level process is as follows:

1. Create volume on NetApp filer (storage system).
2. Make volume accessible via export and mount on host's server.
3. Run "p4 sync" on host to populate the template workspace.
4. Run the build process in the template workspace to generate build artifacts.
5. Create snapshot of volume that contains the pre-built workspace on NetApp filer
6. Create clone from snapshot.
7. Export the cloned volume on filer and then mount clone onto host.
8. Change ownership (by this we mean change the ownership of every file/dir in the tree to be owned by the user you want to give the volume to). Can be done efficiently by creating a script that takes a User ID (uid) as a numeric value and a list of files, which then calls the chown system call for each file - setting the owner to the passed uid. If the number of files or list is of files is large, one can use 'xargs' to split the list into multiple invocations of the script.- NOT DONE IN THIS DEMO SINCE THE SAME USER WAS USE FOR TEMPLATE AND CLONED ENVIRONMENTS
9. Define a Perforce client to let Perforce know the existence of the new workspace, modifying fields such as Root directory and Owner with user-specific information.
10. Run "p4 flush" to make the workspace think it has the file content already. (If you are not cloning at the head revision of the data, you can use the template workspace as a revision specifier.) NOTE: If clone is used only for builds and no edits are needed, then flush is not required.
11. (Optional) Run 'p4 reconcile' to verify that the workspace data is consistent. Ignore any build artifacts that are not kept in the Perforce repository.

 --Steps to Create a Flexcloned Perforce Client--
 First, you need to log into the Performance Lab's NetApp filer.

    ssh fas3270-1m.pl.perforce.com -l admin
    Password:

For the purpose of this demo, I am referring to the parent-source-volume as the *template volume*. The primary-source-Perforce-client is referred to as the *template client*. This helps identify it as the source as opposed to the flexcloned volume and Perforce client.

The NFS template volume will be created using aggregate aggr1 which consists of 6.73TB of total diskspace.

    fas3270::> aggr show -aggregate aggr1 -fields size
    aggregate size   
    --------- ------ 
    aggr1     6.73TB 

The template volume will be called vol1 and is will be 1TB in size. The following commands create the volume, enable it as an NFS volume, and initialize export policies for that volume.

    fas3270::> vol create -volume vol1 -vserver vserver1 -size 1TB  -aggregate aggr1 -state online -type RW -policy default -unix-permissions ---rwxrwxrwx
     (volume create)
    [Job 9893] Job succeeded: Successful       

    fas3270::> vserver nfs create -vserver vserver1  -access true -v3 enabled

    fas3270::> vserver export-policy rule create -vserver vserver1  -policyname default -clientmatch 0.0.0.0/0 -rorule any -rwrule any -anon 0 -superuser none

    fas3270::> vol show vol1                           
      (volume show)
    Vserver   Volume       Aggregate    State      Type       Size  Available Used%
    --------- ------------ ------------ ---------- ---- ---------- ---------- -----
    vserver1  vol1         aggr1        online     RW          1TB    972.8GB    5%

A logical interface needs to be created so that the exported volume can be accessed by a host server. In this example, the logical interface is named infs_1 and reachable using the 10.5.74.109 ip address. NOTE: The 10.5.74.109 ip address is a valid address, registered with the DNS server.

    fas3270::> network interface create -vserver vserver1 -lif infs_1 -role data -data-protocol nfs,cifs,fcache -home-node fas3270-1 -home-port e0b -address 10.5.74.109 -netmask 255.255.255.0 -status-admin up

    Info: Your interface was created successfully; the routing group d10.5.74.0/24 was created


    fas3270::> net int show infs_1
      (network interface show)
                Logical    Status     Network            Current       Current Is
    Vserver     Interface  Admin/Oper Address/Mask       Node          Port    Home
    ----------- ---------- ---------- ------------------ ------------- ------- ----
    vserver1
                infs_1       up/up    10.5.74.109/24     fas3270-1     e0b     true

Mount the template volume that was just created on the host server where you will create a template Perforce client workspace.

    $ hostname
    plsbep2.pl.perforce.com
    $ id
    uid=42(perforce) gid=300(team) groups=300(team) context=unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023
    $ sudo mkdir /netapp2
    $ sudo mount 10.5.74.109:/vol1 /netapp2
    $ sudo mkdir /netapp2/perforce
    $ sudo chown perforce:team /netapp2/perforce

Create a Perforce client using the template vol1 mount in as the client Root:.


    Client: template-ws
    Update: 2015/01/09 10:48:32
    Access: 2015/01/09 10:45:09
    Owner:  perforce
    Host:   plsbep2.pl.perforce.com
    Description:
            Created by perforce.
    Root:   /netapp2/perforce
    Options:        noallwrite noclobber nocompress unlocked nomodtime normdir
    SubmitOptions:  submitunchanged
    LineEnd:        local
    View:
            //depot/main/p4/... //template-ws/depot/main/p4/...

Sync your source code using your template client and build your product so that all build-artifacts are created.

    $  p4 -p perforce:1666 -c template-ws sync
    //depot/main/p4/Jamfile#62 - added as /netapp2/perforce/depot/main/p4/Jamfile
    //depot/main/p4/Jamrules#859 - added as /netapp2/perforce/depot/main/p4/Jamrules
    //depot/main/p4/POLICY#5 - added as /netapp2/perforce/depot/main/p4/POLICY
    //depot/main/p4/Version#589 - added as /netapp2/perforce/depot/main/p4/Version
    ...

    jam -s OSVER=26 p4
    ...found 769 target(s)...
    ...updating 184 target(s)...
    MkDir1 ../p4-bin 
    MkDir1 ../p4-bin/bin.linux26x86_64 
    MkDir1 ../p4-bin/bin.linux26x86_64/objects 
    MkDir1 ../p4-bin/bin.linux26x86_64/objects/client 
    C++ ../p4-bin/bin.linux26x86_64/objects/client/clientmain.o 
    C++ ../p4-bin/bin.linux26x86_64/objects/client/client.o
    C++ ../p4-bin/bin.linux26x86_64/objects/client/clientapi.o 
    C++ ../p4-bin/bin.linux26x86_64/objects/client/clientenv.o 

Now that all the object artifacts are created from the build we need to create another Perforce client from a Flexcloned volume. Log back into the NetApp filer to create snapshot of the template volume. We'll call it vol1-snapshot.

    fas3270::> volume snapshot create -vserver vserver1 -volume vol1 -snapshot vol1-snapshot

    fas3270: vol snapshot show vol1 -snapshot vol1-snapshot
      (volume snapshot show)
                                                                       ---Blocks---
    Vserver  Volume  Snapshot                        State        Size Total% Used%
    -------- ------- ------------------------------- -------- -------- ------ -----
    vserver1 vol1
                     vol1-snapshot                   valid        80KB     0%    0%

Create a flexclone of the snapshot. We'll call it ws2clone. Once it's created, modify the permissions and mount it to an /ws2 export path.

    fas3270::> vol clone create -vserver vserver1 -flexclone ws2clone -parent-volume vol1 -junction-active true
      (volume clone create)
    [Job 9897] Job succeeded: Successful

    fas3270::> vol modify -vserver vserver1 -volume ws2clone -unix-permissions ---rwxrwxrwx
      (volume modify)

    Volume modify successful on volume: ws2clone

    fas3270::> vol mount -vserver vserver1 -volume ws2clone -junction-path /ws2
      (volume mount)

Now that you have a snapshotted the flexcloned volume, you can create another Perforce client using that volume. Once again, on your host server, mount the flexcloned volume and create a Perforce client using that volume as the Perforce client Root:

    # mkdir /ws2

Mount the ws2 clone

    # mount 10.5.74.109:/ws2 /ws2

Create another client using the cloned mount

    Client: ws2-ws
    Owner:  perforce
    Host:   plsbep2.pl.perforce.com
    Description:
            Created by perforce.
    Root:   /ws2/perforce/
    Options:        noallwrite noclobber nocompress unlocked nomodtime normdir
    SubmitOptions:  submitunchanged
    LineEnd:        local
    View:
            //depot/main/p4/... //ws2-ws/depot/main/p4/...

Now that you have a new client, you need to associate the cloned Perforce files to the client using the p4 flush command.

    $ p4 -p perforce:1666 -c ws2-ws flush

Run jam to make sure cloned build is still intact

    $ jam -s OSVER=26 p4
    ...found 769 target(s)...

Modify a single file to force partial rebuild

    # vi Version (and change a line)

Run jam again to do partial build

    $ jam -s OSVER=26 p4
    ...found 769 target(s)...
    ...updating 7 target(s)...
    C++ ../p4-bin/bin.linux26x86_64/objects/client/clientmain.o
    C++ ../p4-bin/bin.linux26x86_64/objects/client/client.o
    Archive ../p4-bin/bin.linux26x86_64/libclient.a
    Ranlib ../p4-bin/bin.linux26x86_64/libclient.a
    C++ ../p4-bin/bin.linux26x86_64/objects/msgs/msgdb.o
    C++ ../p4-bin/bin.linux26x86_64/objects/support/ident.o
    Archive ../p4-bin/bin.linux26x86_64/libsupp.a
    Ranlib ../p4-bin/bin.linux26x86_64/libsupp.a
    Link ../p4-bin/bin.linux26x86_64/p4
    Chmod1 ../p4-bin/bin.linux26x86_64/p4
    Strip1 ../p4-bin/bin.linux26x86_64/p4
    ...updated 7 target(s)...
