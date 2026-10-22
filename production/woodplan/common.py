"""Reusable records, exact unit conversion, JSON/CSV and analytic geometry helpers."""
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter
import csv, json, math, hashlib

@dataclass
class Part:
    id: str
    group: str
    shape: object
    meta: dict = field(default_factory=dict)

@dataclass
class Design:
    parameters: dict
    dimensions: dict
    parts: list
    catalog: list
    connections: list
    hardware: list
    steps: list
    dowels: list
    screws: list
    drawings: dict
    stock_plan: dict = field(default_factory=dict)

def dump(path, obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def metric(value):return f'{float(value):.2f}'.rstrip('0').rstrip('.')
def inch(value):return float(value)/25.4
def measure(value):return f'{metric(value)} mm / {inch(value):.3f} in'
def size(row):return ' × '.join(metric(row[k]) for k in ['t','w','length'])+' mm'
def imperial_size(row):return ' × '.join(f'{inch(row[k]):.3f}' for k in ['t','w','length'])+' in'

def write_csv(path, rows):
    with Path(path).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def read_csv(path):
    with Path(path).open(newline='') as f:return list(csv.DictReader(f))

def bbox(shape):
    b=shape.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]

def polygon_area(poly):
    return abs(sum(x*yy-xx*y for (x,y),(xx,yy) in zip(poly,poly[1:]+poly[:1])))/2

def clip(subject, boundary):
    """Convex polygon intersection; CCW inputs. Deterministic no CAD dependency."""
    def cross(a,b):return a[0]*b[1]-a[1]*b[0]
    result=[list(p) for p in subject]
    for a,b in zip(boundary,boundary[1:]+boundary[:1]):
        output=[];edge=[b[0]-a[0],b[1]-a[1]]
        if not result:break
        for s,e in zip(result[-1:]+result[:-1],result):
            inside=lambda p:cross(edge,[p[0]-a[0],p[1]-a[1]])>=-1e-8
            if inside(s)!=inside(e):
                ray=[e[0]-s[0],e[1]-s[1]];t=cross([a[0]-s[0],a[1]-s[1]],edge)/cross(ray,edge)
                output.append([s[0]+t*ray[0],s[1]+t*ray[1]])
            if inside(e):output.append(e)
        result=output
    return result

def hardware_counts(connections):
    counts=Counter()
    for c in connections:counts.update(c['hardware'])
    return counts

def preserve_p1(repo):
    baseline=json.loads((Path(repo)/'production/docs/p1_preservation_manifest.json').read_text())
    return [p for p,v in baseline.items() if not (Path(repo)/p).is_file() or sha(Path(repo)/p)!=v['sha256']]
