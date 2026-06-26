#!/usr/bin/env python3
from pathlib import Path
from urllib.request import urlretrieve
PDF_DIR = Path(__file__).resolve().parent / 'pdfs'
PDF_DIR.mkdir(exist_ok=True)
PAPERS = [
  [
    "P01",
    "chalaki2021priority",
    "https://arxiv.org/pdf/2109.05573"
  ],
  [
    "P02",
    "chen2021conflictfree",
    "https://arxiv.org/pdf/2107.07179"
  ],
  [
    "P03",
    "chen2021lanechanging",
    "https://arxiv.org/pdf/2109.14175"
  ],
  [
    "P04",
    "luo2023realtime",
    "https://arxiv.org/pdf/2205.01278"
  ],
  [
    "P05",
    "bai2022hybrid",
    "https://arxiv.org/pdf/2201.07833"
  ],
  [
    "P06",
    "jiang2023ecodriving",
    "https://arxiv.org/pdf/2206.12065"
  ],
  [
    "P07",
    "lakshmanan2022cooperative",
    "https://arxiv.org/pdf/2206.12360"
  ],
  [
    "P08",
    "mahbub2022safety",
    "https://arxiv.org/pdf/2203.05739"
  ],
  [
    "P09",
    "dong2023overtaking",
    "https://arxiv.org/pdf/2306.09736"
  ],
  [
    "P10",
    "klimke2026realworld",
    "https://arxiv.org/pdf/2403.16478"
  ],
  [
    "P11",
    "zhao2025spatial",
    "https://arxiv.org/pdf/2412.04290"
  ],
  [
    "P12",
    "yu2025uncertainty",
    "https://arxiv.org/pdf/2505.19939"
  ],
  [
    "P13",
    "liu2023systematic",
    "https://arxiv.org/pdf/2303.05665"
  ],
  [
    "P14",
    "cederle2024distributed",
    "https://arxiv.org/pdf/2405.08655"
  ],
  [
    "P15",
    "li2023dhal",
    "https://arxiv.org/pdf/2303.02630"
  ]
]
for pid, key, url in PAPERS:
    target = PDF_DIR / f'{pid}_{key}.pdf'
    if target.exists() and target.stat().st_size > 1000:
        print(f'skip {target.name}')
        continue
    print(f'download {target.name} <- {url}')
    urlretrieve(url, target)
