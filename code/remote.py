''' Remote HTTP file mapping adapted from https://github.com/migurski/census-tools

Implements a file-like object that can read from a remote URL using ranges.
'''
from logging import getLogger
from os import SEEK_SET, SEEK_CUR, SEEK_END
from sys import stderr
from time import time
from os.path import basename
from io import BytesIO

import requests

class RemoteFileObject:
    """ Implement enough of this to be useful:
        http://docs.python.org/release/2.5.2/lib/bltin-file-objects.html
        
        Pull data from a remote URL with HTTP range headers.
    """

    def __init__(self, url, verbose=False, block_size=(16 * 1024)):
        self.verbose = verbose
        self.url = url

        self.offset = 0
        self.length = self._get_length()
        self.chunks = {}
        
        self.block_size = block_size
        self.start_time = time()

    def _get_length(self):
        """
        """
        resp = requests.head(self.url)
        length = int(resp.headers['Content-Length'])
        
        if self.verbose:
            getLogger(__name__).info('{} bytes in {}'.format(length, basename(self.url)))

        return length

    def _get_range(self, start, end):
        """
        """
        headers = {'Range': 'bytes={}-{}'.format(start, end)}
        resp = requests.get(self.url, headers=headers)

        return resp.content

    def read(self, count=None):
        """ Read /count/ bytes from the resource at the current offset.
        """
        if count is None:
            # to the end
            count = self.length - self.offset

        out = BytesIO()

        while count:
            chunk_offset = self.block_size * (self.offset // self.block_size)
            
            if chunk_offset not in self.chunks:
                range = chunk_offset, min(self.length, self.offset + self.block_size) - 1
                self.chunks[chunk_offset] = BytesIO(self._get_range(*range))
                
                if self.verbose:
                    loaded = float(self.block_size) * len(self.chunks) / self.length
                    getLogger(__name__).info('bytes {1} - {2} of {0}'.format(basename(self.url), *range))

            chunk = self.chunks[chunk_offset]
            in_chunk_offset = self.offset % self.block_size
            in_chunk_count = min(count, self.block_size - in_chunk_offset)
            
            chunk.seek(in_chunk_offset, SEEK_SET)
            out.write(chunk.read(in_chunk_count))
            
            count -= in_chunk_count
            self.offset += in_chunk_count

        out.seek(0)
        return out.read()

    def seek(self, offset, whence=SEEK_SET):
        """ Seek to the specified offset.
            /whence/ behaves as with other file-like objects:
                http://docs.python.org/lib/bltin-file-objects.html
        """
        if whence == SEEK_SET:
            self.offset = offset
        elif whence == SEEK_CUR:
            self.offset += offset
        elif whence == SEEK_END:
            self.offset = self.length + offset

    def tell(self):
        return self.offset
