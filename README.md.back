## P4 FlexClone

### NetApp Flexclone Technology

NetApp FlexClone technology enables instant, space-efficient clones of production or test data to be created easily, minimizing storage requirements, because physical disk space for these clones is required only when data blocks are changed. With NetApp FlexClone, each engineer can have his or her own virtual copy of production or test data for use in test and development activities.


The foundation of NetApp FlexClone is a writable point-in-time image based on a NetApp Snapshot® of a volume. The cloned volume stores only the data that changes between the source and clone. The Snapshot copy can already exist or it can be created automatically as part of the cloning operation. Creating the FlexClone volume takes just a few moments because the copied metadata is very small compared to the actual data. The parent volume can change independently of the FlexClone volume. It can also be split from its parent to create a new standalone volume. Space is used very efficiently because new disk space is
only allocated when there are metadata updates and/or additions to either the parent or the clone volume. While this may sound like magic, this technology has been an integral part of Data ONTAP and deployed for numerous years in productions.

[Paper: NetApp 'Storage magic'](http://www.perforce.com/sites/default/files/pdf/storage-magic-netapp-paper.pdf)

[Slides: NetApp 'Storage magic'](http://www.perforce.com/sites/default/files/pdf/storage-magic-netapp-slides.pdf)


## Design

### Flexclone workflow
1. __Populate__: Automated builds sync Perforce code to a template client workspace and build.

2. __Clone__: NetApp will snapshot/clone the build workspace (Perforce files + build artefacts)

3. __Create__: Perforce user will request to create a workspace, NetApp will provide the content and a `p4 sync -k` to build the have list.

4. __Update__: Use new NetApp snapshot, `p4 reconcile` and incremental build.


### Use cases
1. User creates a FlexClone Template workspace
  *  Perforce Client naming convention (e.g. `flexclone_`)
  *  Populate Perforce have list (regular sync)
  *  NetApp snapshots Workspace content (versioned files and build assets)


  *  `[POST ACTION]` on `p4 client` if name is prefixed with `flexclone_`.
  *  [?] Should the FlexClone Template workspace be imutable?

2. User create a workspace from the FlexClone Template
  * FlexClone pre populates files.
  * Perforce runs a `sync -k ...@flexclone_template-name` to build have list.


  * `[POST ACTION]` on `p4 client -t` if template name is prefixed with `flexclone_`.

3. Delete a FlexClone Template workspace
  * Clean up Perforce template workspace
  * Clean up FlexClone Snapshot
  * [?] Clean up children?

4. Update a FlexClone Template workspace
  * ?

5. User deletes a FlexClone workspace
  * Run Perforce `client -d`
  * Remove the contents of the workspace
  * Destroy clone
