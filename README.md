# GridScripts

Welcome! These are a few scripts that we use at [SURFsara](https://www.surfsara.nl) to work with [the Grid](http://doc.grid.surfsara.nl/en/latest/).

## docker-ui

Building a container with a Grid User Interface.

## ey

Scripts to monitor GGUS tickets. 

## staging

stage.py is a script to stage a large list of files.
state.py can check the status (locality) of those files.

## voms

Check whether the LSC files still match the VO information.

## get-file-checksum

Get checksum of a file through WebDAV. Supports X509 and username/password auth, supports Adler32 and MD5.

## get-macaroon

Script to obtain a macaroon (bearer token) from a dCache WebDAV door.

## view-macaroon

Script to deserialise a macaroon (to see its properties).
