"""Reusable CAD primitives, millimetres. Product joinery lives in adapters."""
import cadquery as cq

def box(x,y,z,dx,dy,dz):
    return cq.Solid.makeBox(dx,dy,dz,cq.Vector(x,y,z))

def cyl(x,y,z,dx,dy,dz,r,length):
    return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(dx,dy,dz))

def yz_prism(poly,x,t):
    wire=cq.Wire.makePolygon([cq.Vector(x,y,z) for y,z in poly],close=True)
    return cq.Solid.extrudeLinear(wire,[],cq.Vector(t,0,0))

