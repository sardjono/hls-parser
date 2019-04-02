# parse_m3u8.py 
# =============
# supports valid_tags
# supports cookies if tokenisation is used for manifest, child playlists and chunks

import requests
import json
from urllib.parse import urlparse
import os
from flask import Flask, request, render_template, jsonify

test_url = "https://tglmp03.akamaized.net/out/v1/86bcd87d69f04c54a14819e5c141428c/master.m3u8"

valid_tags = [
    '#EXTINF',
    '#EXTM3U',
    '#EXT-X-I-FRAME-STREAM-INF',
    '#EXT-X-INDEPENDENT-SEGMENTS',
    '#EXT-X-KEY',
    '#EXT-X-MEDIA',
    '#EXT-X-MEDIA-SEQUENCE',
    '#EXT-X-PROGRAM-DATE-TIME',
    '#EXT-X-SESSION-KEY',
    '#EXT-X-STREAM-INF',
    '#EXT-X-TARGETDURATION',
    '#EXT-X-VERSION',
]

# create the Flask app
app = Flask(__name__)

def get_base_url(url_str=None):
    parsed = urlparse(url_str)
    dir = os.path.split(parsed.path)[0]
    filename = os.path.split(parsed.path)[1]
    baseurl = parsed.scheme + '://' + parsed.netloc + dir + '/'
    print('scheme  :', parsed.scheme)
    print('netloc  :', parsed.netloc)
    print('path    :', parsed.path)
    print('  dir   :', dir)
    print('  file  :', filename)
    print('params  :', parsed.params)
    print('query   :', parsed.query)
    print('fragment:', parsed.fragment)
    print('username:', parsed.username)
    print('password:', parsed.password)
    print('hostname:', parsed.hostname)
    print('port    :', parsed.port)
    print('base url:', baseurl)
    return baseurl

def parse_EXTINF(tag=None, a_line=None):
    '''
    The EXTINF tag specifies the duration of a Media Segment.  It applies
    only to the next Media Segment.  This tag is REQUIRED for each Media
    Segment.  Its format is:

    #EXTINF:<duration>,[<title>]
    <URI>

    where duration is a decimal-floating-point or decimal-integer number
    (as described in Section 4.2) that specifies the duration of the
    Media Segment in seconds.  Durations SHOULD be decimal-floating-
    point, with enough accuracy to avoid perceptible error when segment
    durations are accumulated.  However, if the compatibility version
    number is less than 3, durations MUST be integers.  Durations that
    are reported as integers SHOULD be rounded to the nearest integer.
    The remainder of the line following the comma is an optional human-
    readable informative title of the Media Segment expressed as UTF-8
    text.

    #EXTINF:6,
    '''
    tag_attrib = {}
    a_line = a_line[(len(tag)+1):] # trim tag header, including trailing ':'
    duration = a_line.split(',')[0]
    title = a_line.split(',')[1]
    tag_attrib['duration'] = duration
    tag_attrib['title'] = title
    return tag_attrib

def parse_attributes(tag=None, a_line=None, base=None):
    '''
    #EXT-X-STREAM-INF:<attribute-list>
    <URI>

    #EXT-X-MEDIA: <attribute-list>  Note: attribute may include URI

    Attributes:
    -----------
    BANDWIDTH
    AVERAGE-BANDWIDTH (opt)
    CODECS
    RESOLUTION (opt)
    FRAME-RATE (opt)
    HDCP-LEVEL (opt)
    AUDIO (opt)
    VIDEO (opt)
    SUBTITLES (opt)
    CLOSED-CAPTIONS (opt)

    Sample:
    -------
    #EXT-X-STREAM-INF:BANDWIDTH=1120763,RESOLUTION=640x360,CODECS="avc1.4D401E,mp4a.40.2"
    #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=693828,CODECS="avc1.4D4029,mp4a.40.5",RESOLUTION=320x180,FRAME-RATE=25.000,AUDIO="audio1" = ok
    #EXT-X-STREAM-INF:BANDWIDTH=1691000,AVERAGE-BANDWIDTH=1334000,CODECS="avc1.4D401F,mp4a.40.2",RESOLUTION=960x540,FRAME-RATE=25,AUDIO="AUDIOGROUP",SUBTITLES="textstream-stpp",CLOSED-CAPTIONS=NONE = ok
    #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=147033,CODECS="mp4a.40.2",AUDIO="aac"
    '''
    tag_attrib = {}
    a_line = a_line[(len(tag)+1):] # trim tag header, including trailing ':'
    while len(a_line) > 0:
        k = a_line.split('=')[0]
        print ("  k:%s" % k)
        a_line = a_line[(len(k)+1):]
        print ("    a:%s" % a_line)
        v = a_line.split(',')[0]
        print ("  v:%s" % v)
        a_line = a_line[(len(v)+1):]
        print ("    a:%s" % a_line)
        if '"' in v:
            len_before = len(v)
            v = v.replace('"', '')
            len_after = len(v)
            if len_after == (len_before - 1): # only 1 open quote (")
                v2 = a_line.split(',')[0]
                print ("  v2:%s" % v2)
                a_line = a_line[(len(v2)+1):]
                if len(v2) > 0:
                    v2 = v2.replace('"', '')
                    v = v + ',' + v2
                    print ("  v3:%s" % v)
                #end-if
                print ("    a:%s" % a_line)
            #end-if
        #end-if
        tag_attrib[k] = v
    if 'URI' in tag_attrib:
        uri = tag_attrib['URI']
        if '://' in uri:
            pass
        else:
            tag_attrib['URI']= base + uri
    return tag_attrib

def parse_m3u8(m3u8=None, base=None):
    m3u8_obj = {}  # dict
    media = []     # list of media
    stream = []    # list of streams
    chunk = []  # list of fragments
    continue_next_line = False
    media_obj = {}
    stream_obj = {}
    chunk_obj = {}
    for a_line in m3u8: # <------------------------------------- read each line
        __PRINT_VALUE__ = False
        if len(a_line.strip()) == 0: # <------------------------ check for empty line
            print ("[empty ] %s" % a_line)
        else:
            if a_line.startswith('#EXTM3U'):
                m3u8_obj['format'] = 'M3U'
                print ("[start ] %s" % a_line)
            elif a_line.startswith('#EXTINF'):
                continue_next_line = True ##### next line in m3u8 = part of current one
                print ("[inf   ] %s" % a_line)
                __PRINT_VALUE__ = True
                             ############
                tag_attrib = parse_EXTINF('#EXTINF', a_line)
                             ############
                print ("  [tag_attrib:%s]" % (json.dumps(tag_attrib)))  
            else:
                if a_line.startswith('#EXT-X-'): # <------------ check for m3u8 tag ...
                    tag_with_prefix = a_line.split(':')[0]
                    tag = tag_with_prefix[len('#EXT-X-'):]
                    val = a_line[(len('#EXT-X-')+len(tag)+1):] # declaration in m3u8 tag
                    if tag_with_prefix == '#EXT-X-MEDIA':
                        print ("[media ] %s" % a_line)
                        __PRINT_VALUE__ = True
                                     ################
                        tag_attrib = parse_attributes('#EXT-X-MEDIA', a_line, base)
                                     ################
                        print ("  [tag_attrib:%s]" % (json.dumps(tag_attrib)))
                        key = tag_attrib['TYPE'] + '-' + tag_attrib['NAME']
                        media_obj[key] = tag_attrib
                        media.append(media_obj)
                        media_obj = {}
                    elif tag_with_prefix == '#EXT-X-STREAM-INF':
                        continue_next_line = True ##### next line in m3u8 = part of current one
                        print ("[stream] %s" % a_line)
                        __PRINT_VALUE__ = True
                                     ################
                        tag_attrib = parse_attributes('#EXT-X-STREAM-INF', a_line, base)
                                     ################
                        print ("  [tag_attrib:%s]" % (json.dumps(tag_attrib)))                   
                    elif tag_with_prefix == '#EXT-X-I-FRAME-STREAM-INF':
                        print ("[iframe] %s" % a_line)
                        __PRINT_VALUE__ = True
                                     ################
                        tag_attrib = parse_attributes('#EXT-X-I-FRAME-STREAM-INF',a_line, base)
                                     ################
                        print ("  [tag_attrib:%s]" % (json.dumps(tag_attrib)))
                    elif tag_with_prefix == '#EXT-X-SESSION-KEY':
                        print ("[key   ] %s" % a_line)
                        __PRINT_VALUE__ = True
                                     ################
                        tag_attrib = parse_attributes('#EXT-X-SESSION-KEY',a_line, base)
                                     ################
                        print ("  [tag_attrib:%s]" % (json.dumps(tag_attrib)))
                    elif tag_with_prefix in valid_tags:
                        print ("[okay  ] %s" % a_line)
                        __PRINT_VALUE__ = True
                    else:
                        print ("[??????] %s" % a_line)      
                        m3u8_obj[tag] = val
                        __PRINT_VALUE__ = True
                elif a_line.startswith('#'): # ,---------------- check if line is comment
                    print ("[remark] %s" % a_line)      
                else: # <--------------------------------------- most likely URI of previous tag
                    if continue_next_line:
                        uri = base + a_line
                        print ("    [uri:%s]" % uri)
                        if 'BANDWIDTH' in tag_attrib:
                            tag_attrib['URI'] = uri
                            if 'RESOLUTION' in tag_attrib:
                                key = tag_attrib['RESOLUTION'] + '-' + tag_attrib['BANDWIDTH']
                            else:
                                key = tag_attrib['AUDIO'] + '-' + tag_attrib['BANDWIDTH']
                            #end-if
                            stream_obj[key] = tag_attrib
                            stream.append(stream_obj)
                            stream_obj = {}
                        else:
                            chunk.append(uri)
                            chunk_obj = {}
                    #end-if
                    continue_next_line = False ##### next line in m3u8 = not part of current one
                #end-if
            #end-if
            if __PRINT_VALUE__:
                print ("    [tag:%s]" % tag)
                print ("    [val:%s]" % val)
            #end-if
        #end-if
    #end-for
    m3u8_obj['MEDIA'] = media
    m3u8_obj['STREAM'] = stream
    m3u8_obj['CHUNK'] = chunk
    print ("===============================================================================================")
    print (json.dumps(m3u8_obj))
    print ("===============================================================================================")
    return (m3u8_obj)

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

@app.route('/test', methods=['GET', 'POST'])
def fetch_test_m3u8():
    url = request.args.get('url') #if url doesn't exist, returns None
    if url is None:
        url = test_url
    jar = requests.cookies.RequestsCookieJar()  # init cookie jar
    r = requests.get(url, cookies=jar)          # get cookies
    jar.update(r.cookies)                       # update cookies in jar
    if r.url != url:
        print ("redirect to: ", r.url)
    print ("text: ", r.text)
    print ("status_code: ", r.status_code)
    base = get_base_url(r.url)
    get_object = parse_m3u8(r.text.splitlines(), base)
    return json.dumps(get_object), 200

@app.route('/m3u8', methods=['GET', 'POST'])
def fetch_m3u8():
    url = request.args.get('url') #if url doesn't exist, returns None
    if url is None:
        return "please include .../m3u8?url=<url_of_m3u8>", 200
    jar = requests.cookies.RequestsCookieJar()  # init cookie jar
    r = requests.get(url, cookies=jar)          # get cookies
    jar.update(r.cookies)                       # update cookies in jar
    if r.url != url:
        print ("redirect to: ", r.url)
    print ("text: ", r.text)
    print ("status_code: ", r.status_code)
    base = get_base_url(r.url)
    get_object = parse_m3u8(r.text.splitlines(), base)
#    print ("------------------------------- now the child playlist ---------------------------------------")
#    r = requests.get((base + child_playlist), cookies=jar)  # use cookies in jar
#    jar.update(r.cookies)                                       # update cookies in jar
#    get_object = parse_m3u8(r.text.splitlines(), base)
    return json.dumps(get_object), 200

# We only need this for local development.
if __name__ == '__main__':
    app.run()
