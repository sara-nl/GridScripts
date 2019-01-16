## Remarks on gfal2 API

* There is a bug in gfal2: when all files in your surls list are online an empty string token is returned. 
In our `stage.py` implementation we check this and return a proper message, but we could also consider asking the developers fix this.

* When you rerun the `stage.py` script (orelse submit a stage request on the same files), a new pin is added to the files 
but gfal2 does NOT return a token. Thus, it is not possible to request for releasing the added pin because you miss the handler.
Maybe also useful request to the developers.  

* Opposite to the `bring_online_poll`, the gfal2 `release` implementation does not check whether the given token corresponds 
to the original surls list. Thus, we put in our implementation a poll check before requesting the release to check for consistensy
between token handlers and filelists.

* It would be nice to have an example in our wiki also for single file requests. Of course people can use the scripts 
with a single entry in their file list but we could also document the API commands. Anyone interested for this assignment?
It would be something like:

```sh
$ python
>>> import gfal2
>>> context = gfal2.creat_context()
>>> surl='srm://srm.grid.sara.nl/pnfs/grid.sara.nl/data/lofar/ops/projects/lc2_036/242458/L242458_SAP000_SB013_uv.MS_47416431.tar'
>>> context.getxattr(surl, 'user.status')
'NEARLINE '
>>> context.bring_online(surl, 600, 86400, True)   //If False, the prompt hangs until file gets online
(0, '69d301a1:-2034695100')
>>> context.bring_online_poll(surl, '69d301a1:-2034695100')  //Status 0 not staged
0
>>> context.bring_online_poll(surl, '69d301a1:-2034695100')  //Status 1 staged
1
>>> context.getxattr(surl, 'user.status')
'ONLINE_AND_NEARLINE'
>>> context.release(surl, '69d301a1:-2034695100')  //This should succeed, need to test
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
gfal2.GError: error on the release request : [SE][ReleaseFiles][SRM_ABORTED] SURL is not yet pinned, pinning aborted
```

Alternatively use the `gfal-legacy-bringonline --pin-lifetime` command.

* If you want to play with other Gfal2 features, you can check the list of the API object attributes on the UI as:

```sh
$ python
>>> import gfal2
>>> context = gfal2.creat_context()
>>> l = dir(context)
>>> l
['DirectoryType', 'Dirent', 'FileType', 'GfaltEvent', 'NullHandler', 'Stat', 'TransferParameters', '__class__', '__delattr__', '__dict__', '__doc__', '__format__', '__getattribute__', '__hash__', '__init__', '__instance_size__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', 'abort_bring_online', 'access', 'add_client_info', 'bring_online', 'bring_online_poll', 'cancel', 'checksum', 'chmod', 'clear_client_info', 'directory', 'event_side', 'file', 'filecopy', 'free', 'get_client_info', 'get_opt_boolean', 'get_opt_integer', 'get_opt_string', 'get_opt_string_list', 'get_plugin_names', 'get_user_agent', 'getxattr', 'gfalt_event', 'listdir', 'listxattr', 'load_opts_from_file', 'lstat', 'mkdir', 'mkdir_rec', 'open', 'opendir', 'readlink', 'release', 'remove_client_info', 'rename', 'rmdir', 'set_opt_boolean', 'set_opt_integer', 'set_opt_string', 'set_opt_string_list', 'set_user_agent', 'setxattr', 'stat', 'symlink', 'transfer_parameters', 'unlink']
```
