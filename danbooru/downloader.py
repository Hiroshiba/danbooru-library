#!/usr/bin/python3
# -*- coding: utf-8 -*-

#   Copyright 2012 codestation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import shutil
import hashlib
import logging
from time import sleep
from os.path import basename, isfile, join
from urllib.parse import urlsplit
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

class Downloader(object):
    
    _total = 0
    _abort = False

    def __init__(self, path):
        self.path = path
        
    def stopDownload(self):
        self._abort = True
        
    def _calculateMD5(self, name):
        try:
            file = open(name, 'rb')
            md5_hash = hashlib.md5()
            while True:
                d = file.read(128)
                if not d: break
                md5_hash.update(d)
            file.close()
            return md5_hash.hexdigest()
        except IOError:
            pass
                    
    def downloadQueue(self, dl_list, nohash=False):
        for dl in dl_list:
            if self._abort: break
            
            base = basename(urlsplit(dl['file_url'])[2])
            subdir = base[0]
            filename = join(self.path, subdir, base)
            if nohash and isfile(filename):
                logging.debug("(%i) %s already exists, skipping" % (self._total, filename))
                self._total += 1
                continue
            md5 = self._calculateMD5(filename)
            if md5:
                if md5 == dl['md5']:
                    logging.debug("(%i) %s already exists, skipping" % (self._total, filename))
                    self._total += 1
                    continue
                else:
                    logging.warning("%s md5sum doesn't match, re-downloading")
                        
            try:
                local_file = open(filename, 'wb')
            except IOError:
                logging.error('Error while creating %s' % filename)
                continue

            retries = 0
            while retries < 3:
                try:
                    remote_file = urlopen(dl['file_url'])
                    shutil.copyfileobj(remote_file, local_file)
                    remote_file.close()                
                    local_file.close()
                    self._total += 1
                    logging.debug('(%i) %s [OK]' % (self._total, dl['file_url']))
                    sleep(1)
                    break
                except URLError as e:
                    logging.error('>>> Error %s' % e.reason)
                except HTTPError as e:
                    logging.error('>>> Error %i: %s' % (e.code, e.msg))
                retries += 1
                logging.warning('Retrying (%i) in 2 seconds...' % retries)
                sleep(2)
