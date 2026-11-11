import pickle,sys,json,numpy as np,pandas as pd
sys.path.insert(0,'/tmp/claude-0/analysis')
from timsslib import *
exec(open('main.py').read().split("R={}")[0])   # 重用 prep/stat 工具
SC=['ASMMAT','ASMNUM','ASMGEO','ASMDAT','ASMKNO','ASMAPP','ASMREA']
NM={'ASMMAT':'數學總分','ASMNUM':'數','ASMGEO':'測量與幾何','ASMDAT':'資料','ASMKNO':'知識（Knowing）','ASMAPP':'應用（Applying）','ASMREA':'推理（Reasoning）'}
O={}
for y in ('2019','2023'):
    m,acg,ash=prep(y)
    base=m[np.isfinite(m.TOTWGT)&(m.TOTWGT>0)].copy()
    cc=m[m.ACDGEAS.notna()&m.sex.notna()&m.hrl.notna()].copy()
    O[y]={}
    for sc in SC:
        cols=pvcols(sc)
        def st_all(d,w,p): return np.array([wmean(d[cols[p]].to_numpy(),w)])
        e,s,_=jrr(base,'TOTWGT',st_all); O[y][sc]={'all':(float(e[0]),float(s[0]))}
        for gv,lv,lab in (('sex',[1,2],'sex'),('hrl',[1,2,3],'hrl'),('ACDGEAS',[1,2,3],'principal')):
            diffs=((0,1),) if gv=='sex' else ((0,2),(1,2),(0,1))
            e,s,_=jrr(cc,'TOTWGT',groups_stat(gv,lv,pv=sc,diffs=diffs))
            O[y][sc][lab]=[(float(a),float(b)) for a,b in zip(e,s)]
    # 學生分布份額
    e,s,_=jrr(cc,'TOTWGT',share_stat('hrl',[1,2,3]),use_pv=False); O[y]['hrl_share']=[(float(a),float(b)) for a,b in zip(e,s)]
    e,s,_=jrr(cc,'TOTWGT',share_stat('sex',[1,2]),use_pv=False); O[y]['sex_share']=[(float(a),float(b)) for a,b in zip(e,s)]
    # 校長無效學校學生 vs 有效
    inv=base[base.ACDGEAS.isna()]; 
    O[y]['invalid_school_students']=int(len(inv))
    O[y]['invalid_school_mean_pv1']=float(np.average(inv.ASMMAT01,weights=inv.TOTWGT)) if len(inv) else None
json.dump(O,open('results_domains.json','w'),ensure_ascii=False,indent=1)
# 變化
def diff(a,b): 
    d=b[0]-a[0]; s=(a[1]**2+b[1]**2)**.5; from scipy import stats; return d,s,2*(1-stats.norm.cdf(abs(d/s)))
print('--- 總體變化 2019→2023')
for sc in SC:
    d,s,p=diff(O['2019'][sc]['all'],O['2023'][sc]['all']); print(NM[sc],[round(x,1) for x in O['2019'][sc]['all']],[round(x,1) for x in O['2023'][sc]['all']],'Δ',round(d,1),'se',round(s,1),'p',round(p,4))
print('--- hrl/sex shares',O['2019']['hrl_share'],O['2023']['hrl_share'],O['2019']['sex_share'],O['2023']['sex_share'])
print('--- 家庭資源差（多−少、多−一些、一些−少）變化 總分')
for i,nm in ((3,'多−少'),(4,'一些−少'),(5,'多−一些')):
    d,s,p=diff(O['2019']['ASMMAT']['hrl'][i],O['2023']['ASMMAT']['hrl'][i]); print(nm,[round(x,1) for x in O['2019']['ASMMAT']['hrl'][i]],[round(x,1) for x in O['2023']['ASMMAT']['hrl'][i]],round(d,1),round(s,1),round(p,3))
d,s,p=diff(O['2019']['ASMMAT']['sex'][2],O['2023']['ASMMAT']['sex'][2]); print('性別差 女−男',O['2019']['ASMMAT']['sex'][2],O['2023']['ASMMAT']['sex'][2],round(d,1),round(s,1),round(p,3))
for i,nm in ((3,'非常高−中'),(4,'高−中'),(5,'非常高−高')):
    d,s,p=diff(O['2019']['ASMMAT']['principal'][i],O['2023']['ASMMAT']['principal'][i]); print('校長',nm,round(d,1),round(s,1),round(p,3))
print('--- 各領域：校長 非常高−中 / 家庭資源 多−少 (2023) ; 性別')
for sc in SC:
    print(NM[sc],'校長非常高−中2023',[round(x,1) for x in O['2023'][sc]['principal'][3]],' 2019',[round(x,1) for x in O['2019'][sc]['principal'][3]],'| 性別2023',[round(x,1) for x in O['2023'][sc]['sex'][2]],'| 多−少2023',[round(x,1) for x in O['2023'][sc]['hrl'][3]])
print('invalid school',O['2019']['invalid_school_students'],O['2019']['invalid_school_mean_pv1'],O['2023']['invalid_school_students'],O['2023']['invalid_school_mean_pv1'])
