import numpy as np, pandas as pd
NPV=5
def pvcols(prefix): return [f"{prefix}{i:02d}" for i in range(1,NPV+1)]

def jrr(d, wcol, stat, use_pv=True, zone='JKZONE', rep='JKREP', dbl=0):
    """d: 已篩選好的資料；stat(d, w, p) 回傳一維陣列（第 p 個 plausible value 的估計量）。
    回傳 (估計值, 標準誤, 內部資訊)。
    作法（與 UG 指定的 IDB Analyzer 邏輯一致）：
      - 估計值：各 PV 的估計量平均
      - 抽樣變異：對每個 jackknife 區（JKZONE），JKREP==dbl（預設 0）權重×2、另一重複權重×0（此慣例可重現官方 Exhibit 4.2.2／4.2.3 的臺灣組別標準誤；dbl=1 為另一種慣例），其餘不變，
        重算估計量，差距平方加總；再對 5 個 PV 取平均
      - 測量（插補）變異：(1+1/5) × 各 PV 估計量之樣本變異（ddof=1）
    """
    w0 = d[wcol].to_numpy(float)
    z = d[zone].to_numpy(); r = d[rep].to_numpy()
    zones = np.unique(z)
    P = range(NPV) if use_pv else [0]
    theta = np.array([np.atleast_1d(stat(d, w0, p)) for p in P])
    samp = np.zeros(theta.shape[1])
    for pi, p in enumerate(P):
        for zz in zones:
            w = w0.copy(); idx = z == zz
            w[idx] = w[idx] * np.where(r[idx] == dbl, 2.0, 0.0)
            th = np.atleast_1d(stat(d, w, p))
            samp += (th - theta[pi]) ** 2
    samp /= len(P)
    est = theta.mean(axis=0)
    imp = (1 + 1 / NPV) * theta.var(axis=0, ddof=1) if use_pv else 0.0
    se = np.sqrt(samp + imp)
    return est, se, dict(samp=samp, imp=imp, nzones=len(zones))

def wmean(y, w): return np.sum(w * y) / np.sum(w)

def wls(X, y, w):
    XtW = X.T * w
    return np.linalg.solve(XtW @ X, XtW @ y)

def tstat(est, se): 
    from scipy import stats
    t = est / se
    return t, 2 * (1 - stats.norm.cdf(abs(t)))
