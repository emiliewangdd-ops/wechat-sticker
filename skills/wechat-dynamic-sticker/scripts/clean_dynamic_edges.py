from PIL import Image
import cv2, numpy as np
from pathlib import Path

def clean_sheet(sheet_path, base_path, out_path, scale=350, y=155):
    s=Image.open(sheet_path).convert('RGBA'); base=Image.open(base_path).convert('RGBA').resize((512,512)); w,h=s.size; frames=[]
    for r,c in [(0,0),(0,1),(1,0),(1,1)]:
        cell=s.crop((c*w//2,r*h//2,(c+1)*w//2,(r+1)*h//2)).resize((512,512),Image.Resampling.LANCZOS)
        a=np.array(cell.getchannel('A')); rgb=np.array(cell)[:,:,:3]
        white=(rgb[:,:,0]>238)&(rgb[:,:,1]>238)&(rgb[:,:,2]>238)
        mask=(~white).astype(np.uint8)*255
        n,lab,stats,_=cv2.connectedComponentsWithStats(mask,8)
        keep=np.zeros_like(mask)
        for i in range(1,n):
            if stats[i,cv2.CC_STAT_AREA]>=30: keep[lab==i]=255
        keep=cv2.morphologyEx(keep,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
        keep=cv2.erode(keep,np.ones((2,2),np.uint8),iterations=1)
        cell.putalpha(Image.fromarray(keep))
        cell=cell.resize((scale,scale),Image.Resampling.LANCZOS)
        fr=base.copy(); fr.alpha_composite(cell,((512-scale)//2,y)); frames.append(fr)
    frames[0].save(out_path,save_all=True,append_images=frames[1:],duration=[180,400,450,250],loop=0,disposal=2,transparency=0)

if __name__=='__main__':
    import sys
    clean_sheet(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))
