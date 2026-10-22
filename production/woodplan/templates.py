"""Reusable 1:1 SVG/DXF and tiled paper templates with overlap/calibration."""
import math,json
import ezdxf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,letter
from reportlab.lib.units import mm
from .common import dump,polygon_area

def export_pattern(pattern,out):
    doc=ezdxf.new('R2010');doc.units=4;msp=doc.modelspace()
    for name,color in [('PROFILE',7),('LAP',1)]:doc.layers.new(name,dxfattribs={'color':color})
    for name,poly in pattern['polygons'].items():msp.add_lwpolyline(poly,close=True,dxfattribs={'layer':name})
    msp.add_line((0,-20),(100,-20));msp.add_text('100 mm CALIBRATION',height=4).set_placement((0,-30))
    doc.saveas(out/'drawings/brace_1to1.dxf');dump(out/'drawings/brace_pattern.json',pattern)
    width=pattern['width']+20;height=pattern['height']+65
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="white"/>'
    for name,poly in pattern['polygons'].items():
        points=' '.join(f'{x+10:.8f},{pattern["height"]+10-y:.8f}' for x,y in poly);svg+=f'<polygon points="{points}" fill="none" stroke="{"#243d37" if name=="PROFILE" else "#a55230"}" stroke-width="0.25"/>'
    svg+=f'<path d="M10 {height-30}H110" stroke="black" stroke-width="0.25"/><text x="10" y="{height-15}" font-size="4" font-family="sans-serif">100 mm check bar / actual size / lap depth {pattern["lap_depth"]:g} mm</text></svg>'
    (out/'drawings/brace_1to1.svg').write_text(svg)
    for paper,pagesize in [('A4',A4),('Letter',letter)]:tile(pattern,out/f'template_{paper}.pdf',pagesize,paper)

def tile(pattern,path,pagesize,paper):
    W,H=pagesize;margin=18*mm;overlap=10.0;usablex=(W-2*margin)/mm
    # Pattern viewport stays below the header and above calibration annotations.
    # This also holds for taller patterns requiring more than one tile row.
    usabley=(H-margin-80-100*mm)/mm
    stepx=usablex-overlap;stepy=usabley-overlap
    nx=max(1,math.ceil((pattern['width']-overlap)/stepx));ny=max(1,math.ceil((pattern['height']-overlap)/stepy))
    c=canvas.Canvas(str(path),pagesize=pagesize,invariant=1);c.setTitle(f'DIYWOODPLANNER 1:1 brace template / {paper}')
    tiles=[]
    for row in range(ny):
        for col in range(nx):
            x0=col*stepx;y0=row*stepy;origin=[margin,100*mm]
            c.setFont('Helvetica-Bold',12);c.drawString(margin,H-margin,'DIYWOODPLANNER / 1:1 fabrication template')
            c.setFont('Helvetica',9);c.drawString(margin,H-margin-18,f'{paper} / tile {row+1}-{col+1} of {ny} by {nx} / print actual size, no fit-to-page')
            c.drawString(margin,H-margin-34,f'Origin: X {x0:.2f}, Y {y0:.2f} mm / overlap {overlap:g} mm / lap depth {pattern["lap_depth"]:g} mm')
            c.drawString(margin,H-margin-50,'Tape matching grid coordinates; verify both calibration bars with a ruler.')
            c.saveState();clip=c.beginPath();clip.rect(origin[0],origin[1],usablex*mm,usabley*mm);c.clipPath(clip,stroke=0)
            c.translate(origin[0]-x0*mm,origin[1]-y0*mm);c.scale(mm,mm)
            c.setLineWidth(.2)
            for name,poly in pattern['polygons'].items():
                c.setStrokeColorRGB(*((.14,.24,.21) if name=='PROFILE' else (.65,.32,.19)))
                p=c.beginPath();p.moveTo(*poly[0])
                for pt in poly[1:]:p.lineTo(*pt)
                p.close();c.drawPath(p,stroke=1,fill=0)
            c.setStrokeColorRGB(.7,.7,.7);c.setDash(1,2)
            for xx in range(0,math.ceil(pattern['width']/50)*50+1,50):c.line(xx,0,xx,pattern['height']+12)
            c.restoreState();c.setDash();c.setStrokeColorRGB(.2,.3,.25);c.rect(*origin,usablex*mm,usabley*mm,stroke=1,fill=0)
            # Registration ticks on both clipping boundaries; coordinates remain explicit.
            c.setFont('Helvetica',8);c.drawString(margin,90*mm,f'LEFT X={x0:.2f} mm       RIGHT X={x0+usablex:.2f} mm')
            c.line(margin,55*mm,margin+100*mm,55*mm);c.line(margin,53*mm,margin,57*mm);c.line(margin+100*mm,53*mm,margin+100*mm,57*mm)
            c.drawString(margin,48*mm,'100 mm horizontal calibration')
            c.line(W-margin-15*mm,25*mm,W-margin-15*mm,75*mm);c.drawString(margin,35*mm,'Vertical calibration at right: 50 mm')
            c.drawString(margin,24*mm,'Pattern only: use clamps/guards and a scrap test; this is not a router fixture.')
            c.showPage();tiles.append(dict(row=row,col=col,x0_mm=x0,y0_mm=y0,width_mm=usablex,height_mm=usabley))
    c.save();dump(path.with_suffix('.json'),dict(paper=paper,page_size_pt=list(pagesize),scale_pt_per_mm=mm,overlap_mm=overlap,tiles=tiles,
      calibration_horizontal_mm=100,calibration_vertical_mm=50,pattern_extent_mm=[pattern['width'],pattern['height']]))
