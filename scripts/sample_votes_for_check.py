"""Выбирает 5 случайных голосований из данных, на которых построены графики,
чтобы проверить их вручную в UN Digital Library (https://digitallibrary.un.org).

Запуск из корня проекта:  python3 scripts/sample_votes_for_check.py
Seed (начальное число генератора) фиксирован, поэтому каждый раз выпадают те же 5 голосований.
"""
from pathlib import Path

import pandas as pd
import pyreadr

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "v33" / "UNVotes-1.RData"
OUT = ROOT / "data" / "processed" / "random_votes_to_check.csv"
SEED = 2026
COUNTRIES = {2: "США", 220: "Франция", 365: "СССР/Россия", 710: "Китай (КНР)", 713: "Китай (Китайская Республика)"}
VOTE = {1: "за", 2: "воздержался", 3: "против", 8: "отсутствовал", 9: "не член ООН"}

v = pyreadr.read_r(RAW)["completeVotes"]
v["ccode"] = pd.to_numeric(v["ccode"])
v["year"] = pd.to_datetime(v["date"]).dt.year
v = v[(v["para"] != 1) & (v["amend"] != 1) & (v["year"] <= 2023)]

# Те же голосования, что на графиках: хотя бы одна из стран проголосовала (за/возд./против)
ours = v[v["ccode"].isin(COUNTRIES) & v["vote"].isin([1, 2, 3])]
chosen = pd.Series(ours["rcid"].unique()).sample(5, random_state=SEED).sort_values()

rows = []
for rcid in chosen:
    one = v[v["rcid"] == rcid]
    info = one.iloc[0]
    row = dict(rcid=rcid, date=str(info["date"]), session=int(info["session"]),
               resolution=info["unres"],
               short=(info["short"] if isinstance(info["short"], str) and info["short"].strip()
                      else str(info["descr"]).split(":")[0].strip()))
    votes = one[one["ccode"].isin(COUNTRIES)].set_index("ccode")["vote"]
    for code, name in COUNTRIES.items():
        row[name] = VOTE.get(votes.get(code), "нет записи")
    totals = one["vote"].value_counts()
    row["итог (за–против–возд.)"] = f'{totals.get(1, 0)}–{totals.get(3, 0)}–{totals.get(2, 0)}'
    rows.append(row)

table = pd.DataFrame(rows)
OUT.parent.mkdir(parents=True, exist_ok=True)
table.to_csv(OUT, index=False)
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 60)
print(table.to_string(index=False))
