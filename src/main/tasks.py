## -*- coding: UTF-8 -*-
## tasks.py
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
from hashlib import md5
from itertools import chain as itertools_chain
from datetime import datetime, timezone, timedelta
from json import dumps
from construct.lib import Container

import src.database.models as db
from src.parsers.evtx import EventLogXRecord

class BaseParseTask(object):
    '''
    Base class for parsing tasks
    '''

    def __init__(self, source):
        self._source = source
        self._resultset = None
    @property
    def source(self):
        '''
        @source.getter
        '''
        return self._source
    @source.setter
    def source(self, value):
        '''
        @source.setter
        Preconditions:
            N/A
        '''
        raise AttributeError('source attribute must be set in the constructor')
    @property
    def resultset(self):
        '''
        @resultset.getter
        '''
        return self._resultset
    @resultset.setter
    def resultset(self, value):
        '''
        @_resultset.setter
        Preconditions:
            value if of type List<Any>
        '''
        assert isinstance(value, list)
        self._resultset = value
    def extract_resultset(self, worker):
        '''
        Args:
            worker: BaseQueueWorker => worker that called this task
        Procedure:
            Convert source into result set
        Preconditions:
            worker is subclass of BaseQueueWorker
        '''
        raise NotImplementedError('extract_resultset method not implemented for %s'%type(self).__name__)
    def process_resultset(self, worker):
        '''
        Args:
            worker: BaseQueueWorker => worker that called this task
        Returns:
            List<Any>
            Process result set created in extract_resultset and return results of processing
        Preconditions:
            worker is subclass of BaseQueueWorker
        '''
        raise NotImplementedError('process_resultset method not implemented for %s'%type(self).__name__)
    def __call__(self, worker):
        '''
        Args:
            worker: BaseQueueWorker => worker that called this task
        Returns:
            Any
            Result of running this task
        Preconditions:
            worker is subclass of BaseQueueWorker
        '''
        self.extract_resultset(worker)
        return self.process_resultset(worker)

class BaseParseFileOutputTask(BaseParseTask):
    '''
    Base class for tasks that write output to file
    '''
    NULL = ''

    def __init__(self, source, nodeidx, recordidx, **context):
        super(BaseParseFileOutputTask, self).__init__(source)
        self._nodeidx = nodeidx
        self._recordidx = recordidx
        if 'target' not in context:
            raise KeyError('target was not provided as a keyword argument')
        self._context = Container(**context)
    @property
    def nodeidx(self):
        '''
        @nodeidx.getter
        '''
        return self._nodeidx
    @nodeidx.setter
    def nodeidx(self, value):
        '''
        @nodeidx.setter
        Preconditions:
            N/A
        '''
        raise AttributeError('nodeidx attribute must be set in the constructor')
    @property
    def recordidx(self):
        '''
        @recordidx.getter
        '''
        return self._recordidx
    @recordidx.setter
    def recordidx(self, value):
        '''
        @recordidx.setter
        Preconditions:
            N/A
        '''
        raise AttributeError('recordidx attribute must be set in the constructor')
    @property
    def context(self):
        '''
        @context.getter
        '''
        return self._context
    @context.setter
    def context(self, value):
        '''
        @context.setter
        Preconditions:
            value is of type Container
        '''
        if self._context is None:
            assert isinstance(value, Container)
            self._context = value
        else:
            raise AttributeError('context attribute has already been set')
    def process_resultset(self, worker):
        '''
        @BaseParseTask.process_resultset
        '''
        target_file = path.join(self.context.target, '%s_tmp_amft.out'%worker.name)
        try:
            if len(self.result_set) > 0:
                successful_results = 0
                with open(target_file, 'a') as f:
                    for result in self.result_set:
                        try:
                            if 'sep' in self.context:
                                f.write(self.context.sep.join(result) + '\n')
                            else:
                                f.write(result + '\n')
                            successful_results += 1
                        except Exception as e:
                            Logger.error('Failed to write result for EVTX record %d from node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))
        except Exception as e:
            Logger.error('Failed to write results for EVTX record %d from node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))
        else:
            Logger.info('Successfully wrote %d result(s) for EVTX record %d from node %d'%(successful_results, self.recordidx, self.nodeidx))
        finally:
            return [True]

class ParseCSVTask(BaseParseFileOutputTask):
    '''
    Class for parsing single EVTX record to CSV format
    '''
    def extract_resultset(self, worker):
        '''
        @BaseParseTask.extract_resultset
        '''
        self.result_set = list()
        if self.context.info_type == 'summary':
            try:
                evtx_record = EventLogXRecord(self.source)
                evtx_record.parse()
            except Exception as e:
                Logger.error('Failed to parse EVTX record %d for node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))
            else:
                try:
                    result = list()
                    self.result_set.append(result)
                except Exception as e:
                    Logger.error('Failed to create CSV output record of EVTX record %d for node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))

class ParseJSONTask(BaseParseFileOutputTask):
    '''
    Class for parsing single EVTX record to JSON format
    '''
    def extract_resultset(self, worker):
        '''
        @BaseParseTask.extract_resultset
        '''
        self.result_set = list()
        try:
            evtx_record = EventLogXRecord(self.source)
            result = dumps(evtx_record.parse().serialize(), sort_keys=True, indent=(2 if self.context.pretty else None))
        except Exception as e:
            Logger.error('Failed to parse EVTX record %d for node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))
        else:
            try:
                self.result_set.append(result)
            except Exception as e:
                Logger.error('Failed to create JSON output records of EVTX record %d for node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))

class ParseDBTaskStage1(BaseParseFileOutputTask):
    '''
    Task class to parse single EVTX record in preparation for insertion into DB
    '''

    def __init__(self, source, nodeidx, recordidx, fileledger):
        super(ParseDBTaskStage1, self).__init__(source, nodeidx, recordidx, target=None)
        self._context = None
        self._fileledger = fileledger
    @property
    def fileledger(self):
        '''
        @fileledger.getter
        '''
        return self._fileledger
    @fileledger.setter
    def fileledger(self, value):
        '''
        @fileledger.setter
        Preconditions:
            value is of type Container
        '''
        assert isinstance(value, Container)
        self._fileledger = fileledger
    def extract_resultset(self, worker):
        '''
        @BaseParseTask.extract_resultset
        '''
        self.result_set = list()
        try:
            evtx_record = EventLogXRecord(self.source)
            evtx_record.parse()
            evtx_record._stream = None
        except Exception as e:
            Logger.error('Failed to parse EVTX record %d from node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))
        else:
            try:
                self.result_set.append(ParseDBTaskStage2([evtx_record], self.nodeidx, self.recordidx, self.fileledger))
            except Exception as e:
                Logger.error('Failed to create DB output record for EVTX record %d from node %d (%s)'%(self.recordidx, self.nodeidx, str(e)))
    def process_resultset(self, worker):
        '''
        @BaseParseTask.process_resultset
        '''
        return self.result_set

class ParseDBTaskStage2(ParseDBTaskStage1):
    '''
    Class to push EVTX record information to database
    '''
    def extract_resultset(self, worker):
        '''
        @BaseParseTask.extract_resultset
        '''
        self.result_set = list()
        for evtx_record in self.source:
            #TODO: impelement extract_result method
            pass
    def process_resultset(self, worker):
        '''
        @BaseParseTask.process_resultset
        '''
        if worker.manager.session is None:
            try:
                worker.manager.create_session()
            except Exception as e:
                Logger.error('Failed to create database session (%s)'%str(e))
                return [False]
        successful_results = 0
        for result in self.result_set:
            try:
                worker.manager.add(result)
                worker.manager.commit()
                successful_results += 1
            except Exception as e:
                Logger.error('Failed to commit result to database (%s)'%str(e))
                worker.manager.rollback()
        if successful_results > 0:
            Logger.info('Successfully committed %d result(s) to database'%successful_results)
        return [True]
