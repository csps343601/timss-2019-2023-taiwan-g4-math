import pickle,sys,json,numpy as np,pandas as pd
sys.path.insert(0,'/tmp/claude-0/analysis')
from timsslib import *
D=pickle.load(open('D.pkl','rb'))
LV={1:'非常高',2:'高',3:'中'}
HRL={1:'多',2:'一些',3:'少'}
OUT={}
def prep(y):
    asg=D[(y,'asg')].df.copy(); acg=D[(y,'acg')].df.copy(); ash=D[(y,'ash')].df.copy()
    acg['ACBGEAS']=acg.ACBGEAS.where(acg.ACBGEAS!=999999)
    acg['ACDGEAS']=acg.ACDGEAS.where(acg.ACDGEAS.isin([1,2,3]))
    m=asg.merge(acg[['IDCNTRY','IDSCHOOL','ACDGEAS','ACBGEAS']],on=['IDCNTRY','IDSCHOOL'],how='left',validate='m:1',indicator='_acg')
    m['sex']=m.ITSEX.where(m.ITSEX.isin([1,2]))
    m['hrl']=m.ASDGHRL.where(m.ASDGHRL.isin([1,2,3]))
    return m,acg,ash
def flow(y,m,acg,ash,asg_n):
    f={}
    f['students']=len(m); f['schools_asg']=int(m.IDSCHOOL.nunique()); f['schools_acg']=len(acg)
    f['acg_unique_school']=bool(acg.IDSCHOOL.is_unique)
    f['asg_matched_acg']=int((m._acg=='both').sum())
    f['ash_ids_equal']=bool(set(ash.IDSTUD)==set(m.IDSTUD)); f['ash_rows']=len(ash)
    f['school_valid']=int(acg.ACDGEAS.notna().sum()); f['school_invalid']=int(len(acg)-acg.ACDGEAS.notna().sum())
    f['school_groups']={LV[k]:int((acg.ACDGEAS==k).sum()) for k in (1,2,3)}
    f['student_school_valid']=int(m.ACDGEAS.notna().sum()); f['students_in_invalid_school']=int(m.ACDGEAS.isna().sum())
    f['sex_missing']=int(m.sex.isna().sum()); f['hrl_missing']=int(m.hrl.isna().sum())
    cc=m.ACDGEAS.notna()&m.sex.notna()&m.hrl.notna(); f['complete_cases']=int(cc.sum())
    f['cc_schools']=int(m[cc].IDSCHOOL.nunique())
    f['sum_totwgt']=float(m.TOTWGT.sum())
    return f
def groups_stat(gvar,levels,pv='ASMMAT',diffs=((0,2),(1,2),(0,1))):
    cols=pvcols(pv)
    def stat(d,w,p):
        y=d[cols[p]].to_numpy(); g=d[gvar].to_numpy()
        means=[wmean(y[g==l],w[g==l]) for l in levels]
        out=list(means)+[means[a]-means[b] for a,b in diffs]
        return np.array(out)
    return stat
def share_stat(gvar,levels):
    def stat(d,w,p):
        g=d[gvar].to_numpy(); return np.array([w[g==l].sum()/w.sum() for l in levels])
    return stat
def reg_stat(Xcols,pv='ASMMAT',const=True):
    cols=pvcols(pv)
    def stat(d,w,p):
        X=d[Xcols].to_numpy(float)
        if const: X=np.column_stack([np.ones(len(X)),X])
        return wls(X,d[cols[p]].to_numpy(float),w)
    return stat
def z(est,se): 
    t,p=tstat(est,se); return t,p
def pack(names,est,se,n=None):
    t,p=tstat(est,se)
    return [dict(term=nm,est=float(e),se=float(s),lo=float(e-1.96*s),hi=float(e+1.96*s),p=float(pp)) for nm,e,s,pp in zip(names,est,se,p)]
R={}
for y in ('2019','2023'):
    m,acg,ash=prep(y)
    f=flow(y,m,acg,ash,len(m)); R[y]={'flow':f}
    base=m[m.ACDGEAS.notna()].copy()   # 校長有效
    cc=m[m.ACDGEAS.notna()&m.sex.notna()&m.hrl.notna()].copy()
    for dd in (base,cc):
        dd['very']=(dd.ACDGEAS==1).astype(float); dd['high']=(dd.ACDGEAS==2).astype(float)
        dd['female']=(dd.sex==1).astype(float); dd['hrl_many']=(dd.hrl==1).astype(float); dd['hrl_few']=(dd.hrl==3).astype(float)
    # 1 學生層級分布（非 PV）
    est,se,_=jrr(base,'TOTWGT',share_stat('ACDGEAS',[1,2,3]),use_pv=False)
    R[y]['shares']=pack(['非常高','高','中'],est,se)
    # 全國
    est,se,_=jrr(base,'TOTWGT',groups_stat('ACDGEAS',[1,2,3]))
    names=['平均：非常高','平均：高','平均：中','差：非常高−中','差：高−中','差：非常高−高']
    R[y]['group_means_base']=pack(names,est,se); R[y]['n_base']=len(base)
    est,se,_=jrr(cc,'TOTWGT',groups_stat('ACDGEAS',[1,2,3]))
    R[y]['group_means_cc']=pack(names,est,se); R[y]['n_cc']=len(cc)
    # 模型
    est,se,_=jrr(cc,'TOTWGT',reg_stat(['very','high']))
    R[y]['M0']=pack(['截距(中)','非常高 vs 中','高 vs 中'],est,se)
    est,se,_=jrr(cc,'TOTWGT',reg_stat(['very','high','female','hrl_many','hrl_few']))
    R[y]['M1']=pack(['截距','非常高 vs 中','高 vs 中','女 vs 男','家庭資源多 vs 一些','家庭資源少 vs 一些'],est,se)
    # 連續量尺
    cs=cc[cc.ACBGEAS.notna()].copy()
    sd=float(np.sqrt(np.cov(cs.ACBGEAS,aweights=cs.TOTWGT)))
    cs['eas']=(cs.ACBGEAS-np.average(cs.ACBGEAS,weights=cs.TOTWGT))/sd
    est,se,_=jrr(cs,'TOTWGT',reg_stat(['eas']))
    R[y]['cont_M0']=pack(['截距','ACBGEAS（每 1 個學生加權標準差）'],est,se); R[y]['cont_sd']=sd; R[y]['cont_n']=len(cs)
    est,se,_=jrr(cs,'TOTWGT',reg_stat(['eas','female','hrl_many','hrl_few']))
    R[y]['cont_M1']=pack(['截距','ACBGEAS（每 1 SD）','女 vs 男','家庭資源多 vs 一些','家庭資源少 vs 一些'],est,se)
    # 學生數學 SD（加權）
    sds=[np.sqrt(np.cov(cc[c],aweights=cc.TOTWGT)) for c in pvcols('ASMMAT')]; R[y]['math_sd']=float(np.mean(sds))
    # 學校組成：各組的性別比、家庭資源（描述）
    comp={}
    for k in (1,2,3):
        s=cc[cc.ACDGEAS==k]
        comp[LV[k]]=dict(n=len(s),schools=int(s.IDSCHOOL.nunique()),female=float(np.average(s.female,weights=s.TOTWGT)),hrl_many=float(np.average(s.hrl_many,weights=s.TOTWGT)),hrl_few=float(np.average(s.hrl_few,weights=s.TOTWGT)))
    R[y]['composition']=comp
    # 性別、家庭資源各組平均 & 差距（全體 vs 校長組內）
    est,se,_=jrr(cc,'TOTWGT',groups_stat('hrl',[1,2,3]))
    R[y]['hrl_means']=pack(['平均：多','平均：一些','平均：少','差：多−少','差：一些−少','差：多−一些'],est,se)
    est,se,_=jrr(cc,'TOTWGT',groups_stat('sex',[1,2],diffs=((0,1),)))
    R[y]['sex_means']=pack(['平均：女','平均：男','差：女−男'],est,se)
    # 學校層級（SCHWGT）
    sc=acg.merge(D[(y,'acg')].df[['IDSCHOOL','SCHWGT']] if 'SCHWGT' not in acg.columns else acg[['IDSCHOOL']],on='IDSCHOOL') if False else acg
    # 學校加權比例（ACG 有 SCHWGT、JKCZONE、JKCREP）
    a=acg[acg.ACDGEAS.notna()].copy()
    R[y]['school_wgt_share']={LV[k]:float(a.loc[a.ACDGEAS==k,'SCHWGT'].sum()/a.SCHWGT.sum()) for k in (1,2,3)}
    # ---- 教師連結 ----
    ast=D[(y,'ast')].df.copy(); atg=D[(y,'atg')].df.copy()
    atg['ATDGEAS']=atg.ATDGEAS.where(atg.ATDGEAS.isin([1,2,3])); atg['ATBGEAS']=atg.ATBGEAS.where(atg.ATBGEAS!=999999)
    t=ast[ast.IDSUBJ.isin([1,3])&ast.MATWGT.notna()&(ast.MATWGT>0)].copy()
    tf={}
    tf['ast_rows']=len(ast); tf['math_rows']=len(t); tf['math_students']=int(t.IDSTUD.nunique())
    tf['atg_key_unique']=bool(atg.duplicated(['IDCNTRY','IDTEALIN']).sum()==0)
    t=t.merge(atg[['IDCNTRY','IDTEALIN','ATDGEAS','ATBGEAS']],on=['IDCNTRY','IDTEALIN'],how='left',validate='m:1',indicator='_atg')
    tf['linked_to_atg']=int((t._atg=='both').sum())
    tf['ast_students_dup_math']=int(t.IDSTUD.duplicated().sum())
    t=t.merge(m[['IDSTUD','ACDGEAS','sex','hrl']],on='IDSTUD',how='left',validate='m:1')
    tf['teacher_valid']=int(t.ATDGEAS.notna().sum()); tf['principal_valid']=int(t.ACDGEAS.notna().sum())
    tcc=t[t.ATDGEAS.notna()&t.ACDGEAS.notna()&t.sex.notna()&t.hrl.notna()].copy()
    tf['joint_rows']=len(tcc); tf['joint_students']=int(tcc.IDSTUD.nunique()); tf['joint_teachers']=int(tcc.IDTEACH.nunique()); tf['joint_schools']=int(tcc.IDSCHOOL.nunique())
    tcc['t_very']=(tcc.ATDGEAS==1).astype(float); tcc['t_high']=(tcc.ATDGEAS==2).astype(float)
    tcc['very']=(tcc.ACDGEAS==1).astype(float); tcc['high']=(tcc.ACDGEAS==2).astype(float)
    tcc['female']=(tcc.sex==1).astype(float); tcc['hrl_many']=(tcc.hrl==1).astype(float); tcc['hrl_few']=(tcc.hrl==3).astype(float)
    R[y]['teacher_flow']=tf
    # 一致性（MATWGT 加權）
    ct=pd.crosstab(tcc.ACDGEAS,tcc.ATDGEAS,values=tcc.MATWGT,aggfunc='sum',normalize='all').fillna(0)
    R[y]['cross']={'rows':'校長','cols':'教師','table':ct.round(4).to_dict()}
    est,se,_=jrr(tcc,'MATWGT',share_stat('ATDGEAS',[1,2,3]),use_pv=False); R[y]['t_shares']=pack(['非常高','高','中'],est,se)
    est,se,_=jrr(tcc,'MATWGT',groups_stat('ATDGEAS',[1,2,3])); R[y]['t_group_means']=pack(names,est,se)
    est,se,_=jrr(tcc,'MATWGT',groups_stat('ACDGEAS',[1,2,3])); R[y]['t_principal_means']=pack(names,est,se)
    est,se,_=jrr(tcc,'MATWGT',reg_stat(['t_very','t_high'])); R[y]['T0_teacher']=pack(['截距','教師：非常高 vs 中','教師：高 vs 中'],est,se)
    est,se,_=jrr(tcc,'MATWGT',reg_stat(['very','high'])); R[y]['T0_principal']=pack(['截距','校長：非常高 vs 中','校長：高 vs 中'],est,se)
    est,se,_=jrr(tcc,'MATWGT',reg_stat(['very','high','t_very','t_high'])); R[y]['T1_both']=pack(['截距','校長：非常高 vs 中','校長：高 vs 中','教師：非常高 vs 中','教師：高 vs 中'],est,se)
    est,se,_=jrr(tcc,'MATWGT',reg_stat(['very','high','t_very','t_high','female','hrl_many','hrl_few'])); R[y]['T2_both_adj']=pack(['截距','校長：非常高 vs 中','校長：高 vs 中','教師：非常高 vs 中','教師：高 vs 中','女 vs 男','家庭資源多 vs 一些','家庭資源少 vs 一些'],est,se)
    print(y,'done',flush=True)
json.dump(R,open('results_main.json','w'),ensure_ascii=False,indent=1)
