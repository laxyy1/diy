"""Reusable orthographic triangle depth-buffer renderer. No product rules."""
import numpy as np
from PIL import Image

def render(mesh,path,selection=None,offsets=None,view=(1.6,-2.6,1.5),width=1100,height=1450):
    cam=np.array(view,dtype=float);cam/=np.linalg.norm(cam)
    u=np.cross([0,0,1],cam);u/=np.linalg.norm(u);v=np.cross(cam,u)
    items=[]
    for m in mesh:
        if selection and not selection(m):continue
        vs=np.array(m['vertices'],float)
        vs+=np.array((offsets or {}).get(m['id'],[0,0,0]))
        items.append((m,vs))
    allvs=np.vstack([vs for m,vs in items]);coords=np.array([allvs@u,allvs@v]).T
    lo=coords.min(0);hi=coords.max(0);scale=min((width-80)/(hi[0]-lo[0]),(height-80)/(hi[1]-lo[1]))
    mid=(lo+hi)/2
    zbuf=np.full((height,width),-np.inf);rgb=np.ones((height,width,3))*np.array([250,247,241])
    normalbuf=np.zeros((height,width,3))
    light=np.array([-0.3,-0.7,1.]);light/=np.linalg.norm(light)
    for m,vs in items:
        proj=np.array([(vs@u-mid[0])*scale+width/2,height/2-(vs@v-mid[1])*scale,vs@cam]).T
        for tri in m['triangles']:
            wv=vs[list(tri)];normal=np.cross(wv[1]-wv[0],wv[2]-wv[0]);ln=np.linalg.norm(normal)
            if ln<1e-9:continue
            normal/=ln
            if normal@cam<=1e-8:continue
            q=proj[list(tri)];xmin=max(0,int(np.floor(q[:,0].min())));xmax=min(width-1,int(np.ceil(q[:,0].max())))
            ymin=max(0,int(np.floor(q[:,1].min())));ymax=min(height-1,int(np.ceil(q[:,1].max())))
            if xmax<xmin or ymax<ymin:continue
            xx,yy=np.meshgrid(np.arange(xmin,xmax+1)+.5,np.arange(ymin,ymax+1)+.5)
            a,b,c=q;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-9:continue
            l1=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            l2=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;l3=1-l1-l2
            zz=l1*a[2]+l2*b[2]+l3*c[2]
            zzview=zbuf[ymin:ymax+1,xmin:xmax+1]
            mask=(l1>=-1e-6)&(l2>=-1e-6)&(l3>=-1e-6)&(zz>zzview)
            shade=.72+.28*max(0,normal@light)
            color=np.array(m['color'])*255*shade
            zzview[mask]=zz[mask]
            rgb[ymin:ymax+1,xmin:xmax+1][mask]=color
            normalbuf[ymin:ymax+1,xmin:xmax+1][mask]=normal
    # Edge darkening comes from visible normals/depth, not hidden through-lines.
    finite=np.isfinite(zbuf);edge=np.zeros((height,width),bool)
    for axis in [0,1]:
        neigh=np.roll(normalbuf,1,axis);dif=np.linalg.norm(normalbuf-neigh,axis=2)
        edge|=(dif>.4)&finite
    rgb[edge]*=.66
    image=Image.fromarray(np.uint8(np.clip(rgb,0,255)))
    image.save(path)
    return {'u':u.tolist(),'v':v.tolist(),'mid':mid.tolist(),'scale':float(scale),'width':width,'height':height}

