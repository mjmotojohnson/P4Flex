# FLEXCLONE SETUP #
##
##

##Setup for SSH Passwordless

On Filer (Suggested that this is done by admin):

1. Creates an access control role name vol_snapshot which only has access to the volume snapshot commands.

    `security login role create –role vol_snapshot –cmddirname “volume” –access all –query “”`

2. Create a user that has access only to the volume snapshot commands. 

    `security login create –username sadmin –application ssh –authmethod publickey –role vol_snapshot`
    

On Host as root or admin user:

3.  Generate an ssh key


    `ssh-keygen –t rsa`

 A public key file of form “id_rsa.pub” is placed in ~/.ssh directory. 

4. Cut and paste the public key generated in file and place as value on the filer.

    `cd .ssh`

    `cat id_rsa.pub`

    ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAsT18WDJho+recfdN77Qm7msj+LSgOZ7exSGMtM5N1//T5KJT1k4qXqY38j14Kn1pYAzeMaVGPd4uzC+q4wO8bKEZyoyfsLba4lzypNSf8sU4+MZ2xSiRd2KqRPb2up5Si64aJFnu+9Q98GhO2J5K/OzOQBoyCZW/ntZlZ0KNCz2o+L7osa2aEpgbupIz54qkO7Q2+es5RLg3FN+S6lmffq4whwu7WhVm6oAI6Rks7670ot1ydTOemdobICBtLXlJLwGicSaacWWh7C4v99GPDvx/r6atoY+BpEOQ7bM0s9eALcJ6njgGxpL71+iBBKb3beas5Za7ULgOJRxILjHJtQ== root@ibmx3755-svl03


5.  On Filer, Add the Key Information (if the you want to add other publickeys for different users then add new key with different "index" number.  It is highly suggested that only a **privilege user** be allowed to these commands:

 `security login publickey create -username sadmin -index 2 -publickey "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAsT18WDJho+recfdN77Qm7msj+LSgOZ7exSGMtM5N1//T5KJT1k4qXqY38j14Kn1pYAzeMaVGPd4uzC+q4wO8bKEZyoyfsLba4lzypNSf8sU4+MZ2xSiRd2KqRPb2up5Si64aJFnu+9Q98GhO2J5K/OzOQBoyCZW/ntZlZ0KNCz2o+L7osa2aEpgbupIz54qkO7Q2+es5RLg3FN+S6lmffq4whwu7WhVm6oAI6Rks7670ot1ydTOemdobICBtLXlJLwGicSaacWWh7C4v99GPDvx/r6atoY+BpEOQ7bM0s9eALcJ6njgGxpL71+iBBKb3beas5Za7ULgOJRxILjHJtQ== root@ibmx3755-svl03"`

##Create Base Template 

ASSUMPTIONS

* An aggregate, vserver and network interface has been created.

* The p4 server is running in order to do a p4 submit 

p4d -p 172.31.10.101:1666 -r /mnt/p4db -J `pwd`/journal -q -L `pwd`/logs -v server=3 -v track=1 -d

. 

1.  On filer, Create and mount volume on filer:
`vol create -volume ws_template -vserver perforce -aggregate p4 -size 30G -state online -type RW -policy default -unix-permissions ---rwxrwxrwx -junction-path /ws_template ` 
2. On host as root, Mount the volume using the network interface LIF:

    `mount –t nfs –o vers=3,local_lock=all,nocto  172.31.10.9:/ /mnt`
3. Extract the source in which template will be created. 

    `cd /mnt/ws_template`

    `tar xvf /mnt/releases/linux-4.0.4.tar.xz`

4. Define your p4 client  config:

    `export P4PORT=172.31.10.101:1666`

    `export P4CLIENT=testaj`

     `p4 set`

     `p4 client`

5. Add the source files to depots and submit

    `find . –type f –print | p4 –x –add`

    `p4 submit`

6. Build

    `make`

The above assume that the source files has not been checked in, however, if they are checked in then just do a "p4 sync", define "p4 client" and then make. 

##Create FlexClone Workspace For User

1. On Host as root, take snapshot and create FlexClone and then modify permissions and mount to correct junction path.  There are two ways to do this.  However, the uggested way would be to have admin create the stable snapshot and users would create workspace based on that stable snapshot of parent volume. Usually an admin would do these steps which includes:

    `ssh sadmin@172.17.39.164 vol snapshot create -vserver perforce -volume ws_template -snapshot stable`

    `ssh sadmin@172.17.39.164 "vol clone create -vserver perforce -flexclone t1 -parent-volume ws_template -junction-active true" -parent-snapshot stable -junction-path /t1`


    OR if you want to create a snapshot and clone based on current state of parent volume do the following (not really suggested since if parent may not be stable or in an unknown state when the user creates the clone):

    `ssh sadmin@172.17.39.164 "vol clone create -vserver perforce -flexclone t1 -parent-volume ws_template -junction-active true" -junction-path /t1`

    If there are permissions issues when doing a "chmod" or access of volume from user please modify permissions of volume as follows. This step can be skipped:

    `ssh sadmin@172.17.39.164 "vol modify -vserver perforce -volume t1 -unix-permissions ---rwxrwxrwx"`

    After all parent-volume has been cloned based on the snapshot created, mount the volume on Host (**NOTE**: the NFS Data LIF IP of filer should be provide and not the management IP for below)

    `sudo mount -t nfs -o vers=3 172.17.39.164:/t1 /t1`

     After mount you should be able to see the contents:

    `ls /t1/ws1`

    `cd /t1/ws1`

     Then a chown needs to be done on volume to be owned by user who will own workspace:

    `chown -R tester:tester linux-4.0.4`
    

2. As user tester: 

    `cd /t1/ws1`
 
3. Define your p4 client config:

    `export P4PORT=172.31.10.101:1666`

    `export P4CLIENT=testeraj`
    
	`p4 set`

    `p4 client`

4. Run "p4 flush" to make workspace think it has the file content already.


    `p4 flush`  or `sync -k`

5. User can now edit and modify workspace.

##Delete FlexClone Workspace

1. As user, delete client workspace

    `p4 client –d testeraj`

2. As root, delete flexclone volume workspace

     `ssh sadmin@172.17.39.164 " vol unmount -vserver perforce -volume t1"`

     `ssh sadmin@172.17.39.164 " vol offline -vserver perforce –volume t1"`

     `ssh sadmin@172.17.39.164 " vol delete -vserver perforce -volume t1"`
    