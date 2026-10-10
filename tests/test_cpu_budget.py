import concurrent.futures
from dataclasses import replace
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'eval_scheduler'))
from eval_scheduler.cpu_budget import CpuBudget, child_affinity


def pool(monkeypatch, cores=range(32), total=16, reserve=4):
    monkeypatch.setattr(os, 'sched_getaffinity', lambda pid: set(cores))
    return CpuBudget(total, reserve)


def test_defaults_and_noncontiguous_affinity(monkeypatch):
    monkeypatch.setattr(os, 'sched_getaffinity', lambda pid: set(range(10, 610, 2)))
    p=CpuBudget()
    assert p.total_cores==256 and p.reserve_cores==8 and p.capacity==248
    assert p.reserved_core_ids==tuple(range(10,26,2))
    assert p.acquire().core_ids==(26,28)
    info=p.snapshot()
    assert info['available_cores']==246
    assert not set(p.reserved_core_ids) & set(p.worker_core_ids)


def test_small_affinity_does_not_steal_gateway_reserve(monkeypatch):
    p=pool(monkeypatch,cores=[9,11,20],total=256,reserve=8)
    assert p.total_cores==3 and p.reserve_cores==3 and p.capacity==0
    with pytest.raises(ValueError):p.acquire()


@pytest.mark.parametrize('total,reserve',[(0,0),(-1,0),(True,0),(2,3),(2,-1),(2,False),(2.0,0)])
def test_invalid_budget(total,reserve):
    with pytest.raises(ValueError):CpuBudget(total,reserve)


@pytest.mark.parametrize('count',[0,-1,True,1.5,'2',13])
def test_invalid_request(monkeypatch,count):
    p=pool(monkeypatch)
    with pytest.raises(ValueError):p.acquire(count)


def test_admission_release_and_lease_integrity(monkeypatch):
    p=pool(monkeypatch);lease=p.acquire(12)
    assert p.acquire() is None
    other=CpuBudget(16,4)
    with pytest.raises(ValueError):other.release(lease)
    with pytest.raises(ValueError):p.release(replace(lease))
    p.release(lease)
    assert p.available_cores==12
    with pytest.raises(ValueError):p.release(lease)
    with pytest.raises(ValueError):p.prepare(['echo'],{},lease)


def test_concurrent_claims_nonoverlap(monkeypatch):
    p=pool(monkeypatch);barrier=threading.Barrier(24)
    def claim(_):
        barrier.wait()
        return p.acquire()
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as executor:
        leases=[l for l in executor.map(claim,range(24)) if l is not None]
    assert len(leases)==6
    cores=[c for lease in leases for c in lease.core_ids]
    assert len(cores)==len(set(cores))==12
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        list(executor.map(p.release,leases))
    assert p.available_cores==12 and not p.snapshot()['leases']


def test_prepare_copies_env_caps_threads_no_shell(monkeypatch):
    p=pool(monkeypatch);lease=p.acquire(3)
    monkeypatch.setattr(shutil,'which',lambda name:'/usr/bin/taskset')
    env={'OMP_NUM_THREADS':'999','OPENBLAS_NUM_THREADS':'999','KEEP':'yes',
         'GOMP_CPU_AFFINITY':'0-999','KMP_AFFINITY':'explicit','OMP_PLACES':'{0}',
         'OMP_PROC_BIND':'true'}
    args,new=p.prepare(['echo','; touch /not-executed'],env,lease)
    assert args[-1]=='; touch /not-executed' and args[1:3]==['--cpu-list','4,5,6']
    assert env['OMP_NUM_THREADS']=='999' and new['KEEP']=='yes'
    for key in ('OMP_NUM_THREADS','OMP_THREAD_LIMIT','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS',
                'NUMEXPR_NUM_THREADS','NUMEXPR_MAX_THREADS','RAYON_NUM_THREADS'):
        assert new[key]=='3'
    assert new['TOKENIZERS_PARALLELISM']=='false'
    assert new['OMP_PROC_BIND']=='false'
    assert not {'GOMP_CPU_AFFINITY','KMP_AFFINITY','OMP_PLACES'} & new.keys()
    assert env['GOMP_CPU_AFFINITY']=='0-999'
    monkeypatch.setattr(shutil,'which',lambda name:None)
    with pytest.raises(RuntimeError):p.prepare(['echo'],{},lease)
    assert p.available_cores==9


@pytest.mark.parametrize('argv',[[], 'echo hello', [''], ['echo','\0']])
def test_invalid_argv(monkeypatch,argv):
    p=pool(monkeypatch);lease=p.acquire()
    with pytest.raises(ValueError):p.prepare(argv,{},lease)


def test_empty_affinity_fails_closed(monkeypatch):
    monkeypatch.setattr(os,'sched_getaffinity',lambda pid:set())
    with pytest.raises(ValueError,match='No CPUs'):CpuBudget()


@pytest.mark.skipif(not hasattr(os,'sched_getaffinity') or not shutil.which('taskset'),reason='Linux taskset required')
def test_real_child_grandchild_inheritance_and_exit_guard():
    original=child_affinity()
    p=CpuBudget(total_cores=min(4,len(original)),reserve_cores=1 if len(original)>1 else 0)
    lease=p.acquire(min(2,p.capacity))
    grandchild="import os,json; print(json.dumps(sorted(os.sched_getaffinity(0))))"
    code=("import os,sys,json,subprocess; "
          "print(json.dumps({'affinity':sorted(os.sched_getaffinity(0)),"
          f"'grandchild':json.loads(subprocess.check_output([sys.executable,'-c',{grandchild!r}])),"
          "'threads':os.environ['OMP_NUM_THREADS']}),flush=True); sys.stdin.readline()")
    argv,env=p.prepare([sys.executable,'-c',code],None,lease)
    child=subprocess.Popen(argv,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    try:
        row=json.loads(child.stdout.readline())
        assert row['affinity']==row['grandchild']==list(lease.core_ids)
        assert child_affinity(child.pid)==lease.core_ids
        assert row['threads']==str(lease.cpu_cores)
        assert child_affinity()==original
        with pytest.raises(RuntimeError):p.release(lease,child=child)
        child.communicate('\n',timeout=10)
        assert child.returncode==0
        p.release(lease,child=child)
        assert p.available_cores==p.capacity
    finally:
        if child.poll() is None:
            child.kill();child.wait()
