# HLS Parser
Parses HLS manifest and generates output in JSON format

## Features:
1. Supports the following HLS tags:
```
#EXTINF
#EXTM3U
#EXT-X-I-FRAME-STREAM-INF
#EXT-X-INDEPENDENT-SEGMENTS
#EXT-X-KEY
#EXT-X-MEDIA
#EXT-X-MEDIA-SEQUENCE
#EXT-X-PROGRAM-DATE-TIME
#EXT-X-SESSION-KEY
#EXT-X-STREAM-INF
#EXT-X-TARGETDURATION
#EXT-X-VERSION
... more to be added soon ...
```
2. Supports cookie-based tokenisation of URL
3. Supports redirection of URL

## Environment:
* Mac OS X 10.12.6 (Sierra)
* python 3.6

## Steps to configure and test:

1. Create and run inside python virtual environment
```
$ cd ~
$ mkdir parse_hls
$ cd parse_hls
$ python3.6 -m venv venv
$ source venv/bin/activate
$ pip install --upgrade pip 
$ pip install flask
```
2. Copy package from this repository

3. Run in local environment 
```
# note: all debug messages will appear in this window
$ python parse_hls.py
```
4. Use web browser to parse HLS in local machine

    http://localhost:5000/test 

    http://localhost:5000/m3u8?url=<url_of_hls_manifest>
