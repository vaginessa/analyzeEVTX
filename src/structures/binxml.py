## -*- coding: UTF-8 -*-
## binxml.py
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

'''
BinXML Token Type: binary XML token types
'''
BinXMLToken = Enum(Int16ul,
    EOF                         = 0x00,
    OpenStartEmptyElementTag    = 0x01,
    CloseStartElementTag        = 0x02,
    CloseEmptyElementTag        = 0x03,
    EndElementTag               = 0x04,
    LastValue                   = 0x05,
    LastAttribute               = 0x06,
    LastCDATASection            = 0x07,
    LastCharRef                 = 0x08,
    LastEntityRef               = 0x09,
    PITarget                    = 0x0A,
    PIData                      = 0x0B,
    TemplateInstance            = 0x0C,
    NormalSubstitution          = 0x0D,
    OptionalSubstitution        = 0x0E,
    FragmentHeaderToken         = 0x0F,
    OpenStartElementTag         = 0x41,
    Value                       = 0x45,
    Attribute                   = 0x46,
    CDATASection                = 0x47,
    CharRef                     = 0x48,
    EntityRef                   = 0x49\
)

'''
BinXML Value Type: binary XML value types
'''
BinXMLValue = Enum(Int16ul,
    Null            = 0x00,
    String          = 0x01,
    AnsiString      = 0x02,
    Int8            = 0x03,
    UInt8           = 0x04,
    Int16           = 0x05,
    UInt16          = 0x06,
    Int32           = 0x07,
    UInt32          = 0x08,
    Int64           = 0x09,
    UInt64          = 0x0A,
    Real32          = 0x0B,
    Real64          = 0x0C,
    Bool            = 0x0D,
    Binary          = 0x0E,
    GUID            = 0x0F,
    SizeT           = 0x10,
    FileTime        = 0x11,
    SysTime         = 0x12,
    SID             = 0x13,
    HexInt32        = 0x14,
    HexInt64        = 0x15,
    EvtHandle       = 0x20,
    BinXMLType      = 0x21,
    EvtXML          = 0x23,
    StringArray     = 0x81,
    AnsiStringArray = 0x82,
    Int8Array       = 0x83,
    UInt8Array      = 0x84,            
    Int16Array      = 0x85,
    UInt16Array     = 0x86,
    Int32Array      = 0x87,
    UInt32Array     = 0x88,
    Int64Array      = 0x89,
    UInt64Array     = 0x8A,
    Real32Array     = 0x8B,
    Real64Array     = 0x8C,
    BoolArray       = 0x8D,
    GUIDArray       = 0x8F,
    SizeTArray      = 0x90,
    FileTimeArray   = 0x91,
    SysTimeArray    = 0x92,
    SIDArray        = 0x93,
    HexInt32Array   = 0x94,
    HexInt64Array   = 0x95\
)

BinXMLName = Struct(\
    Padding(4),
    'NameHash'          / Int16ul,
    'CharacterCount'    / Int16ul,
    'Name'              / PaddedString(this.CharacterCount, 'utf16')
)

BinXMLFragmentHeader = Struct(\
    'Token'         / BinXMLToken,
    'MajorVersion'  / Int8ul,
    'MinorVersion'  / Int8ul,
    'Flags'         / Int8ul
)
