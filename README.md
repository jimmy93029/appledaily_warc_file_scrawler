# 蘋果日報語言模型資料整理

工作日誌: https://hackmd.io/@jimmywupika/HyfuxFiF6 

原始資料：https://archive.fart.website/archivebot/viewer/job/202209030158271bpf8

資料擁有單位：蘋果日報

語言：繁體中文

格式： json

資料時間：2003 到 2022

訓練資料描述：訓練資料擷取自蘋果日報的新聞，其新聞發布年份從 2003 到 2022 不等。另外，資料當中的廣告已適當地處理掉了，各種新聞的主題也可以從 "subjects" 欄位中查看。

資料筆數：約 953175 筆

大小：約 4.3 GB

下載：

範例資料:

```json!
{
    "uri": "https//www.appledaily.com.tw/entertainment/20220824/724E2C670A6767BFA1ADA8478E",
    "standard": {
      "name": "ninjs",
      "version": "2.1",
      "schema": "https://iptc.org/std/ninjs/ninjs-schema_2.1.json"
    },
    "firstcreated": "2022-08-24",
    "versioncreated": "2022-09-03",
    "contentcreated": "2024-02-15",
    "type": "text",
    "language": "zh-Hant-TW",
    "headlines": [
      {
        "role": "main",
        "value": "時尚｜RIMOWA溝槽紋美妝手機殼　多色炫彩俏搭行李箱｜蘋果新聞網｜蘋果日報"
      }
    ],
    "subjects": [
      {
        "name": "entertainment"
      }
    ],
    "bodies": [
      {
        "role": "main",
        "value": "\n以前衛而耐用設計行李箱打響時尚美名的德國品牌RIMOWA，為許多商務差旅人士、旅行生活家所愛用，品牌至今124年歷史的工藝底蘊，也在近年於行李箱之外，開拓包括箱型小包款、iPhone Accessories手機配件等新旅行配件類別，設計上也連貫經典行李箱溝槽式設計外觀及品牌Logo，即呈現一如既往地細膩奢華質感，最新開賣的iPhone 13 Pro /Pro Max手機保護殼，並推出多款色彩選擇，還能搭配自己的行李箱顏色，展現個人美感品味。\n\n新款RIMOWA手機保護殼，採用聚碳酸酯材質製作，以細膩的溝槽式紋路提供舒適順手的抓握手機感，同時保護手機避免磨損和刮擦，並且輕量。\n\n保護殼分別以iPhone 13 Pro與iPhone 13 Pro Max兩款手機型號尺寸，推出包括金屬銀色、炫
彩、薰衣草紫、霧黑色與火鶴紅等色款，其中光澤質感高級的銀色款，風格簡約低調；炫彩款式則流淌著細膩精緻的光線游彩；薰衣草紫則散發著南法浪漫氣息；火鶴紅的搶眼和
熱情更是充滿個性，還有霧黑色款的穩重，色色皆美型。"
      }
    ],
    "by": "###",
    "located": "台北報導",
    "altids": [
      {
        "role": "internal",
        "value": "724E2C670A6767BFA1ADA8478E"
      }
    ]
  }
```
