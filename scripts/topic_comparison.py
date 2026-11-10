"""Сравнение голосования США, Франции, СССР/России и Китая (КНР) по темам.

Запуск из корня проекта:  python3 scripts/topic_comparison.py

Что считаем (только голосования по резолюциям целиком, год — из даты голосования):
1. Доля «за» у каждой страны по каждой теме = за / (за + воздержался + против).
2. Индекс совпадения для каждой пары стран: по каждому голосованию, где обе страны
   проголосовали, 1 — одинаково, 0.5 — одна воздержалась, а другая нет, 0 — одна «за»,
   другая «против» (как agreement score у Лейпхарта). Затем среднее по теме.
Периоды: 1971–1991 (холодная война, КНР уже в ООН) и 1992–2023.
Темы — отметки из данных Voeten (me, nu, di, co, hr, ec); у голосования может быть
несколько тем сразу, тогда оно учитывается в каждой.
"""
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyreadr

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "v33" / "UNVotes-1.RData"
PROC = ROOT / "data" / "processed"
FIG = ROOT / "figures"

COUNTRIES = {2: "США", 220: "Франция", 365: "СССР/Россия", 710: "Китай"}
COLORS = {"США": "#1f5fbf", "Франция": "#8e44ad", "СССР/Россия": "#c0392b", "Китай": "#e69500"}
TOPICS = {
    "me": "Палестина и\nБлижний Восток",
    "nu": "Ядерное\nоружие",
    "di": "Разоружение",
    "co": "Колониализм",
    "hr": "Права\nчеловека",
    "ec": "Экономическое\nразвитие",
    "all": "Все\nголосования",
}
PERIODS = {"1971–1991": (1971, 1991), "1992–2023": (1992, 2023)}

v = pyreadr.read_r(RAW)["completeVotes"]
v["ccode"] = pd.to_numeric(v["ccode"])
v["year"] = pd.to_datetime(v["date"]).dt.year
v = v[(v["para"] != 1) & (v["amend"] != 1) & v["vote"].isin([1, 2, 3])
      & v["ccode"].isin(COUNTRIES) & v["year"].between(1971, 2023)]
v["period"] = pd.cut(v["year"], [1970, 1991, 2023], labels=list(PERIODS))

# Широкая таблица: одна строка = одно голосование, колонки = голоса 4 стран
topics_of_vote = v.drop_duplicates("rcid").set_index("rcid")[["period", *list(TOPICS)[:-1]]].fillna(0)
topics_of_vote["all"] = 1
wide = v.pivot_table(index="rcid", columns="ccode", values="vote", aggfunc="first").rename(columns=COUNTRIES)
wide = wide.join(topics_of_vote)


def agreement(a, b):
    both = a.notna() & b.notna()
    a, b = a[both], b[both]
    score = np.where(a == b, 1.0, np.where((a == 2) | (b == 2), 0.5, 0.0))
    return score.mean(), len(score)


yes_rows, pair_rows = [], []
for period in PERIODS:
    for t in TOPICS:
        sub = wide[(wide["period"] == period) & (wide[t] == 1)]
        for c in COUNTRIES.values():
            s = sub[c].dropna()
            yes_rows.append(dict(period=period, topic=t, country=c, n_votes=len(s),
                                 yes_share=(s == 1).mean()))
        for c1, c2 in combinations(COUNTRIES.values(), 2):
            score, n = agreement(sub[c1], sub[c2])
            pair_rows.append(dict(period=period, topic=t, pair=f"{c1} – {c2}", n_votes=n, agreement=score))

yes = pd.DataFrame(yes_rows)
pairs = pd.DataFrame(pair_rows)
PROC.mkdir(parents=True, exist_ok=True)
yes.to_csv(PROC / "topic_yes_share.csv", index=False)
pairs.to_csv(PROC / "topic_pair_agreement.csv", index=False)

# --- Рисунок 1: доля «за» по темам ---
FIG.mkdir(exist_ok=True)
fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharey=True)
x = np.arange(len(TOPICS))
w = 0.2
for ax, period in zip(axes, PERIODS):
    d = yes[yes["period"] == period]
    for i, c in enumerate(COUNTRIES.values()):
        vals = d[d["country"] == c].set_index("topic").loc[list(TOPICS), "yes_share"] * 100
        ax.bar(x + (i - 1.5) * w, vals, w, color=COLORS[c], label=c)
    ax.set_xticks(x, TOPICS.values(), fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Голосов «за», %")
    ax.set_title(period, loc="left", fontsize=11)
    ax.grid(axis="y", alpha=0.3)
    ax.axvline(len(TOPICS) - 1.5, color="grey", lw=0.8)
axes[0].legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.2), frameon=False)
fig.suptitle("Доля голосов «за» по темам (резолюции целиком)", y=0.985)
fig.text(0.01, 0.005, "Данные: Voeten, UNGA Voting Data (v33). Доля = за / (за + воздержался + против).",
         fontsize=7, color="grey")
fig.tight_layout(rect=(0, 0.02, 1, 0.99))
fig.subplots_adjust(top=0.87)
fig.savefig(FIG / "topic_yes_share.png", dpi=150)

# --- Рисунок 2: тепловая карта совпадения пар ---
pair_order = [f"{a} – {b}" for a, b in combinations(COUNTRIES.values(), 2)]
fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
for ax, period in zip(axes, PERIODS):
    m = (pairs[pairs["period"] == period].pivot(index="pair", columns="topic", values="agreement")
         .loc[pair_order, list(TOPICS)] * 100)
    im = ax.imshow(m.values, cmap="RdYlBu", vmin=0, vmax=100, aspect="auto")
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            val = m.values[i, j]
            ax.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=9,
                    color="white" if val < 20 or val > 85 else "black")
    ax.set_xticks(range(len(TOPICS)), [t.replace("\n", " ") for t in TOPICS.values()],
                  rotation=35, ha="right", fontsize=9)
    ax.set_yticks(range(len(pair_order)), pair_order, fontsize=9)
    ax.set_title(period, fontsize=11)
fig.colorbar(im, ax=axes, shrink=0.8, label="Индекс совпадения, % (100 = всегда одинаково)")
fig.suptitle("Насколько одинаково голосуют пары стран, по темам")
fig.text(0.01, -0.22, "1 — одинаковый голос, 0,5 — одна страна воздержалась, 0 — «за» против «против». "
         "Данные: Voeten, UNGA Voting Data (v33).", fontsize=7, color="grey")
fig.savefig(FIG / "topic_agreement.png", dpi=150, bbox_inches="tight")

print("Готово: figures/topic_yes_share.png, figures/topic_agreement.png, data/processed/topic_*.csv")
