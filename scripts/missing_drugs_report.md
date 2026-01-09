# Missing Drug Data Report (Refined)

This report lists drugs identified in the `ppt_content/*.md` files that are missing from the application's databases after careful normalization and synonym checking.

## 1. Drugs Missing from Database entirely (No Card)
| Chinese Name | English Name | PPT File | Reason |
| :--- | :--- | :--- | :--- |
| 氯琥珀胆碱 | Succinylcholine Chloride | 10.md | Not found in `data.json` |
| 碘解磷定 | Pralidoxime Iodide | 10.md | Not found in `data.json` |
| 碘解磷定 | PAM | 10.md | Not found in `data.json` |
| 曼尼希反应 | Mannich反应 | 10.md | Not found in `data.json` |
| 胆碱受体激动剂的药效团单元 | Pharmacophoric elements | 10.md | Not found in `data.json` |
| 色甘酸钠 | Cromolyn Sodium | 11.md | Not found in `data.json` |
| H1 受体拮抗剂构效关系 | SAR | 11.md | Not found in `data.json` |
| H2受体拮抗剂的构效关系 | SAR | 12.md | Not found in `data.json` |
| 质子泵抑制剂 (PPI) 的构效关系 | SAR | 12.md | Not found in `data.json` |

## 2. Drugs Missing Descriptions (Key Points)
| Chinese Name | English Name | PPT File | In `data.json`? | Reason |
| :--- | :--- | :--- | :--- | :--- |
| 盐酸苯海索 | Benzhexol Hydrochloride | 10.md | Yes | Not found in `keyPointsData.js` |
| 氢溴酸山莨菪碱 | 654-2 | 10.md | Yes | Not found in `keyPointsData.js` |
| 氯琥珀胆碱 | Suxamethonium Chloride | 10.md | Yes | Not found in `keyPointsData.js` |
| 碘解磷定 | PAM | 10.md | No | Not found in `keyPointsData.js` |
| 曼尼希反应 | Mannich反应 | 10.md | No | Not found in `keyPointsData.js` |
| 马来酸氯苯那敏 | 扑尔敏 | 11.md | Yes | Not found in `keyPointsData.js` |
| 盐酸哌替啶 | 杜冷丁 | 8.md | Yes | Not found in `keyPointsData.js` |
| 对乙酰氨基酚 | 扑热息痛 | 9.md | Yes | Not found in `keyPointsData.js` |
| 吲哚美辛 | Indometacin | 9.md | Yes | Not found in `keyPointsData.js` |
