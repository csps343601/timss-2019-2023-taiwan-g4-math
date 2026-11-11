import sys,json,numpy as np
sys.path.insert(0,'.')
exec(open('main.py').read().split("R={}")[0])
S={}
for y in ('2019','2023'):
    m,acg,ash=prep(y); cc=m[m.ACDGEAS.notna()&m.sex.notna()&m.hrl.notna()].copy()
    for df in (cc,):
        df['very']=(df.ACDGEAS==1).astype(float); df['high']=(df.ACDGEAS==2).astype(float)
        df['female']=(df.sex==1).astype(float); df['hrl_many']=(df.hrl==1).astype(float); df['hrl_few']=(df.hrl==3).astype(float)
    out={}
    for dbl in (0,1):
        e,s,_=jrr(cc,'TOTWGT',reg_stat(['very','high','female','hrl_many','hrl_few']),dbl=dbl); out[dbl]=[(float(a),float(b)) for a,b in zip(e,s)]
    # 各層級組合：未加權 OLS 作為對照（僅供參考，無推論意義）
    X=np.column_stack([np.ones(len(cc)),cc[['very','high','female','hrl_many','hrl_few']].to_numpy()])
    b=np.mean([np.linalg.lstsq(X,cc[c].to_numpy(),rcond=None)[0] for c in pvcols('ASMMAT')],axis=0)
    out['unweighted_ols']=[float(x) for x in b]
    # 去掉家庭資源少（n 小）後
    c2=cc[cc.hrl!=3].copy()
    e,s,_=jrr(c2,'TOTWGT',reg_stat(['very','high','female','hrl_many'])); out['no_few']=[(float(a),float(b)) for a,b in zip(e,s)]
    # 學校數：各組有效學校（校長有效）
    S[y]=out
json.dump(S,open('results_sens.json','w'),indent=1)
for y in S: print(y,'dbl0 very',S[y][0][1],'dbl1 very',S[y][1][1],'unweighted',S[y]['unweighted_ols'][1:3],'no_few very',S[y]['no_few'][1])
