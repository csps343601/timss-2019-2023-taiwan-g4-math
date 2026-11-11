import pickle,sys,numpy as np,pandas as pd
sys.path.insert(0,'/tmp/claude-0/analysis')
from timsslib import *
D=pickle.load(open('D.pkl','rb'))
OFFICIAL={ # 官方公布值（2023：timss2023.org Exhibit 1.1.1/1.1.13/1.1.14；2019 總分：Exhibit 1.1.10 趨勢表）
 ('2023','ASMMAT'):(607,1.7),('2023','ASMNUM'):(602,1.6),('2023','ASMGEO'):(622,1.8),('2023','ASMDAT'):(601,2.0),
 ('2023','ASMKNO'):(619,1.7),('2023','ASMAPP'):(612,1.8),('2023','ASMREA'):(589,1.8),
 ('2019','ASMMAT'):(599,1.9)}
SCRIPT19={('2019','ASMNUM'):(599,1.7),('2019','ASMGEO'):(607,1.8),('2019','ASMDAT'):(590,2.4)} # 先前 R 腳本記錄的值（本次未能重新取得官方來源）
rows=[]
for (y,sc),(om,ose) in {**OFFICIAL,**SCRIPT19}.items():
    d=D[(y,'asg')].df
    cols=pvcols(sc)
    ok=np.isfinite(d.TOTWGT)&(d.TOTWGT>0)&d.JKZONE.notna()&d.JKREP.notna()&d[cols].notna().all(axis=1)
    dd=d[ok]
    stat=lambda dd,w,p: np.array([wmean(dd[cols[p]].to_numpy(),w)])
    est,se,info=jrr(dd,'TOTWGT',stat)
    src='官方網站' if (y,sc) in OFFICIAL else 'R 腳本記錄值（未重新核對來源）'
    rows.append(dict(year=y,scale=sc,n=len(dd),zones=info['nzones'],est=est[0],se=se[0],off_mean=om,off_se=ose,
        ok=(round(est[0])==om) and (round(se[0],1)==ose),source=src))
R=pd.DataFrame(rows); pd.set_option('display.width',200); print(R.round(3).to_string())
R.to_csv('gate_py.csv',index=False)
print('ALL PASS:',R.ok.all())
