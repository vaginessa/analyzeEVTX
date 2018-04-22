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

from construct import *

from .binxml import *

'''
NTFSFILETIME
'''
NTFSFILETIME = Struct(
    'dwLowDateTime'         / Int32ul,
    'dwHighDateTime'        / Int32ul
)

'''
EVTX File Header: header of evtx file
    Signature: signature of evtx file (constant: 'ElfFile\x00')
    FirstChunkNumber: number of first chunk in file
    LastChunkNumber: number of last chunk in file
    NextRecordID: event log record ID of next record to be written
    HeaderSize: used size of evtx file header (constant: 128 bytes)
    MinorVersion: minor version of evtx format (constant: 1)
    MajorVersion: major version of evtx format (constant: 3)
    FirstChunkOffset: offset from beginning of file to first data chunk (constant: 4096 bytes)
    Flags: flags indicating whether the file is dirty and/or full
    Checksum: CRC32 checksum of first 120 bytes of the file header
'''
EVTXFileHeader = Struct(\
    'Signature'         / Const(b'ElfFile\x00'),
    'FirstChunkNumber'  / Int64ul,
    'LastChunkNumber'   / Int64ul,
    'NextEventRecordID' / Int64ul,
    'HeaderSize'        / Const(128, Int32ul),
    'MinorVersion'      / Int16ul,
    'MajorVersion'      / Int16ul,
    'FirstChunkOffset'  / Const(4096, Int16ul),
    'ChunkCount'        / Int16ul,
    Padding(76),
    'Flags'             / FlagsEnum(Int32ul,\
        DIRTY   = 0x0001,
        FULL    = 0x0002\
    ),
    'Checksum'          / Int32ul,
    Padding(3968)
)

'''
EVTX Chunk Header: evtx data chunk header
    Signature: signature of evtx header (constant: 'ElfChnk\x00')
    FirstEventRecordNumber: number of first event record in data chunk
    LastEventRecordNumber: number of last event record in data chunk
    FirstEventRecordID: ID of first event record in data chunk
    LastEventRecordID: ID of last event record in data chunk
    HeaderSize: size of chunk header (constant: 128 bytes)
    LastEventRecordOffset: offset from beginning of chunk header to data of last event record in chunk
    FreeSpaceOffset: offset to free space in the chunk
    EventRecordsChecksum: CRC32 checksum of event records data
    Checksum: CRC32 checksum of first 120 bytes of header and bytes 128 to 512 of the chunk
'''
EVTXChunkHeader = Struct(\
    'Signature'                 / Const(b'ElfChnk\x00'),
    'FirstEventRecordNumber'    / Int64ul,
    'LastEventRecordNumber'     / Int64ul,
    'FirstEventRecordID'        / Int64ul,
    'LastEventRecordID'         / Int64ul,
    'HeaderSize'                / Const(128, Int32ul),
    'LastEventRecordOffset'     / Int32ul,
    'FreeSpaceOffset'           / Int32ul,
    'EventRecordsChecksum'      / Int32ul,
    Padding(68),
    'Checksum'                  / Int32ul
)

EVTXRecordData = Struct(\
    'Signature'         / Const(b'\x2a\x2a\x00\x00'),
    'Size'              / Int32ul,
    'EventRecordID'     / Int64ul,
    'RawWriteTime'      / NTFSFILETIME
)
