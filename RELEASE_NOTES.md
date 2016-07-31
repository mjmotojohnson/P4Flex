################################################################################
# P4 Flex Release Notes
################################################################################
v1.2.0 (2016-07-30)
- Added back p4 client registration and p4 run_sync -k functionality removed
  in the MERGE demo version.
- Added logging to enable easier debug tracing.  Logging verbosity is easily 
  controlled by setting verbosity level at the bigging of the program.
- Perforce permission controls commented out. This can be enable as needed.  
- Disabled chown functionality.  Chown functionality from ONTAP 9 will be added
  in the next version.  For now the program writes information on how to 
  execute the chown functionality if needed.
- Added ONTAP and ONTAP API version information in banner.
- Added -test option to exit after testing the connection to the filer
- Added significant error checking.  The script now tests for the existence or 
  non-existence of volumes, snapshots and clones before making filer calls.  This 
  ensures the user gets a nice understandable message out instead of an exception 
  from the filer like was the case in initial version.  The output of initial 
  version was horrible since when an error occurred, Python tossed out trace-back 
  information which make user input error look like a coding problem.  The new 
  version is much more robust to bad user input.
- Additional comments to help make the code more readable and debug-able.


v1.1.0 (2016-05-11)
First major release since P4 Flex was first uploaded to Perforce Swarm as a
reference example.  This version is a significant upgrade bringing it to
customer engagement ready status.

- Renamed many of the files to to preceed with p4flex. 
- Upgraded error handling.  No instead of throwing exceptions, the python code
  will perform pre-checks for things like the existence of a volume or
  snapshot before trying to create a duplicate. Improved error messages to make
  error understanding and correction easier.
- Added additional checks to ensure all proper command line options are passed
  for the given function.  This helps identify user error before the filer calls 
  are executed. The error messages help the user correct there mistake.
- Updated the usage help messaging.
- Added improve list volume, list snapshot and list clone reports.  The list
  clone option now reports the FlexClone efficiency numbers and the
  relationship between volume->snapshot-flexclone.
  The list snapshot output filters out the hourly, daily and nightly snapshots 
  for improved readability.
- Added run banner and better reporting of execution status.
- Disabled volume and snapshot creation/deletion permission checks.  The code
  is nicely commented out and can be re-implemented.  It was found to hinder
  initial bring-up for new users.
- Properly handle new volume UNIX UID and GID values.  Instead of new volumes
  taking on root:root permissions, the new volume takes on the UID:GID of the 
  user creating the volume.
- Added command line option to specify UID and GID for the volume from the command line.
- Added the ability to pass junction_path values on the volume and clone
  creation command lines.  This allows for improved customization.  Also fixed
  the default junction_path values.
- Code updated for readability with lots of new comments.  Improved comments
  in all files.
- Added configuration option to specify where the flexclones are mounted.  There is also
  command line option to pass a junction_path to the volume and clone create option.
- Removed chown operation in the p4flex script.  This has been replaced by a
  highly parallel chown scripts.  Added the following files;
      CeFileListGen.pl
      CeChownList.pl  
      fast_chown.c 
      Makefile
  The create clone process generates the line required for running the
  CeChownList.pl.  
- Added delete snapshot capability. Ensure that all create options had corresponding 
  delete function.
- Improved code associated with looping thru *-get-itr api calls.  
- Added option to force "thin provisioning" of new flexclones.  By default a flexclone
  will inherit the thin/thick provision setting of the parent volume.  A thick provisioned
  flexclone provides no space efficiencies.
- Added QUICKSTART guide which includes additional details on ONTAP filer setup requirements.
- The default configuration values define and example SW development project with specific 
  project directory hierarchy.  The project hierarchy is documented in docs/project_example.txt
  which shows the mapping of UNIX directory, Volume/Clone/Qtree, and junction_path assumptions.
  This helps put the flow into a more realist context which better resembles real-world customer 
  environments.
- Added updated presentation PDF in the docs directory.

Degraded Functionality & next version requirements
- Perforce client registration/de-registration disabled. This needs to be re-enabled.
  This fuctionality will be added back with the option to skip this step.  If the clone
  will only be used for testing, there is no need to register the workspace. This is the 
  case with a Bisect flow for instance.
- Perforce p4 flush functionality disabled.  This needs to be re-enabled.
  This fuctionality will be added back with the option to skip this step.  If the clone
  will only be used for testing, there is no need to register the workspace. If the clone 
  will only be used for testing, there is no need to take the time to do a flush.
- Perforce permission controls commented out.  
- Disabled chown functionality.  This will be added back with an option to skip this 
  step.  If the owner of the master volume is the same as the existing user, there is 
  no need to take the time to chown. This is the case in a bisect flow for example.


