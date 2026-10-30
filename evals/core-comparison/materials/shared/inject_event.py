#!/usr/bin/env python3
"""Organizer-only frozen working-parameter event; no study executor reads it."""
import argparse, hashlib, json
from decimal import Decimal
from pathlib import Path

def strict(text):
 def pairs(items):
  out={}
  for key,value in items:
   if key in out:raise ValueError('Duplicate JSON key')
   out[key]=value
  return out
 def bad(value):raise ValueError('Nonfinite JSON number')
 return json.loads(text,object_pairs_hook=pairs,parse_int=Decimal,parse_float=Decimal,parse_constant=bad)

def equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 return a==b

def main():
 p=argparse.ArgumentParser();p.add_argument('--patch',required=True);p.add_argument('--project',required=True);p.add_argument('--receipt',required=True);a=p.parse_args()
 raw_patch=Path(a.patch).read_text();strict(raw_patch);e=json.loads(raw_patch);r=Path(a.project).resolve();target=r/e['target']
 assert target.is_relative_to(r) and target.is_file() and not any(x.is_symlink() for x in [target,*target.parents]),'Unsafe/missing project path'
 before=target.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
 assert equal(strict(before.decode()),strict(json.dumps(e['before_json']))),'Unexpected semantic parameters; do not silently repair'
 after=(json.dumps(e['after_json'],ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();assert sha(after)==e['after_sha256'];target.write_bytes(after)
 Path(a.receipt).write_text(json.dumps({'case_id':e['case_id'],'target':e['target'],'before_sha256':sha(before),'canonical_before_sha256':e['before_sha256'],'format_only_initial_difference':sha(before)!=e['before_sha256'],'after_sha256':sha(after),'only_intended_target_mutated_by_this_script':True,'immutable_primary_sources_changed':False},ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
