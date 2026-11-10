"""График: доля голосов «за» по годам для Франции, СССР/России, США и Китая.

Данные: UNVotes-1.RData из версии 33 датасета Voeten (скачивается scripts/download_data.sh).
Запуск из корня проекта:  python3 scripts/plot_yes_share.py

Методика:
- год берём из даты голосования (колонка `year` в файле содержит ошибки, например
  у 78-й сессии стоит 2022, хотя голосования шли в 2023–2024);
- 2024 год отбрасываем: в файле есть только голосования до июня;
- считаем только голосования по резолюциям целиком (без отдельных абзацев и поправок),
  потому что абзацы и поправки попадали в данные в разные годы очень по-разному;
- доля «за» = «за» / («за» + «воздержался» + «против»); отсутствия не учитываются;
- СССР и Россия в данных — один код COW 365;
- Китай: КНР (код 710) — с 1971 года; до этого место Китая занимала
  Китайская Республика (Тайвань, код 713), её показываем пунктиром.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pyreadr

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "v33" / "UNVotes-1.RData"
OUT_CSV = ROOT / "data" / "processed" / "yes_share_by_year.csv"
OUT_PNG = ROOT / "figures" / "yes_share_by_year.png"

COUNTRIES = {
    2: ("США", "#1f5fbf", "-"),
    220: ("Франция", "#8e44ad", "-"),
    365: ("СССР / Россия", "#c0392b", "-"),
    710: ("Китай (КНР)", "#e69500", "-"),
    713: ("Китай (Китайская Республика, до 1971)", "#e69500", ":"),
}
LAST_FULL_YEAR = 2023

votes = pyreadr.read_r(RAW)["completeVotes"]
votes["ccode"] = pd.to_numeric(votes["ccode"])
votes["year"] = pd.to_datetime(votes["date"]).dt.year

whole_resolutions = (votes["para"] != 1) & (votes["amend"] != 1)  # пусто = резолюция целиком
cast = votes["vote"].isin([1, 2, 3])  # 1 за, 2 воздержался, 3 против
sel = votes[whole_resolutions & cast & votes["ccode"].isin(COUNTRIES.keys())
            & (votes["year"] <= LAST_FULL_YEAR)]

table = (sel.assign(yes=sel["vote"].eq(1))
            .groupby(["ccode", "year"])
            .agg(n_votes=("yes", "size"), yes_share=("yes", "mean"))
            .reset_index())
table["country"] = table["ccode"].map(lambda c: COUNTRIES[c][0])
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
table.to_csv(OUT_CSV, index=False)

fig, ax = plt.subplots(figsize=(11, 6))
for code, (label, color, style) in COUNTRIES.items():
    d = table[table["ccode"] == code]
    ax.plot(d["year"], d["yes_share"] * 100, style, color=color, label=label,
            lw=2 if style == "-" else 1.6)

for x, text in [(1971, "КНР получает\nместо Китая"), (1991, "распад\nСССР")]:
    ax.axvline(x, color="grey", lw=0.8, ls="--")
    ax.text(x + 0.5, 3, text, fontsize=8, color="grey", va="bottom")

ax.set_xlim(1946, LAST_FULL_YEAR)
ax.set_ylim(0, 100)
ax.set_ylabel("Голосов «за», % от поданных")
ax.set_title("Доля голосов «за» в Генеральной Ассамблее ООН, 1946–2023\n"
             "(только голосования по резолюциям целиком)")
ax.grid(alpha=0.3)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=3, fontsize=9, frameon=False)
fig.text(0.01, 0.01, "Данные: Voeten, UNGA Voting Data (Harvard Dataverse, v33). "
         "Доля = за / (за + воздержался + против). В 1951 году было лишь 6–7 голосований, "
         "поэтому скачок в этом году ненадёжен.", fontsize=7, color="grey")
fig.tight_layout(rect=(0, 0.03, 1, 1))
OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT_PNG, dpi=150)
print(f"Сохранено: {OUT_PNG.relative_to(ROOT)} и {OUT_CSV.relative_to(ROOT)}")
