## -*- coding: UTF-8 -*-
## evtx.py
##
## Copyright (c) 2018 Noah Rubin
## 
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
## 
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
## 
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.

import logging
Logger = logging.getLogger(__name__)
from os import path
from io import BytesIO
import inspect
from construct.lib import Container
import hashlib
from datetime import datetime
from dateutil.tz import tzlocal, tzutc

import src.structures.evtx as evtxstructs
from src.utils.time import WindowsTime

class EventLogXRecord(Container):
    '''
    Class for parsing Windows EVTX file records
    '''

    def __init__(self, raw_entry, load=False):
        super(EventLogXRecord, self).__init__()
        for attribute in [\
            'standard_information',
            'attribute_list',
            'file_name',
            'object_id',  
            'security_descriptor',
            'volume_name',
            'volume_information',
            'data',
            'index_root',
            'index_allocation',
            'bitmap',
            'logged_utility_stream'\
        ]:
            self[attribute] = list()
        self._raw_entry = raw_entry
        self._stream = None
        if load:
            self.parse()
    def _clean_transform(self, value, serialize=False):
        '''
        Args:
            value: Any  => value to be converted
        Returns:
            Any
            Raw value if it is not of type Container, else recursively removes
            any key beginning with 'Raw'
        Preconditions:
            N/A
        '''
        if issubclass(type(value), Container):
            cleaned_value = Container(value)
            if '_raw_entry' in cleaned_value:
                del cleaned_value['_filepath']
            if '_stream' in cleaned_value:
                del cleaned_value['_stream']
            for key in cleaned_value:
                if key.startswith('Raw') or key.startswith('_'):
                    del cleaned_value[key]
                else:
                    cleaned_value[key] = self._clean_transform(cleaned_value[key], serialize)
            return cleaned_value
        elif isinstance(value, list):
            return list(map(lambda entry: self._clean_transform(entry, serialize), value))
        elif isinstance(value, datetime) and serialize:
            return value.strftime('%Y-%m-%d %H:%M:%S.%f%z')
        elif isinstance(value, (bytes, bytearray)) and serialize:
            return value.decode('UTF8', errors='replace')
        else:
            return value
    def _prepare_kwargs(self, structure_parser, **kwargs):
        '''
        Args:
            structure_parser: Callable  => function to prepare kwargs for
            kwargs: Dict<String, Any>   => kwargs to prepare
        Returns:
            Dict<String, Any>
            Same set of keyword arguments but with values filled in
            for kwargs supplied as None with attribute values from self
            NOTE:
                This function uses the inspect module to get the keyword
                arguments for the given structure parser.  I know this is weird
                and non-standard OOP, and is subject to change int the future,
                but it works as a nice abstraction on the various structure parsers 
                for now.
        Preconditions:
            structure_parser is callable that takes 0 or more keyword arguments
            Only keyword arguments supplied to function
        '''
        argspec = inspect.getargspec(structure_parser)
        kwargs_keys = argspec.args[(len(argspec.args) - len(argspec.defaults))+1:]
        prepared_kwargs = dict()
        for key in kwargs_keys:
            if key in kwargs:
                if kwargs[key] is None:
                    prepared_kwargs[key] = getattr(\
                        self, 
                        key if key != 'stream' else '_stream', 
                        None\
                    )
                    if prepared_kwargs[key] is None:
                        raise Exception('Attribute %s was no provided and has not been parsed'%key)
                else:
                    prepared_kwargs[key] = kwargs[key]
            else:
                prepared_kwargs[key] = getattr(\
                    self, 
                    key if key != 'stream' else '_stream', 
                    None\
                )
        return prepared_kwargs
    def get_stream(self, persist=False):
        '''
        Args:
            persist: Boolean    => whether to persist stream as attribute on self
        Returns:
            TextIOWrapper|BytesIO
            Stream of prefetch file at self._filepath
        Preconditions:
            persist is of type Boolean  (assumed True)
        '''
        stream = BytesIO(self._raw_entry)
        if persist:
            self._stream = stream
        return stream
    def serialize(self):
        '''
        Args:
            N/A
        Returns:
            Container<String, Any>
            Serializable representation of self in Container object
        Preconditions:
            N/A
        '''
        return self._clean_transform(self, serialize=True)
    def parse_structure(self, structure, *args, stream=None, **kwargs):
        '''
        Args:
            structure: String               => structure to parse
            stream: TextIOWrapper|BytesIO   => stream to parse structure from
        Returns:
            Container
            Parsed structure if parsed successfully, None otherwise
        Preconditions:
            structure is of type String
            stream is of type TextIOWrapper|BytesIO (assumed True)
        '''
        if stream is None:
            stream = self._stream
        structure_parser = getattr(self, '_parse_' + structure, None)
        if structure_parser is None:
            Logger.error('Structure %s is not a known structure'%structure)
            return None
        try:
            prepared_kwargs = self._prepare_kwargs(structure_parser, **kwargs)
        except Exception as e:
            Logger.error('Failed to parse provided kwargs for structure %s (%s)'%(structure, str(e)))
            return None
        original_position = stream.tell()
        try:
            return structure_parser(original_position, *args, stream=stream, **prepared_kwargs)
        except Exception as e:
            Logger.error('Failed to parse %s structure (%s)'%(structure, str(e)))
            return None
    def parse(self):
        '''
        Args:
            N/A
        Procedure:
            Attempt to parse the supplied MFT entry, extracting
            header information and resident attribute data
        Preconditions:
            N/A
        '''
        self.get_stream(persist=True)
        try:
            return self
        finally:
            if self._stream is not None:
                self._stream.close()
                self._stream = None

class EventLogX(Container):
    '''
    Class for parsing Windows EVTX file
    '''
    def __init__(self, filepath):
        super(EventLogX, self).__init__()
        self._filepath = filepath
    def _hash_file(self, algorithm):
        '''
        Args:
            algorithm: String   => hash algorithm to use
        Returns:
            String
            Hex digest of hash of prefetch file
        Preconditions:
            algorithm is of type String
        '''
        try:
            hash = getattr(hashlib, algorithm)()
        except Exception as e:
            Logger.error('Unable to obtain %s hash of EVTX file (%s)'%(algorithm, str(e)))
            return None
        else:
            for record in self.records:
                hash.update(record)
            return hash.hexdigest()
    @property
    def records(self):
        '''
        @records.getter
        '''
        if self._filepath is None:
            return list()
        evtx_file = open(self._filepath, 'rb')
        try:
            #TODO: implement records
        finally:
            evtx_file.close()
            evtx_file = None
    @records.setter
    def records(self, value):
        '''
        @records.setter
        Preconditions:
            N/A
        '''
        raise AttributeError('records is a dynamic attribute and cannot be set')
    def get_metadata(self, simple_hash=True):
        '''
        Args:
            simple_hash: Boolean    => whether to only collect SHA256 hash or
                                       MD5 and SHA1 as well
        Returns:
            Container<String, Any>
            Container of metadata about this EVTX file:
                file_name: EVTX file name
                file_path: full path on local system
                file_size: size of file on local system
                md5hash: MD5 hash of EVTX file
                sha1hash: SHA1 hash of EVTX file
                sha2hash: SHA256 hash of EVTX file
                modify_time: last modification time of EVTX file on local system
                access_time: last access time of EVTX file on local system
                create_time: create time of EVTX file on local system
        Preconditions:
            simple_hash is of type Boolean
        '''
        assert isinstance(simple_hash, bool), 'Simple_hash is of type Boolean'
        return Container(\
            file_name=path.basename(self._filepath),
            file_path=path.abspath(self._filepath),
            file_size=path.getsize(self._filepath),
            md5hash=self._hash_file('md5') if not simple_hash else None,
            sha1hash=self._hash_file('sha1') if not simple_hash else None,
            sha2hash=self._hash_file('sha256'),
            modify_time=datetime.fromtimestamp(path.getmtime(self._filepath), tzlocal()).astimezone(tzutc()),
            access_time=datetime.fromtimestamp(path.getatime(self._filepath), tzlocal()).astimezone(tzutc()),
            create_time=datetime.fromtimestamp(path.getctime(self._filepath), tzlocal()).astimezone(tzutc())\
        )
    def parse(self):
        '''
        Args:
            N/A
        Returns:
            Gen<EventLogXRecord>
            Iterator over the {{FILETYPE} records in this EVTX file
        Preconditions:
            N/A
        '''
        for record in self.records:
            yield EventLogXRecord(record)
