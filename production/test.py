#!/usr/bin/env python3
"""Run regressions/fault injection and optionally save a new structured report."""
import argparse,unittest,json,sys
from pathlib import Path

class RecordedResult(unittest.TextTestResult):
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.records=[]
    def addSuccess(self,test):super().addSuccess(test);self.records.append({'id':test.id(),'status':'passed'})
    def addFailure(self,test,err):super().addFailure(test,err);self.records.append({'id':test.id(),'status':'failed','error':self._exc_info_to_string(err,test)})
    def addError(self,test,err):super().addError(test,err);self.records.append({'id':test.id(),'status':'error','error':self._exc_info_to_string(err,test)})
    def addSkip(self,test,reason):super().addSkip(test,reason);self.records.append({'id':test.id(),'status':'skipped','reason':reason})

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=Path);args=parser.parse_args()
    if args.report and args.report.exists():raise FileExistsError('Choose a new report path; refusing overwrite.')
    suite=unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent/'tests'))
    result=unittest.TextTestRunner(verbosity=2,resultclass=RecordedResult).run(suite)
    report={'passed':result.wasSuccessful(),'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'tests':result.records}
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
    sys.exit(0 if result.wasSuccessful() else 1)
