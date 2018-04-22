## -*- coding: UTF8 -*-
## models.py
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

from datetime import datetime
import re
from sqlalchemy.orm import relationship
from sqlalchemy.types import String, Text, Integer, TIMESTAMP, BigInteger, Boolean, LargeBinary
from sqlalchemy import Column, ForeignKey, Index, text
from sqlalchemy.schema import UniqueConstraint, CheckConstraint, DDL
from sqlalchemy.ext.declarative import declarative_base, declared_attr

from src.utils.database import TimestampDefaultExpression, create_view 

class BaseTableTemplate(object):
    '''
    Base table class
    '''
    @declared_attr
    def __tablename__(cls):
        return str(cls.__name__.lower())

    @staticmethod
    def _convert_key(key):
        '''
        Args:
            key: String => key to convert
        Returns:
            String
            key converted from camel case to snake case
            NOTE:
                Implementation taken from:
                https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case#1176023
        Preconditions:
            key is of type String
        '''
        assert isinstance(key, str), 'Key is not of type String'
        return re.sub(\
            '([a-z0-9])([A-Z])', r'\1_\2', re.sub(\
                '(.)([A-Z][a-z]+)', r'\1_\2', key\
            )\
        ).lower()
    def populate_fields(self, data_dict, overwrite=True):
        '''
        Args:
            data_dict: Dict<String, Any>    => dict containing data to map to fields
            overwrite: Boolean              => whether to overwrite values of current instance
        Procedure:
            Populate attributes of this instance with values from data_dict
            where each key in data_dict maps a value to an attribute.
            For example, to populate id and created_at, data_dict would be:
            {
                'id': <Integer>,
                'created_at': <DateTime>
            }
        Preconditions:
            data_dict is of type Dict<String, Any>
        '''
        assert hasattr(data_dict, '__getitem__') and all((isinstance(key, str) for key in data_dict)), 'Data_dict is not of type Dict<String, Any>'
        for key in data_dict:
            converted_key = self._convert_key(key)
            if hasattr(self, converted_key) and (getattr(self, converted_key) is None or overwrite):
                setattr(self, converted_key, data_dict[key])
        return self

BaseTable = declarative_base(cls=BaseTableTemplate)

class ViewMixin(object):
    '''
    Mixin for (materialized) views
    '''
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

class ConcreteTableMixin(ViewMixin):
    '''
    Mixin class for (non-view) tables
    '''
    id          = Column(BigInteger().with_variant(Integer, 'sqlite'), primary_key=True)
    created_at  = Column(TIMESTAMP(timezone=True), server_default=TimestampDefaultExpression(), index=True)

class FileLedgerLinkedMixin(object):
    '''
    Mixin for tables linked to fileledger table
    fileledger table serves as accounting system for parser
    '''
    @declared_attr
    def meta_id(cls):
        return Column(BigInteger, ForeignKey('fileledger.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)

class FileLedger(BaseTable, ConcreteTableMixin):
    '''
    Parsed $MFT file ledger (tracking) table
    '''
    file_name               = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    file_path               = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    file_size               = Column(BigInteger, nullable=False)
    md5hash                 = Column(String().with_variant(Text, 'postgresql'))
    sha1hash                = Column(String().with_variant(Text, 'postgresql'))
    sha2hash                = Column(String().with_variant(Text, 'postgresql'), nullable=False)
    modify_time             = Column(TIMESTAMP(timezone=True))
    access_time             = Column(TIMESTAMP(timezone=True))
    create_time             = Column(TIMESTAMP(timezone=True))
    completed               = Column(Boolean, index=True)
    entry_headers           = relationship('EntryHeader', backref='file_ledger')
