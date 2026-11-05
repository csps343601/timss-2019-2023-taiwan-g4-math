# TIMSS 2019–2023 臺灣四年級數學研究

[閱讀網頁版研究報告](index.html) · [下載 Markdown 報告](TIMSS2019_2023_校長學業成功重視與數學成就_研究報告.md) · [下載期中簡報](TIMSS_2019_2023_期中專題提案_純TIMSS.pptx)

本專案比較 TIMSS 2019 與 2023 臺灣國小四年級的數學內容及認知領域成就，並分析性別、家庭學習資源與校長報告的學校重視學業成功程度。兩輪是不同學生的重複橫斷面，結果不能解讀為個人成長或疫情的因果效果。

## 資料與重現

原始資料由 [IEA TIMSS International Database](https://www.iea.nl/data-tools/repository/timss) 取得。發布資料夾僅包含研究報告、簡報、分析程式和彙整統計；**不包含學生、教師或校長層級原始資料**。

將官方下載的 TIMSS 2019 與 2023 臺灣四年級 SPSS 檔依分析程式所列路徑放置後，在 R 安裝 `foreign` 套件，依序執行：

```powershell
Rscript official_timss_reproduction_gate.R
Rscript analyze_timss_principal_emphasis.R
```

先檢查 `official_timss_reproduction_gate.csv` 的八筆 `pass` 是否皆為 `TRUE`，再檢視 `timss_principal_output/` 的分析結果。估計使用權重、五個 plausible values 與 `JKZONE`／`JKREP` jackknife；方法與限制見網頁報告。

## 發布到 GitHub Pages

1. 在 GitHub 建立新的 repository，不要預先加入 README。
2. **只在本發布資料夾內**開啟 PowerShell，執行：

```powershell
git init
git add .
git commit -m "Publish TIMSS 2019–2023 research report"
git branch -M main
git remote add origin https://github.com/你的帳號/你的儲存庫.git
git push -u origin main
```

3. 到 repository 的 **Settings → Pages → Build and deployment**，選 **Deploy from a branch**，設定 **main** 和 **/(root)**，按 **Save**。
4. GitHub 顯示網站網址後，開啟首頁檢查報告與下載連結。預設網址通常是 `https://你的帳號.github.io/你的儲存庫/`。

公開 repository 任何人都可讀取成果。若需限制讀取權限，請先確認你的 GitHub Pages 方案與儲存庫設定。
