"""Reusable artifact writers. Every output directory must be new."""
import cadquery as cq
from .common import dump,write_csv,bbox
from .stock import lumber_layout,plywood_layout

def export_design(design,out):
    for sub in ['cad/parts','drawings','qa']: (out/sub).mkdir(parents=True,exist_ok=True)
    assembly=cq.Assembly(name='DIYWOODPLANNER_development')
    records=[];mesh=[];lookup={r['id']:r for r in design.catalog}
    for p in design.parts:
        # Color is adapter data; the generic writer has a neutral fallback.
        color=design.drawings.get('colors',{}).get(p.group,(.74,.56,.36))
        assembly.add(p.shape,name=p.id,color=cq.Color(*color))
        cq.exporters.export(p.shape,str(out/f'cad/parts/{p.id}.step'))
        records.append(dict(id=p.id,group=p.group,meta=p.meta,bbox=bbox(p.shape),volume_mm3=p.shape.Volume(),
          stock_dimensions={k:lookup[p.group][k] for k in ['t','w','length']}))
        vs,ts=p.shape.tessellate(.4,.3)
        mesh.append(dict(id=p.id,group=p.group,meta=p.meta,color=color,vertices=[[v.x,v.y,v.z] for v in vs],triangles=ts))
    assembly.export(str(out/'cad/assembly.step'))
    comp=cq.Compound.makeCompound([p.shape for p in design.parts])
    for name,view in [('isometric',(1,-1,.7)),('front',(0,-1,0)),('side',(-1,0,0)),('rear',(0,1,0))]:
        cq.exporters.export(comp,str(out/f'drawings/{name}.svg'),opt={'projectionDir':view,'showHidden':False,'width':1000,'height':1500,'strokeWidth':.5})
    dump(out/'parameters.json',design.parameters);dump(out/'dimensions.json',design.dimensions)
    dump(out/'parts.json',records);dump(out/'cad/mesh.json',mesh);dump(out/'cut_list.json',design.catalog)
    write_csv(out/'cut_list.csv',design.catalog);write_csv(out/'hardware.csv',design.hardware)
    dump(out/'connections.json',design.connections);dump(out/'assembly_steps.json',design.steps)
    dump(out/'dowels.json',design.dowels);dump(out/'screws.json',design.screws)
    stock=design.parameters['stock'];plan=design.stock_plan
    layouts={'lumber':lumber_layout(design.catalog,stock,plan['families'],plan.get('blank_lengths')),'plywood':plywood_layout(design.catalog,stock)}
    dump(out/'cutting_layouts.json',layouts)
    buy=[]
    from collections import Counter
    for family,n in Counter(b['family'] for b in layouts['lumber']).items():
        b=next(b for b in layouts['lumber'] if b['family']==family);buy.append(dict(id=family,quantity=n,description=f"Hardwood {b['t']:g} x {b['w']:g} x {b['length']:g} mm; add defect allowance"))
    buy.append(dict(id='PLY',quantity=len(layouts['plywood']),description=plan['sheet_description']))
    buy.extend(plan.get('extra_purchases',[]))
    write_csv(out/'purchasing.csv',buy)
    return layouts
