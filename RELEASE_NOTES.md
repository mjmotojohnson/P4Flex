################################################################################
# P4 Flex Release Notes
################################################################################

v1.1.0 (2016-05-11)
First major release since P4 Flex was first uploaded to Perforce Swarm as a
reference example.  This version is a significant upgrade bringing it to
customer engagement ready status.

- Renamed many of the files to to preceed with p4flex. 
- Upgraded error handling.  No instead of throwing exceptions, the python code
  will perform pre-checks for things like the existence of a volume or
  snapshot before trying to create a duplicate.
- Added improve list volume, list snapshot and list clone reports.  The list
  clone option now reports the FlexClone efficiency numbers and the
  relationship between volume->snapshot-flexclone.
- Disabled volume and snapshot creation/deletion permission checks.  The code
  is nicely commented out and can be re-implemented.  It was found to hinder
  initial bring-up for new users.
- Added the ability to pass junction_path values on the volume and clone
  creation command lines.  This allows for improved customization.  Also fixed
  the default junction_path values.
- Code updated for readability with lots of new comments.  Improved comments
  in all files.
- Added run banner and better reporting of execution status.
- Removed chown operation in the p4flex script.  This has been replaced by a
  highly parallel chown scripts.  Added the following files;
      CeFileListGen.pl
      CeChownList.pl  
      fast_chown.c 
      Makefile
  The create clone process generates the line required for running the
  CeChownList.pl.  
- Added updated presentation PDF in the docs directory.


