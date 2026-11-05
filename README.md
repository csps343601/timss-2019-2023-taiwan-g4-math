# TIMSS 2019–2023 臺灣四年級數學研究

[閱讀網頁版研究報告](https://csps343601.github.io/timss-2019-2023-taiwan-g4-math/) · [下載 Markdown 報告](TIMSS2019_2023_校長學業成功重視與數學成就_研究報告.md) · [下載期中簡報](TIMSS_2019_2023_期中專題提案_純TIMSS.pptx)

本專案比較 TIMSS 2019 與 2023 臺灣國小四年級的數學內容及認知領域成就，並分析性別、家庭學習資源與校長報告的學校重視學業成功程度。兩輪是不同學生的重複橫斷面，結果不能解讀為個人成長或疫情的因果效果。

## 資料與重現

原始資料由 [IEA TIMSS International Database](https://www.iea.nl/data-tools/repository/timss) 取得。發布資料夾僅包含研究報告、簡報、分析程式和彙整統計；**不包含學生、教師或校長層級原始資料**。

將官方下載的 TIMSS 2019 與 2023 臺灣四年級 SPSS 檔依分析程式所列路徑放置後，在 R 安裝 `foreign` 套件，依序執行：

```powershell
Rscript official_timss_reproduction_gate.R
Rscript analyze_timss_principal_emphasis.R
```

先檢查 `official_timss_reproduction_gate.csv` 的八筆 `pass` 是否皆為 `TRUE`，再檢視 `timss_principal_output/` 的分析結果。估計使用權重、五個 plausible values 與 `JKZONE`／`JKREP` jackknife；方法與限制見網頁報告。

## 網站

本報告透過 GitHub Pages 從 `main` 分支根目錄發布：[開啟公開網站](https://csps343601.github.io/timss-2019-2023-taiwan-g4-math/)。

