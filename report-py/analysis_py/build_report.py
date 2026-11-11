import json,re,html,pickle,sys,openpyxl,numpy as np,pandas as pd
sys.path.insert(0,'/tmp/claude-0/analysis')
R=json.load(open('results_main.json')); O=json.load(open('results_domains.json')); S=json.load(open('results_sens.json'))
GG=json.load(open('results_gate_group.json')); GP=pd.read_csv('gate_py.csv')
D=pickle.load(open('D.pkl','rb'))
U="/mnt/user-data/uploads/timss2023"
CB={'2023':openpyxl.load_workbook(f"{U}/T23_Codebook_G4.xlsx",read_only=True,data_only=True),
    '2019':openpyxl.load_workbook(f"{U}/TIMSS2019/T19_G4_Codebooks/T19_G4_Codebook.xlsx",read_only=True,data_only=True)}
def f1(x): return f"{x:.1f}"
def f2(x): return f"{x:.2f}"
def pct(x,d=1): return f"{100*x:.{d}f}%"
def ci(r): return f"{f1(r['lo'])+0 if False else f1(r['lo']).replace('-0.0','0.0')} 至 {f1(r['hi']).replace('-0.0','0.0')}"
def pf(p): return "<0.001" if p<0.001 else f"{p:.3f}"
def g(y,key,i): return R[y][key][i]
LV=['非常高','高','中']
# ---------- 區塊 ----------
B=[]
def H(l,t,i=None): B.append(('h',l,t,i))
def P(t): B.append(('p',t))
def L(items): B.append(('l',items))
def T(head,rows,cap=None,cls=''): B.append(('t',head,rows,cap,cls))
def FIG(svg,cap,alt): B.append(('f',svg,cap,alt))
def N(t): B.append(('n',t))
# ---------- SVG ----------
C19,C23='c19','c23'
def forest(rows,xmin,xmax,w=720,rowh=30,left=170,title='',ref=None,fmt=f1,groups=None):
    h=rowh*len(rows)+46; pw=w-left-30
    X=lambda v:left+(v-xmin)/(xmax-xmin)*pw
    s=[f'<svg viewBox="0 0 {w} {h}" role="img" class="chart" xmlns="http://www.w3.org/2000/svg">']
    t0=int(np.ceil(xmin/10)*10)
    for tv in range(t0,int(xmax)+1,10 if (xmax-xmin)<=120 else 20):
        s.append(f'<line x1="{X(tv):.1f}" x2="{X(tv):.1f}" y1="8" y2="{h-28}" class="gl"/><text x="{X(tv):.1f}" y="{h-10}" class="ax" text-anchor="middle">{tv}</text>')
    if ref is not None: s.append(f'<line x1="{X(ref):.1f}" x2="{X(ref):.1f}" y1="8" y2="{h-28}" class="ref"/>')
    for i,(lab,est,lo,hi,col) in enumerate(rows):
        y=18+i*rowh
        s.append(f'<text x="{left-10}" y="{y+4}" class="lb" text-anchor="end">{html.escape(lab)}</text>')
        s.append(f'<line x1="{X(lo):.1f}" x2="{X(hi):.1f}" y1="{y}" y2="{y}" style="stroke:var(--{col})" stroke-width="2.5"/>')
        s.append(f'<line x1="{X(lo):.1f}" x2="{X(lo):.1f}" y1="{y-5}" y2="{y+5}" style="stroke:var(--{col})" stroke-width="2"/><line x1="{X(hi):.1f}" x2="{X(hi):.1f}" y1="{y-5}" y2="{y+5}" style="stroke:var(--{col})" stroke-width="2"/>')
        s.append(f'<circle cx="{X(est):.1f}" cy="{y}" r="5.5" style="fill:var(--{col})"/>')
        s.append(f'<text x="{X(hi)+8:.1f}" y="{y+4}" class="vl">{fmt(est)}</text>')
    s.append('</svg>'); return ''.join(s)
def dumbbell(rows,xmin,xmax,w=720,rowh=34,left=170):
    h=rowh*len(rows)+46; pw=w-left-60
    X=lambda v:left+(v-xmin)/(xmax-xmin)*pw
    s=[f'<svg viewBox="0 0 {w} {h}" role="img" class="chart" xmlns="http://www.w3.org/2000/svg">']
    for tv in range(int(np.ceil(xmin/10)*10),int(xmax)+1,10):
        s.append(f'<line x1="{X(tv):.1f}" x2="{X(tv):.1f}" y1="8" y2="{h-28}" class="gl"/><text x="{X(tv):.1f}" y="{h-10}" class="ax" text-anchor="middle">{tv}</text>')
    for i,(lab,a,b,sig) in enumerate(rows):
        y=18+i*rowh
        s.append(f'<text x="{left-10}" y="{y+4}" class="lb" text-anchor="end">{html.escape(lab)}</text>')
        s.append(f'<line x1="{X(a):.1f}" x2="{X(b):.1f}" y1="{y}" y2="{y}" style="stroke:var({"--ink" if sig else "--rule"})" stroke-width="{3 if sig else 2}" {"" if sig else "stroke-dasharray=\"4 3\""}/>')
        s.append(f'<circle cx="{X(a):.1f}" cy="{y}" r="6" style="fill:var(--c19)"/><circle cx="{X(b):.1f}" cy="{y}" r="6" style="fill:var(--c23)"/>')
        s.append(f'<text x="{max(X(a),X(b))+11:.1f}" y="{y+4}" class="vl">{b-a:+.1f}{"" if sig else "（不顯著）"}</text>')
    s.append('</svg>'); return ''.join(s)
def hero_svg():
    rows=[]
    for k,lab in enumerate(LV):
        for y,col in (('2019',C19),('2023',C23)):
            r=R[y]['group_means_base'][k]; rows.append((f"{lab}・{y}",r['est'],r['lo'],r['hi'],col))
    return forest(rows,555,650,w=760,rowh=36,left=150)
# ---------- 變項表（codebook 實際讀取）----------
def cbrow(y,sh,v):
    for i,r in enumerate(CB[y][sh].iter_rows(values_only=True),1):
        if r[0]==v: return i,r
    raise KeyError((y,sh,v))
KEYV=[('ACG','ACDGEAS','校長報告的學校重視學業成功（三類指標）'),('ACG','ACBGEAS','同上（連續量尺）'),('ACG','SCHWGT','學校權重'),
 ('ASG','ITSEX','學生性別（學生追蹤表）'),('ASG','ASDGHRL','家庭學習資源（三類）'),('ASG','ASMMAT01','數學成就可能值（01–05 共五個）'),
 ('ASG','TOTWGT','學生總權重'),('ASG','JKZONE','jackknife 區'),('ASG','JKREP','jackknife 重複碼'),('ASG','IDSCHOOL','學校識別碼'),('ASG','IDSTUD','學生識別碼'),
 ('ATG','ATDGEAS','教師報告的學校重視學業成功（三類）'),('ATG','IDTEALIN','教師—班級識別碼'),('AST','IDSUBJ','教師任教科目'),('AST','MATWGT','數學教師權重')]
def keyvar_rows():
    out=[]
    for fcode,v,desc in KEYV:
        cells=[f"`{v}`",f"{fcode}",desc]
        for y,suf in (('2019','M7'),('2023','M8')):
            i,r=cbrow(y,fcode+suf if False else (fcode+'M'+('7' if y=='2019' else '8')),v)
            vals=r[8] if r[8] else (r[3] or '')
            cells.append(f"第 {i} 列；{str(vals)[:70] if r[8] else str(r[3])}")
        out.append(cells)
    return out
# ---------- 檔案盤點 ----------
FILEDESC={'acg':('ACG','校長／學校問卷'),'asg':('ASG','學生問卷＋成就可能值'),'ash':('ASH','家長／家庭問卷'),'ast':('AST','學生—教師連結（含教師權重）'),'atg':('ATG','教師問卷')}
inv=[]
for k,(c,dsc) in FILEDESC.items():
    a=D[('2019',k)].df.shape; b=D[('2023',k)].df.shape
    inv.append([f"`{c}`",dsc,f"`{k}twnm7.sav`",f"{a[0]:,}",f"{a[1]}",f"`{k}twnm8.sav`",f"{b[0]:,}",f"{b[1]}"])
# ============ 內容 ============
y9,y3='2019','2023'
fl9,fl3=R[y9]['flow'],R[y3]['flow']; tf9,tf3=R[y9]['teacher_flow'],R[y3]['teacher_flow']
m23=R[y3]['M1'][1]; m19=R[y9]['M1'][1]; u23=R[y3]['group_means_base'][3]; u19=R[y9]['group_means_base'][3]
sd23=R[y3]['math_sd']; sd19=R[y9]['math_sd']
def dd(a,b):
    d=b['est']-a['est']; s=(a['se']**2+b['se']**2)**.5; from scipy import stats; return d,s,2*(1-stats.norm.cdf(abs(d/s)))
chg_gap=dd(u19,u23)
TITLE="TIMSS 2019 至 2023 臺灣國小四年級數學領域成就變化與學習支持優先方向"
SUB="校長報告的學校重視學業成功程度與學生數學成就的關聯"
SUMMARY=[
 f"臺灣四年級數學總分由 {f1(O[y9]['ASMMAT']['all'][0])}（SE {f1(O[y9]['ASMMAT']['all'][1])}）升至 {f1(O[y3]['ASMMAT']['all'][0])}（SE {f1(O[y3]['ASMMAT']['all'][1])}），增加 {f1(dd({'est':O[y9]['ASMMAT']['all'][0],'se':O[y9]['ASMMAT']['all'][1]},{'est':O[y3]['ASMMAT']['all'][0],'se':O[y3]['ASMMAT']['all'][1]})[0])} 分。增幅主要來自測量與幾何（+{f1(O[y3]['ASMGEO']['all'][0]-O[y9]['ASMGEO']['all'][0])}）、資料（+{f1(O[y3]['ASMDAT']['all'][0]-O[y9]['ASMDAT']['all'][0])}）、應用與推理；「數」（+{f1(O[y3]['ASMNUM']['all'][0]-O[y9]['ASMNUM']['all'][0])}）與「知識」（{O[y3]['ASMKNO']['all'][0]-O[y9]['ASMKNO']['all'][0]:+.1f}）的變化在統計上不顯著。",
 f"2023 年，校長評為「非常高」重視學業成功的學校（{fl3['school_groups']['非常高']} 校），學生數學平均 {f1(u23['est'] if False else R[y3]['group_means_base'][0]['est'])}；評為「中」的學校（{fl3['school_groups']['中']} 校）為 {f1(R[y3]['group_means_base'][2]['est'])}。未調整差距 {f1(u23['est'])} 分（95% CI {ci(u23)}）；控制性別與家庭學習資源後為 {f1(m23['est'])} 分（95% CI {ci(m23)}），約 {m23['est']/sd23:.2f} 個學生標準差。2019 年方向相同：未調整 {f1(u19['est'])} 分，調整後 {f1(m19['est'])} 分（95% CI {ci(m19)}）。",
 f"2023 的差距比 2019 大，但「差距的變化」本身不顯著（{chg_gap[0]:+.1f} 分，SE {f1(chg_gap[1])}，p = {pf(chg_gap[2])}），不能說這個關聯增強了。",
 f"教師報告的重視程度沒有同樣的梯度：2023 年「非常高」教師組 {f1(R[y3]['t_group_means'][0]['est'])} 分，低於「高」組 {f1(R[y3]['t_group_means'][1]['est'])} 分。把兩者放進同一個模型，校長報告的關聯仍在（非常高 vs 中 {f1(R[y3]['T2_both_adj'][1]['est'])} 分）。",
 "這些都是相關，不是因果。校長的評分是主觀報告，也可能反映學校原本的學生組成；資料是橫斷面，無法判斷方向。"]
H(1,TITLE,'top')
P(f"**{SUB}**")
for s_ in SUMMARY: B.append(('sum',s_))
FIG(hero_svg(),"圖 1　各組數學平均與 95% 信賴區間（橘：2019；藍：2023）。信賴區間 ＝ 估計值 ± 1.96 × SE。","橫軸為數學平均分數，列出三個重視程度組在 2019 與 2023 的平均與信賴區間；非常高組高於中組，兩年皆然。")
# --- 1
H(2,"1. 研究問題與定位",'q')
P("本研究使用 TIMSS 2019 與 2023 臺灣四年級次級資料，回答兩組問題：")
L(["**描述性問題**：2019 至 2023 年，臺灣四年級數學的內容領域（數、測量與幾何、資料）與認知領域（知識、應用、推理）成就如何變化？",
   "**關聯性問題（主分析）**：校長報告的學校重視學業成功程度，與學生數學成就是否有關？此關聯在控制學生性別、家庭學習資源，並納入教師報告後是否仍在？兩個調查年的關聯是否不同？",
   "**應用問題**：依上述證據，哪些學生群體或學習面向值得優先關注？"])
P("TIMSS 2019 與 2023 是兩批不同的學生（重複橫斷面），沒有逐人追蹤。本報告只估計族群層級的關聯，不估計任何介入或疫情的因果效果。")
# --- 2
H(2,"2. 實際載入的資料：檔名、檔案種類與欄位",'data')
P("我沒有憑記憶描述檔案，而是用自寫的 .sav 讀取器（`savreader.py`，純 Python）載入十個臺灣檔案，並把每個檔案的欄位名稱與順序和 codebook 逐一比對。結果十個檔案都完全一致（集合相同、順序相同）。")
H(3,"2.1 檔名怎麼讀")
P("TIMSS 2023 四年級檔名由「資料種類（3 碼）＋國家（3 碼 ISO）＋M8」組成，例如 `asgtwnm8.sav` ＝ ASG（學生問卷）＋TWN（臺灣）＋M8（2023 主調查）。檔案種類定義見 2023 使用手冊 Exhibit 2.4（PDF 第 58 頁）；檔名規則見同手冊 PDF 第 57 頁。2019 檔名為 `…twnm7.sav`，格式相同、尾碼為 M7；2019 使用手冊本體不在資料夾內（資料夾內查無），所以 M7 的意義是依 codebook 檔名（`ACGM7`、`ASGM7` 等工作表）判讀，不是出自 2019 手冊。")
P("資料夾內另有 `…twnb7.sav`（2019，codebook 檔名為 `T19Br_G4_Codebook.xlsx`）與 `eT19PSI_G4_Codebook.xlsx`；本研究的全國估計只用 M7 主檔（見第 4 節，估計值已和官方公布值吻合）。")
T(["代碼","資料檔是什麼","2019 檔名","2019 列數","欄數","2023 檔名","2023 列數","欄數"],inv,"表 1　本研究實際載入的臺灣主檔（列數與欄數為載入後實測）")
P("各檔的「一列」代表什麼，會影響能不能直接算人數：ACG 一列一所學校；ASG、ASH 一列一位學生；ATG 一列一個「教師—班級」組合；AST 一列一個「學生—教師」連結，所以一位學生可有多列（2023 年 AST 共 "+f"{tf3['ast_rows']:,}"+" 列，其中數學教師連結 "+f"{tf3['math_rows']:,}"+" 列、涵蓋 "+f"{tf3['math_students']:,}"+" 位學生）。")
H(3,"2.2 欄位叫什麼名字")
P("context 變項名稱由 7–8 個字元組成：第 1 碼 A＝四年級；第 2 碼 C／T／S＝校長／教師／學生與家長；第 3 碼 B＝問卷原題、D＝衍生變項；第 4 碼表示主題；其後為題號（2023 使用手冊 PDF 第 71 頁）。例如 `ACDGEAS` 讀作：A（四年級）、C（校長）、D（衍生）、G（一般）、EAS（重視學業成功）。")
P("資料夾內查無 2019 版本手冊，所以 2019 與 2023 的同名變項是否等值，我只能用 codebook 標籤核對。有一個需要小心的例子：2023 年的 `ACBG14A`–`J` 是「學校問題嚴重程度」，但 2019 年的 `ACBG14A`–`K` 是標籤為「SCH CHARACTER」（TCH UNDERSTANDING 至 STD RESPECT，共 11 題）的題組；2023 年同標籤的 11 題在 `ACBG12A`–`K`。**不能只用變項名稱跨年比對。**")
T(["變項","檔案","意義","2019 codebook","2023 codebook"],keyvar_rows(),"表 2　主要變項與編碼（出自兩輪 codebook 實際列號）")
H(3,"2.3 遺漏值代碼")
P("使用手冊（PDF 第 74 頁）定義三類遺漏：Not Administered（SPSS 為系統遺漏）、Omitted or Invalid（9、99、999…）、Not Applicable（6、96、996…）。本研究使用的變項中，`ACDGEAS`、`ASDGHRL`、`ITSEX` 的無效值為 9，`ACBGEAS` 為 999999，分析前全部轉成缺漏。codebook 的遺漏值欄把 Not Applicable 寫成「6: Logically not applicable」。")
# --- 3
H(2,"3. 變項選擇與跨檔案連結",'link')
T(["角色","變項","來源檔","說明"],[
 ["結果","`ASMMAT01`–`05`","ASG／AST","數學整體成就的五個可能值；領域為 `ASMNUM/GEO/DAT`（內容）、`ASMKNO/APP/REA`（認知）"],
 ["主要解釋","`ACDGEAS`","ACG","校長報告：1 非常高、2 高、3 中（9 無效）。以「中」為參照組"],
 ["主要解釋（連續）","`ACBGEAS`","ACG","同一概念的連續量尺（用於敏感度分析，標準化為每 1 個學生加權 SD）"],
 ["調整","`ITSEX`、`ASDGHRL`","ASG","性別（1 女、2 男）、家庭學習資源（1 多、2 一些、3 少）"],
 ["教師報告","`ATDGEAS`","ATG","教師對同一概念的三類報告，經 AST 連到學生"],
 ["權重／變異","`TOTWGT`、`MATWGT`、`JKZONE`、`JKREP`","ASG／AST","學生分析用 TOTWGT；與教師連結的分析用 MATWGT；JK 變數做 jackknife 標準誤"]],"表 3　研究變項（對照 codebook）")
P("連結規則依使用手冊 PDF 第 70–71、78–80 頁：學校資料用 `IDCNTRY`＋`IDSCHOOL` 接到學生；家庭資料用 `IDCNTRY`＋`IDSTUD`；教師資料只能經 AST 以 `IDCNTRY`＋`IDTEALIN` 連到學生。各連結的實測結果如下：")
T(["連結","鍵","2019","2023"],[
 ["ASG → ACG（學生接學校）","IDCNTRY＋IDSCHOOL",f"{fl9['asg_matched_acg']:,} / {fl9['students']:,} 位學生接上；校長檔每校一列：{'是' if fl9['acg_unique_school'] else '否'}",f"{fl3['asg_matched_acg']:,} / {fl3['students']:,} 位學生接上；每校一列：{'是' if fl3['acg_unique_school'] else '否'}"],
 ["ASG ↔ ASH（學生與家庭）","IDCNTRY＋IDSTUD",f"兩檔學生集合相同：{'是' if fl9['ash_ids_equal'] else '否'}（{fl9['ash_rows']:,} 列）",f"兩檔學生集合相同：{'是' if fl3['ash_ids_equal'] else '否'}（{fl3['ash_rows']:,} 列）"],
 ["AST → ATG（學生接教師）","IDCNTRY＋IDTEALIN",f"數學連結 {tf9['math_rows']:,} 列，{tf9['linked_to_atg']:,} 列接上；ATG 鍵唯一：{'是' if tf9['atg_key_unique'] else '否'}",f"數學連結 {tf3['math_rows']:,} 列，{tf3['linked_to_atg']:,} 列接上；ATG 鍵唯一：{'是' if tf3['atg_key_unique'] else '否'}"],
 ["同時有校長、教師、性別與家庭資源","—",f"{tf9['joint_rows']:,} 列／{tf9['joint_students']:,} 位學生／{tf9['joint_teachers']} 位教師／{tf9['joint_schools']} 校",f"{tf3['joint_rows']:,} 列／{tf3['joint_students']:,} 位學生／{tf3['joint_teachers']} 位教師／{tf3['joint_schools']} 校"]],"表 4　跨檔案連結的實測結果")
P(f"手冊（PDF 第 77 頁）說明教師權重只在 AST 內，且教師變項應視為學生的屬性、只與連結檔一起分析。所以教師模型另用 `MATWGT`，樣本和學生模型不同；同一位學生若有多位數學教師，會有多列（2019 年 {tf9['ast_students_dup_math']} 列、2023 年 {tf3['ast_students_dup_math']} 列是重複的學生）。")
# 樣本流程
T(["步驟","2019","2023"],[
 ["臺灣學生（ASG）",f"{fl9['students']:,}",f"{fl3['students']:,}"],
 ["學校（ACG）",f"{fl9['schools_acg']}",f"{fl3['schools_acg']}"],
 ["校長指標有效的學校（非常高／高／中）",f"{fl9['school_valid']}（{fl9['school_groups']['非常高']}／{fl9['school_groups']['高']}／{fl9['school_groups']['中']}）",f"{fl3['school_valid']}（{fl3['school_groups']['非常高']}／{fl3['school_groups']['高']}／{fl3['school_groups']['中']}）"],
 ["校長指標無效學校內的學生（不納入）",f"{fl9['students_in_invalid_school']}",f"{fl3['students_in_invalid_school']}"],
 ["校長指標有效的學生",f"{fl9['student_school_valid']:,}",f"{fl3['student_school_valid']:,}"],
 ["其中缺家庭資源（ASDGHRL）而不納入調整模型",f"{fl9['student_school_valid']-fl9['complete_cases']}",f"{fl3['student_school_valid']-fl3['complete_cases']}"],
 ["調整模型樣本（完整個案）",f"{fl9['complete_cases']:,}（{fl9['cc_schools']} 校）",f"{fl3['complete_cases']:,}（{fl3['cc_schools']} 校）"]],"表 5　樣本篩選流程")
# --- 4
H(2,"4. 統計方法與官方數字重現",'method')
P("TIMSS 是多階段分層抽樣，不能把學生當成簡單隨機樣本。依 2023 使用手冊（PDF 第 19、76–78 頁）：分析要用抽樣權重（學生分析用 `TOTWGT`；學校層級分析用 `SCHWGT`；教師變項用 `MATWGT`）；成就分數要用五個可能值（plausible values），每個可能值各算一次再整合；標準誤用 jackknife 重複抽樣（JRR），變數為 `JKZONE`、`JKREP`。")
P("估計方式：(1) 各可能值的估計量取平均；(2) 抽樣變異＝每個 jackknife 區把一個重複的權重乘 2、另一個乘 0，重算估計量，差距平方加總，再對五個可能值取平均；(3) 測量變異＝(1 + 1/5) × 五個估計量的樣本變異；總變異是兩者相加。迴歸係數、組平均與組間差都用同一套程序，差異的標準誤直接由重複估計得出（不是兩個標準誤相加）。顯著性用常態近似（手冊 PDF 第 30 頁說明比較用無限自由度的 t 檢定）。")
N("資料夾內查無 TIMSS 2023 Technical Report（手冊指向第 3、13、15 章），因此無法直接對照第 13 章的公式；我以「重現官方公布的臺灣數字」作為替代的驗證關卡。")
rows=[]
for _,r in GP.iterrows():
    rows.append([f"{int(r.year)}",{'ASMMAT':'數學總分','ASMNUM':'數','ASMGEO':'測量與幾何','ASMDAT':'資料','ASMKNO':'知識','ASMAPP':'應用','ASMREA':'推理'}[r.scale],f"{int(r.n):,}",f"{r.est:.1f}（{r.se:.2f}）",f"{int(r.off_mean)}（{r.off_se:.1f}）","吻合" if r.ok else "不吻合",r.source])
T(["年","量尺","n","本研究 平均（SE）","官方 平均（SE）","核對","官方值來源"],rows,"表 6　重現關卡 A：臺灣全體數學與領域平均（官方精度：平均四捨五入到整數、SE 到小數第 1 位）")
rows=[[x['exhibit'],x['measure'],f"{x['est']:.1f}（{x['se']:.2f}）",f"{x['off_est']}（{x['off_se']}）","吻合" if x['ok'] else "不吻合"] for x in GG]
T(["官方 Exhibit","量","本研究（SE）","官方（SE）","核對"],rows,"表 7　重現關卡 B：本研究主要變項的官方分組數字（TIMSS 2023 Exhibit 4.2.2 數學、4.2.3 科學；校長報告，四年級臺灣）")
P(f"兩個關卡共 {len(GP)+len(GG)} 個數字，**全部吻合**。2019 年的校長分組（官方 Exhibit 7.2）：學生比例 9／73／18%、平均 609／601／588；本研究為 {'／'.join(str(round(100*x['est'])) for x in R[y9]['shares'])}%、{'／'.join(str(round(x['est'])) for x in R[y9]['group_means_base'][:3])}，亦吻合（這組官方值取自你資料夾裡先前的紀錄 `published_subgroup_reproduction.csv`，本次未能重新取得 2019 官方網頁）。")
N("關卡 A 裡 2019 年三個內容領域（數、測量與幾何、資料）的官方值，以及 2019 年的認知領域，我這次無法重新從官方網站取得（2019 官方網頁不在可存取的網域內）。這三個內容領域值取自先前 R 腳本記錄；2019 認知領域沒有官方對照值，表中不列。2019 數學總分（599，SE 1.9）已由 TIMSS 2023 趨勢表（Exhibit 1.1.10）驗證。")
P("**一個重要的發現**：關卡 A 在 JKREP 的兩種雙倍權重慣例（JKREP＝0 加倍或 JKREP＝1 加倍）下都能通過，但關卡 B 只有「JKREP＝0 的重複權重乘 2」能讓全部 13 個數字吻合；另一種慣例下，「非常高」組的標準誤為 3.8，官方為 3.9。因此本報告採用能重現關卡 B 的慣例。估計值完全不受影響，只影響組別相關統計量的標準誤，差異不到 0.2（敏感度分析見第 9 節）。")
# --- 5
H(2,"5. 描述統計",'desc')
sh=R[y3]['shares']; sh9=R[y9]['shares']
T(["校長報告的重視程度","2019 學生%（SE）","2019 數學平均（SE）","2023 學生%（SE）","2023 數學平均（SE）"],
  [[LV[i],f"{pct(sh9[i]['est'])}（{pct(sh9[i]['se'])}）",f"{f1(R[y9]['group_means_base'][i]['est'])}（{f1(R[y9]['group_means_base'][i]['se'])}）",f"{pct(sh[i]['est'])}（{pct(sh[i]['se'])}）",f"{f1(R[y3]['group_means_base'][i]['est'])}（{f1(R[y3]['group_means_base'][i]['se'])}）"] for i in range(3)],
  "表 8　各重視程度組的學生比例與數學平均（校長指標有效的學生；TOTWGT 加權，jackknife SE）")
pass
comp=R[y3]['composition']; comp9=R[y9]['composition']
T(["重視程度組","2019 學校數","2019 家庭資源「多」","2023 學校數","2023 學生數","2023 女生%","2023 家庭資源「多」","2023 家庭資源「少」"],
  [[LV[i],f"{comp9[LV[i]]['schools']}",pct(comp9[LV[i]]['hrl_many']),f"{comp[LV[i]]['schools']}",f"{comp[LV[i]]['n']:,}",pct(comp[LV[i]]['female']),pct(comp[LV[i]]['hrl_many']),pct(comp[LV[i]]['hrl_few'])] for i in range(3)],
  "表 9　各重視程度組的組成（調整模型樣本，TOTWGT 加權）")
P(f"組成差異很大：2023 年「非常高」組的學生中 {pct(comp['非常高']['hrl_many'])} 家庭學習資源屬「多」，「中」組只有 {pct(comp['中']['hrl_many'])}。這是為什麼調整家庭學習資源後差距會縮小。同時，「非常高」與「中」兩組各只有 {fl3['school_groups']['非常高']} 與 {fl3['school_groups']['中']} 所學校（2019 年 {fl9['school_groups']['非常高']} 與 {fl9['school_groups']['中']} 所），有效樣本比學生人數所顯示的小得多，標準誤已反映這點。")
H(3,"5.1 數學領域成就與 2019→2023 變化")
SC=[('ASMMAT','數學總分'),('ASMNUM','數'),('ASMGEO','測量與幾何'),('ASMDAT','資料'),('ASMKNO','知識'),('ASMAPP','應用'),('ASMREA','推理')]
rows=[];drows=[]
for k,nm in SC:
    a=O[y9][k]['all'];b=O[y3][k]['all']; d,s_,p=dd({'est':a[0],'se':a[1]},{'est':b[0],'se':b[1]})
    rows.append([nm,f"{f1(a[0])}（{f1(a[1])}）",f"{f1(b[0])}（{f1(b[1])}）",f"{d:+.1f}",f1(s_),pf(p)]); drows.append((nm,a[0],b[0],p<0.05))
T(["量尺","2019 平均（SE）","2023 平均（SE）","變化","SE","p"],rows,"表 10　數學領域平均與變化（兩年為獨立樣本，SE＝√(SE₁²＋SE₂²)；此做法在總分上可重現官方趨勢表 Exhibit 1.1.10 的 −8（2.6），未另加連結誤差）")
FIG(dumbbell(drows,570,630),"圖 2　各領域 2019（橘）到 2023（藍）的變化；實線＝變化顯著（p<0.05），虛線＝不顯著。","七個量尺從 2019 到 2023 的變化。測量與幾何、資料、應用、推理上升；數與知識變化不顯著。")
# --- 6
H(2,"6. 主要結果：校長重視程度與數學成就",'main')
H(3,"6.1 組平均與組間差")
def rowmod(y,key,idx,lab):
    r=R[y][key][idx]; return [lab,f"{f1(r['est'])}",f1(r['se']),ci(r),pf(r['p'])]
rows=[]
for y in (y9,y3):
    for key,nm in (('group_means_base','未調整（校長有效學生）'),):
        for i,lab in ((3,'非常高 − 中'),(4,'高 − 中'),(5,'非常高 − 高')):
            r=R[y][key][i]; rows.append([y,lab,f1(r['est']),f1(r['se']),ci(r),pf(r['p'])])
T(["年","組間差（分）","估計","SE","95% CI","p"],rows,"表 11　未調整的組間差（數學總分）")
H(3,"6.2 調整性別與家庭學習資源")
rows=[]
for y in (y9,y3):
    for nm,key,i in (('非常高 vs 中（未調整，同一樣本）','M0',1),('非常高 vs 中（調整）','M1',1),('高 vs 中（未調整，同一樣本）','M0',2),('高 vs 中（調整）','M1',2),('女 vs 男','M1',3),('家庭資源 多 vs 一些','M1',4),('家庭資源 少 vs 一些','M1',5)):
        r=R[y][key][i]; rows.append([y,nm,f1(r['est']),f1(r['se']),ci(r),pf(r['p'])])
T(["年","項","係數（分）","SE","95% CI","p"],rows,"表 12　加權迴歸（結果＝數學五個可能值；參照組＝中、男生、家庭資源「一些」）")
fr=[]
for y,col in ((y9,C19),(y3,C23)):
    for key,nm in (('M0','非常高 vs 中・未調整'),('M1','非常高 vs 中・調整')):
        r=R[y][key][1]; fr.append((f"{nm}・{y}",r['est'],r['lo'],r['hi'],col))
FIG(forest(fr,-10,50,left=210,ref=0),"圖 3　「非常高 vs 中」的組間差與 95% CI。虛線為 0。","四個估計：兩年各有未調整與調整；調整後縮小，但 2023 的信賴區間未跨過 0。")
P(f"調整性別與家庭學習資源後，2023 年「非常高 vs 中」從 {f1(R[y3]['M0'][1]['est'])} 縮小為 {f1(m23['est'])} 分，縮小約 {100*(1-m23['est']/R[y3]['M0'][1]['est']):.0f}%；2019 年從 {f1(R[y9]['M0'][1]['est'])} 縮小為 {f1(m19['est'])} 分，縮小約 {100*(1-m19['est']/R[y9]['M0'][1]['est']):.0f}%。即使控制後仍有 2023 年 {m23['est']/sd23:.2f}（2019 年 {m19['est']/sd19:.2f}）個學生標準差的差距。「高 vs 中」在 2023 年調整後不顯著（{f1(R[y3]['M1'][2]['est'])}，p = {pf(R[y3]['M1'][2]['p'])}）；2019 年則顯著（{f1(R[y9]['M1'][2]['est'])}，p = {pf(R[y9]['M1'][2]['p'])}）。")
H(3,"6.3 連續量尺（敏感度）")
rows=[]
for y in (y9,y3):
    for key,nm in (('cont_M0','未調整'),('cont_M1','調整性別與家庭資源')):
        r=R[y][key][1]; rows.append([y,nm,f1(r['est']),f1(r['se']),ci(r),pf(r['p']),f"{R[y]['cont_n']:,}"])
T(["年","模型","每 +1 SD 的分數差","SE","95% CI","p","n"],rows,"表 13　以連續量尺 ACBGEAS 取代三類指標（每 1 個學生加權標準差）")
P(f"連續量尺的結果與三類指標方向一致：調整後每 +1 SD，2019 年 {f1(R[y9]['cont_M1'][1]['est'])} 分（p = {pf(R[y9]['cont_M1'][1]['p'])}），2023 年 {f1(R[y3]['cont_M1'][1]['est'])} 分（p = {pf(R[y3]['cont_M1'][1]['p'])}）。")
H(3,"6.4 2019 與 2023 的比較")
rows=[]
for i,lab in ((3,'非常高 − 中'),(4,'高 − 中'),(5,'非常高 − 高')):
    a=R[y9]['group_means_base'][i]; b=R[y3]['group_means_base'][i]; d,s_,p=dd(a,b)
    rows.append([lab,f1(a['est']),f1(b['est']),f"{d:+.1f}",f1(s_),pf(p)])
T(["組間差（未調整）","2019","2023","變化","SE","p"],rows,"表 14　組間差在兩年間的變化（兩年獨立樣本）")
P("三個組間差的變化都不顯著，所以資料不支持「關聯增強」或「關聯減弱」的說法；2023 的點估計較大，但不確定性也大。")
# --- 7 teacher
H(2,"7. 納入教師報告：學生、教師、校長三檔連結",'teacher')
cr=R[y3]['cross']['table']; cr9=R[y9]['cross']['table']
def agree(c): return sum(c[k][k] for k in ('1.0','2.0','3.0'))
P(f"在可連結到數學教師的學生中，校長與教師報告相同類別的比例（MATWGT 加權）：2019 年 {pct(agree(cr9))}、2023 年 {pct(agree(cr))}。兩位報告者只有約一半一致，所以兩者不是同一個測量。")
rows=[]
for y in (y9,y3):
    for nm,key,idxs in (('教師報告','T0_teacher',(1,2)),('校長報告（同一樣本）','T0_principal',(1,2))):
        for i in idxs:
            r=R[y][key][i]; rows.append([y,nm,r['term'].split('：')[1],f1(r['est']),f1(r['se']),ci(r),pf(r['p'])])
T(["年","報告者","比較","係數（分）","SE","95% CI","p"],rows,"表 15　教師與校長報告分開放入模型（MATWGT 加權，未調整其他變項）")
rows=[]
for y in (y9,y3):
    for i in (1,2,3,4):
        r=R[y]['T2_both_adj'][i]; rows.append([y,r['term'],f1(r['est']),f1(r['se']),ci(r),pf(r['p'])])
T(["年","項","係數（分）","SE","95% CI","p"],rows,"表 16　同時放入校長與教師報告，並控制性別與家庭資源")
tt=R[y3]['t_group_means']
P(f"2023 年教師報告為「非常高」的學生平均 {f1(tt[0]['est'])}，低於「高」組的 {f1(tt[1]['est'])}，沒有隨重視程度單調上升；校長報告的梯度則是 {f1(R[y3]['t_principal_means'][0]['est'])}／{f1(R[y3]['t_principal_means'][1]['est'])}／{f1(R[y3]['t_principal_means'][2]['est'])}。同時放入兩者後，校長報告的「非常高 vs 中」在 2023 年仍有 {f1(R[y3]['T2_both_adj'][1]['est'])} 分（p = {pf(R[y3]['T2_both_adj'][1]['p'])}），教師報告的「高 vs 中」有 {f1(R[y3]['T2_both_adj'][3+1]['est'])} 分（p = {pf(R[y3]['T2_both_adj'][3+1]['p'])}）。2019 年同時放入兩者後，校長「非常高 vs 中」為 {f1(R[y9]['T2_both_adj'][1]['est'])} 分（p = {pf(R[y9]['T2_both_adj'][1]['p'])}），教師「非常高 vs 中」為 {f1(R[y9]['T2_both_adj'][3]['est'])} 分（p = {pf(R[y9]['T2_both_adj'][3]['p'])}；教師「非常高」組只占 {pct(R[y9]['t_shares'][0]['est'])}）。兩年的樣式不同，兩位報告者各自對應不同面向的可能性不能排除，但本資料不能檢驗原因。")
# --- 8 support
H(2,"8. 領域變化與學習支持優先方向",'priority')
P("下表把前面的描述性證據整理成「值得優先關注」的方向。這裡的「優先」是依落差大小與統計證據排序的資料導向建議，不是在說某項措施有效。")
hr=O[y3]['ASMMAT']['hrl']; sx=O[y3]['ASMMAT']['sex']
T(["方向","資料證據","證據強度與限制"],[
 ["家庭學習資源較少的學生",f"2023 年家庭資源「多」平均 {f1(hr[0][0])}，「一些」{f1(hr[1][0])}，「少」{f1(hr[2][0])}；多 − 一些差 {f1(hr[5][0])}（SE {f1(hr[5][1])}）。「少」組僅占學生 {pct(O[y3]['hrl_share'][2][0])}（2019 年 {pct(O[y9]['hrl_share'][2][0])}）。","梯度非常穩定；「少」組樣本小、估計不精確，且兩年家庭資源題目有調整，三類比例的跨年變化不宜解讀為家庭條件改善。"],
 ["推理能力",f"推理為三個認知領域中最低（2023：{f1(O[y3]['ASMREA']['all'][0])}，知識 {f1(O[y3]['ASMKNO']['all'][0])}，應用 {f1(O[y3]['ASMAPP']['all'][0])}）；官方亦公布臺灣推理領域比整體低 18 分。推理 2019→2023 仍上升 {O[y3]['ASMREA']['all'][0]-O[y9]['ASMREA']['all'][0]:+.1f}。","落差一致且來自官方數字；但領域之間難度與題目組成不同，相對弱勢不等於教學缺失。"],
 ["「數」領域",f"內容領域中唯一未顯著上升者（{O[y3]['ASMNUM']['all'][0]-O[y9]['ASMNUM']['all'][0]:+.1f}，p = {pf(dd({'est':O[y9]['ASMNUM']['all'][0],'se':O[y9]['ASMNUM']['all'][1]},{'est':O[y3]['ASMNUM']['all'][0],'se':O[y3]['ASMNUM']['all'][1]})[2])}）；2023 年也是女生落差最大的領域（女 − 男 {f1(O[y3]['ASMNUM']['sex'][2][0])}，SE {f1(O[y3]['ASMNUM']['sex'][2][1])}）。","「未顯著」不等於「沒有變化」；信賴區間仍包含小幅增減。"],
 ["女生（2023）",f"總分女 − 男 {f1(sx[2][0])}（SE {f1(sx[2][1])}，p = {pf(2*(1-__import__('scipy.stats',fromlist=['norm']).norm.cdf(abs(sx[2][0]/sx[2][1]))))}）；2019 年 {f1(O[y9]['ASMMAT']['sex'][2][0])}（不顯著）。數與推理較大，資料領域無顯著差距。","兩年差距的變化不顯著（{:+.1f}，SE {:.1f}），不能說差距擴大。".format(dd({'est':O[y9]['ASMMAT']['sex'][2][0],'se':O[y9]['ASMMAT']['sex'][2][1]},{'est':sx[2][0],'se':sx[2][1]})[0],dd({'est':O[y9]['ASMMAT']['sex'][2][0],'se':O[y9]['ASMMAT']['sex'][2][1]},{'est':sx[2][0],'se':sx[2][1]})[1])],
 ["校長評為「中」重視的學校",f"2023 年這些學校（{fl3['school_groups']['中']} 校，占學生 {pct(sh[2]['est'])}）平均 {f1(R[y3]['group_means_base'][2]['est'])}，比「非常高」組低 {f1(u23['est'])} 分；調整後仍低 {f1(m23['est'])} 分。","這是學校分組的描述，不能推論「提高校長評分會提高成績」；也可能是未觀察到的學校特性（例如地區、學生背景）。適合當作識別需要更多資源的學校的訊號，而非介入目標。"]],"表 17　優先方向與證據")
P("領域與族群交叉的詳細數字（各領域的性別差、家庭資源差、校長組差）見附表 A1。")
rows=[]
for k,nm in SC:
    a=O[y3][k]
    rows.append([nm,f"{f1(a['sex'][2][0])}（{f1(a['sex'][2][1])}）",f"{f1(a['hrl'][3][0])}（{f1(a['hrl'][3][1])}）",f"{f1(a['principal'][3][0])}（{f1(a['principal'][3][1])}）",f"{f1(O[y9][k]['principal'][3][0])}（{f1(O[y9][k]['principal'][3][1])}）"])
T(["量尺","女 − 男（2023）","家庭資源 多 − 少（2023）","校長 非常高 − 中（2023）","校長 非常高 − 中（2019）"],rows,"附表 A1　各領域的組間差（SE）")
# --- 9
H(2,"9. 敏感度分析",'sens')
rows=[]
for y in (y9,y3):
    a=S[y]['0'][1];b=S[y]['1'][1];c=S[y]['no_few'][1]
    rows.append([y,f"{f1(a[0])}（{f1(a[1])}）",f"{f1(b[0])}（{f1(b[1])}）",f"{f1(c[0])}（{f1(c[1])}）",f1(S[y]['unweighted_ols'][1])])
T(["年","採用的 JRR 慣例：非常高 vs 中（SE）","另一種 JRR 慣例（SE）","排除家庭資源「少」的學生（SE）","未加權 OLS（僅供對照）"],rows,"表 18　調整後「非常高 vs 中」的穩健性")
P("四種做法都得到同方向、量級相近的估計；兩種 JRR 慣例的標準誤相差不到 0.2 分，不影響任何結論。未加權 OLS 只作對照，不具推論意義。")
# --- 10
H(2,"10. 解讀：相關與因果",'interp')
L(["**可以說的**：2019 與 2023 年，校長認為學校「非常高」重視學業成功的學生，數學平均高於認為「中」的學校的學生；這個差距在控制性別與家庭學習資源後仍存在。",
   "**不能說的**：不能說校長的重視程度造成較高成績，也不能說提高重視程度會提高成績。可能的其他解釋包括：(1) 學生原有程度與家庭背景（只控制了家庭學習資源一項）；(2) 反向：成績較好的學校，校長更傾向給高分；(3) 共同原因：例如學校資源、地區、師資；(4) 報告者偏誤：評分是主觀的，三類指標的切分點由量尺決定，非原始選項。",
   "**教師與校長不一致**：教師報告沒有單調梯度，兩者只有約一半一致；這提醒我們「學校重視學業成功」不是單一、客觀的屬性。"])
# --- 11
H(2,"11. 研究限制",'limits')
L(["**設計**：重複橫斷面、觀察資料，無法識別因果，也不能逐人追蹤。",
   f"**學校數量少**：「非常高」與「中」組各只有 {fl3['school_groups']['非常高']} 與 {fl3['school_groups']['中']} 所學校（2019 年 {fl9['school_groups']['非常高']} 與 {fl9['school_groups']['中']} 所）；群集抽樣使有效樣本量受學校數限制。標準誤已由 jackknife 反映，但估計仍不精確，組間差的信賴區間很寬。",
   "**只有三類**：codebook 定義此指標只有三個值（1 非常高、2 高、3 中），沒有「低」類，所以無法比較重視程度更低的學校。",
   "**控制變項有限**：只控制性別與家庭學習資源；未控制學校所在地、學生先備知識、班級規模等（codebook 有學校所在地 `ACBG05A/B`，可作後續分析）。家庭學習資源題目在兩年間有調整，其「少」組在 2023 年只占約 2%。",
   "**兩年可比性**：同名變項的題目需逐題核對（如 `ACBG14` 在兩年意義不同）；量尺的建構規則在技術報告第 15 章，資料夾內查無，所以 `ACBGEAS`／`ACDGEAS` 跨年等值我只能用題目標籤判斷。",
   "**重現關卡的資料來源**：2019 內容領域的官方值取自先前記錄，2019 認知領域沒有官方對照；TIMSS 2023 Technical Report 不在資料夾內，JRR 公式未能直接對照。",
   "**未做多層次模型**：本報告使用設計型推論（權重＋JRR），沒有估計學校層級的變異成分；若要分離學校間與學校內差異，可另做多層次分析。",
   "**多重比較**：表格列出多個組間差與領域，沒有做多重比較校正；請把 p 值視為描述性線索。",
   "**翻譯與名詞**：本報告的變項說明與中文用語是我自己整理，不是官方譯名。"])
# --- 12
H(2,"12. 重現方式與檔案",'repro')
P("所有數字由 `analysis_py/` 資料夾內的 Python 程式從 .sav 檔計算：`savreader.py`（讀檔）→ `timsslib.py`（JRR 與可能值整合）→ `gate.py`（重現關卡 A）→ `main.py`、`domains.py`、`sens.py`（分析）→ `build_report.py`（產生本報告）。程式不依賴 R 或 pyreadstat。")
P("與你先前以 R 完成的結果交叉比對：2019 與 2023 的組平均、組間差與調整模型係數（表 8、表 11、表 12 的點估計，例如 2023 年「非常高 vs 中」21.1125 分）在小數點後四位內都相同；標準誤相差不到 0.2，來源是 JRR 慣例（第 4 節）。")
P("**資料與文件來源**：`T23_UG_International-Database.pdf`（PDF 第 19、57、58、70–71、74、76–80 頁）；`T23_Codebook_G4.xlsx`；`T19_G4_Codebook.xlsx`；十個 .sav 檔。官方公布值：TIMSS 2023 International Results（Exhibit 1.1.1、1.1.10、1.1.13、1.1.14、4.2.2、4.2.3，timss2023.org）。")
# ======== 渲染 ========
def inl_md(t): return t
def inl_html(t):
    t=html.escape(t,quote=False)
    t=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',t)
    t=re.sub(r'`([^`]+)`',r'<code>\1</code>',t)
    return t
# md
md=[]
for b in B:
    k=b[0]
    if k=='h': md.append('\n'+'#'*b[1]+' '+b[2]+'\n')
    elif k=='p': md.append(b[1]+'\n')
    elif k=='sum': md.append('- '+b[1])
    elif k=='l': md.append('\n'.join('- '+x for x in b[1])+'\n')
    elif k=='n': md.append('> '+b[1]+'\n')
    elif k=='t':
        md.append(f"\n**{b[3]}**\n" if b[3] else '')
        md.append('| '+' | '.join(b[1])+' |'); md.append('|'+'|'.join('---' for _ in b[1])+'|')
        for r in b[2]: md.append('| '+' | '.join(str(c).replace('|','／') for c in r)+' |')
        md.append('')
    elif k=='f': md.append(f"\n*{b[2]}*（圖像見 HTML 版；數字見對應表格）\n")
open('out/report.md','w',encoding='utf-8').write('\n'.join(md).replace('p = <0.001','p < 0.001'))
# html
nav=[(b[3],b[2]) for b in B if b[0]=='h' and b[1]==2]
body=[];insum=False
for b in B:
    k=b[0]
    if k!='sum' and insum: body.append('</ul></div>'); insum=False
    if k=='h':
        if b[1]==1: body.append(f'<h1 id="{b[3]}">{inl_html(b[2])}</h1>')
        else: body.append(f'<h{b[1]} id="{b[3] or ""}">{inl_html(b[2])}</h{b[1]}>'.replace(' id=""',''))
    elif k=='p': body.append(f'<p>{inl_html(b[1])}</p>')
    elif k=='sum':
        if not insum: body.append('<div class="sumbox"><h2 class="sumh">結論先看這裡</h2><ul>'); insum=True
        body.append(f'<li>{inl_html(b[1])}</li>')
    elif k=='l': body.append('<ul>'+''.join(f'<li>{inl_html(x)}</li>' for x in b[1])+'</ul>')
    elif k=='n': body.append(f'<aside class="note">{inl_html(b[1])}</aside>')
    elif k=='t':
        th=''.join(f'<th scope="col">{inl_html(h)}</th>' for h in b[1])
        tr=''.join('<tr>'+''.join(f'<td>{inl_html(str(c))}</td>' for c in r)+'</tr>' for r in b[2])
        body.append(f'<figure class="tbl"><figcaption>{inl_html(b[3] or "")}</figcaption><div class="scroll"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div></figure>')
    elif k=='f': body.append(f'<figure class="fig"><div role="img" aria-label="{html.escape(b[3])}">{b[1]}</div><figcaption>{inl_html(b[2])}</figcaption></figure>')
# 取代：把 h1 與前導段落包成 hero
page=open('template.html',encoding='utf-8').read()
navh=''.join(f'<a href="#{i}">{html.escape(t)}</a>' for i,t in nav)
page=page.replace('{{TITLE}}',html.escape(TITLE)).replace('{{NAV}}',navh).replace('{{BODY}}','\n'.join(body)).replace('{{SUB}}',html.escape(SUB))
open('out/report.html','w',encoding='utf-8').write(page.replace('p = &lt;0.001','p &lt; 0.001').replace('p = <0.001','p < 0.001'))
print('OK',len(page)//1024,'KB html;',len('\n'.join(md))//1024,'KB md')
