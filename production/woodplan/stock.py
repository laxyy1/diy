"""Reusable, deterministic purchasing layouts. Feasible layouts, not optimal nesting."""
from collections import defaultdict
from .common import metric

def lumber_layout(catalog, stock, families, blank_lengths=None):
    groups={r['id']:r for r in catalog};blank_lengths=blank_lengths or {}
    boards=[]
    for family,ids in families:
        pending=[]
        for id in ids:
            r=groups[id]
            for n in range(r['qty']):pending.append((id,blank_lengths.get(id,r['length'])))
        # First-fit, stable sorted longest first, with one kerf charged per blank.
        batch=[]
        for id,length in sorted(pending,key=lambda a:(-a[1],a[0])):
            if length+stock['kerf']+2*stock['end_trim']>stock['board_length']:
                raise ValueError('A stock blank exceeds board length: '+id)
            b=next((b for b in batch if b['cursor']+length+stock['kerf']<=stock['board_length']-stock['end_trim']),None)
            if b is None:
                b={'family':family,'id':f'{family}-{len(batch)+1}','length':stock['board_length'],
                   't':max(groups[k]['t'] for k in ids),'w':max(groups[k]['w'] for k in ids),
                   'cursor':stock['end_trim'],'cuts':[]};batch.append(b)
            b['cuts'].append({'group':id,'start':b['cursor'],'length':length});b['cursor']+=length+stock['kerf']
        for b in batch:
            b['waste_length']=b['length']-sum(a['length'] for a in b['cuts'])
            b['waste_definition']='Includes end trims, crosscut kerfs and offcut; excludes ripping/defects.'
        boards.extend(batch)
    return boards

def plywood_layout(catalog, stock):
    """Unrotated free-rectangle packing; grain remains in X. Multiple sheets supported."""
    rectangles=[]
    for r in catalog:
        if r['material']!='Cabinet plywood':continue
        for i in range(r['qty']):rectangles.append({'id':f'{r["id"]}-{i+1}','group':r['id'],'length':r['length'],'width':r['w']})
    rectangles.sort(key=lambda r:(-r['width'],-r['length'],r['id']))
    sheets=[];gap=max(stock['nest_gap'],stock['kerf']);trim=stock['end_trim']
    for r in rectangles:
        rw,rh=r['length']+gap,r['width']+gap
        if r['length']>stock['sheet_length']-2*trim or r['width']>stock['sheet_width']-2*trim:
            raise ValueError('Plywood piece exceeds the unrotated usable sheet: '+r['id'])
        options=[]
        for si,sheet in enumerate(sheets):
            for x,y,w,h in sheet['free']:
                if rw<=w and rh<=h:options.append((w*h-rw*rh,y,x,si))
        if not options:
            sheets.append({'id':f'PLY-{len(sheets)+1}','length':stock['sheet_length'],'width':stock['sheet_width'],
                'free':[(trim,trim,stock['sheet_length']-2*trim+gap,stock['sheet_width']-2*trim+gap)],'pieces':[]})
            options=[(0,trim,trim,len(sheets)-1)]
        _,y,x,si=min(options);sheet=sheets[si];r.update(x=x,y=y);sheet['pieces'].append(r)
        # MaxRects free-space split: rectangles may overlap; every placement splits
        # every intersecting free rectangle, so occupied regions cannot be reused.
        free=[]
        for fx,fy,fw,fh in sheet['free']:
            if fx+fw<=x or x+rw<=fx or fy+fh<=y or y+rh<=fy:free.append((fx,fy,fw,fh));continue
            if fx<x:free.append((fx,fy,x-fx,fh))
            if x+rw<fx+fw:free.append((x+rw,fy,fx+fw-x-rw,fh))
            if fy<y:free.append((fx,fy,fw,y-fy))
            if y+rh<fy+fh:free.append((fx,y+rh,fw,fy+fh-y-rh))
        free=sorted(set(free))
        sheet['free']=[a for i,a in enumerate(free) if not any(i!=j and a[0]>=b[0] and a[1]>=b[1] and a[0]+a[2]<=b[0]+b[2] and a[1]+a[3]<=b[1]+b[3] for j,b in enumerate(free))]
    for s in sheets:
        area=s['length']*s['width'];s['waste_area_mm2']=area-sum(p['length']*p['width'] for p in s['pieces']);s['waste_fraction']=s['waste_area_mm2']/area
    return sheets
