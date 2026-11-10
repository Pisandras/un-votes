"""Собирает отчёт report/index.html из готовых графиков и таблиц.

Запуск из корня проекта (после plot_yes_share.py, topic_comparison.py и
sample_votes_for_check.py):  python3 scripts/build_report.py
Картинки встраиваются прямо в HTML, поэтому файл можно открыть или отправить отдельно.
"""
import base64
import html
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "report" / "index.html"


def img(name, alt):
    data = base64.b64encode((FIG / name).read_bytes()).decode()
    return f'<figure><img src="data:image/png;base64,{data}" alt="{html.escape(alt)}"></figure>'


def un_res_symbol(unres):
    """R/35/75 -> A/RES/35/75 (номер в UN Digital Library)."""
    parts = unres.split("/")
    return f"A/RES/{parts[1]}/{parts[2]}" if len(parts) == 3 else unres


# --- Таблица голосований для проверки ---
checks = pd.read_csv(PROC / "random_votes_to_check.csv")
countries = ["США", "Франция", "СССР/Россия", "Китай (КНР)"]
check_rows = []
for _, r in checks.iterrows():
    sym = un_res_symbol(r["resolution"])
    url = f"https://digitallibrary.un.org/search?ln=en&p={sym.replace('/', '%2F')}"
    cells = "".join(f'<td class="vote v-{html.escape(r[c])}">{html.escape(r[c])}</td>' for c in countries)
    short = html.escape(str(r["short"]).capitalize())
    check_rows.append(
        f'<tr><td><a href="{url}" target="_blank" rel="noopener">{sym}</a><div class="desc">{short}</div></td>'
        f'<td class="nowrap">{r["date"]}</td>{cells}<td class="num">{r["итог (за–против–возд.)"]}</td></tr>')

# --- Таблица долей «за» по периодам (из yes_share_by_year.csv) ---
ys = pd.read_csv(PROC / "yes_share_by_year.csv")
ys["country"] = ys["country"].replace({"Китай (КНР)": "Китай", "Китай (Китайская Республика, до 1971)": "Китай*"})
bins = [1945, 1959, 1970, 1991, 2023]
labels = ["1946–1959", "1960–1970", "1971–1991", "1992–2023"]
ys["period"] = pd.cut(ys["year"], bins, labels=labels)
piv = (ys.pivot_table(index="period", columns="country", values="yes_share", observed=True) * 100).round(0)
order = ["США", "Франция", "СССР / Россия", "Китай*", "Китай"]
piv = piv[[c for c in order if c in piv.columns]]
head = "".join(f"<th>{c}</th>" for c in piv.columns)
body = "".join(
    "<tr><th>{}</th>{}</tr>".format(p, "".join(
        f'<td class="num">{"" if pd.isna(v) else int(v)}</td>' for v in row))
    for p, row in piv.iterrows())
period_table = f'<table><thead><tr><th>Период</th>{head}</tr></thead><tbody>{body}</tbody></table>'

page = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Голосования в ГА ООН</title>
<style>
:root {{
  --bg: #fbfaf7; --fg: #1d1d1f; --muted: #5f6368; --line: #e3e1db; --card: #ffffff;
  --accent: #1f5fbf; --note-bg: #f3efe4; --yes: #2e7d32; --no: #c62828; --abst: #8d6e00;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #17181a; --fg: #ececec; --muted: #a5a8ad; --line: #34363a; --card: #202225;
    --accent: #7aa7f0; --note-bg: #2a2820; --yes: #7bc47f; --no: #ef7b7b; --abst: #d9b84a;
  }}
}}
:root[data-theme="dark"] {{
  --bg: #17181a; --fg: #ececec; --muted: #a5a8ad; --line: #34363a; --card: #202225;
  --accent: #7aa7f0; --note-bg: #2a2820; --yes: #7bc47f; --no: #ef7b7b; --abst: #d9b84a;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--fg);
  font: 17px/1.6 Georgia, "Times New Roman", serif; }}
main {{ max-width: 860px; margin: 0 auto; padding: 40px 16px 80px; }}
h1, h2, h3, th, .meta, table, nav {{ font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
h1 {{ font-size: 2rem; line-height: 1.2; margin: 0 0 8px; }}
h2 {{ font-size: 1.35rem; margin: 48px 0 12px; padding-top: 12px; border-top: 1px solid var(--line); }}
h3 {{ font-size: 1.05rem; margin: 24px 0 8px; }}
.meta {{ color: var(--muted); font-size: .9rem; margin-bottom: 24px; }}
a {{ color: var(--accent); }}
.question {{ background: var(--note-bg); border-left: 4px solid var(--accent); padding: 14px 18px;
  font-size: 1.1rem; border-radius: 4px; }}
nav {{ font-size: .9rem; display: flex; flex-wrap: wrap; gap: 6px 16px; margin: 20px 0; }}
figure {{ margin: 20px 0; background: #fff; border: 1px solid var(--line); border-radius: 6px; padding: 8px; }}
figure img {{ width: 100%; height: auto; display: block; }}
.table-wrap {{ overflow-x: auto; margin: 16px 0; }}
table {{ border-collapse: collapse; font-size: .88rem; width: 100%; }}
th, td {{ border-bottom: 1px solid var(--line); padding: 6px 10px; text-align: left; vertical-align: top; }}
thead th {{ border-bottom: 2px solid var(--fg); }}
td.num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
td.vote {{ white-space: nowrap; font-weight: 600; }}
.v-за {{ color: var(--yes); }} .v-против {{ color: var(--no); }} .v-воздержался {{ color: var(--abst); }}
.small {{ font-size: .88rem; color: var(--muted); }}
.desc {{ font-size: .8rem; color: var(--muted); margin-top: 2px; }}
.nowrap {{ white-space: nowrap; }}
.scroll-hint {{ display: none; }}
@media (max-width: 700px) {{ .scroll-hint {{ display: block; }} }}
ul.findings li {{ margin-bottom: 8px; }}
dt {{ font-weight: bold; margin-top: 10px; }}
dd {{ margin-left: 0; }}
</style>
</head>
<body>
<main>
<h1>Как голосуют США, Франция, Россия и Китай в Генеральной Ассамблее ООН</h1>
<p class="meta">Учебный проект по международным отношениям · данные 1946–2023</p>

<p class="question"><b>Вопрос.</b> Как менялась готовность четырёх постоянных членов Совета Безопасности
голосовать «за» резолюции Генеральной Ассамблеи, и по каким темам они сближаются или расходятся сильнее всего?</p>

<nav>
<a href="#data">Данные</a><a href="#trend">Доля «за» по годам</a><a href="#topics">По темам</a>
<a href="#check">Проверка</a><a href="#conclusions">Выводы</a><a href="#limits">Ограничения</a><a href="#sources">Источники</a>
</nav>

<h2 id="data">1. Данные и методика</h2>
<p><b>Источник:</b> Erik Voeten, «United Nations General Assembly Voting Data», Harvard Dataverse
(<a href="https://doi.org/10.7910/DVN/LEJUQZ">doi:10.7910/DVN/LEJUQZ</a>). В текущей версии датасета
(v39) остались только расчётные показатели, поэтому голоса взяты из файла <code>UNVotes-1.RData</code>
версии 33 (июнь 2024): 1,28 млн строк, «страна × голосование», сессии 1–78.</p>
<dl>
<dt>Какие голосования</dt>
<dd>Только голосования по резолюциям целиком, без отдельных абзацев и поправок: те попадали в данные
в разные десятилетия очень неравномерно и исказили бы сравнение во времени.</dd>
<dt>Доля «за»</dt>
<dd>«За» ÷ («за» + «воздержался» + «против»). Отсутствие на голосовании не учитывается.</dd>
<dt>Индекс совпадения пары стран</dt>
<dd>По каждому голосованию, где обе страны проголосовали: 1 — одинаково, 0,5 — одна воздержалась,
0 — одна «за», другая «против»; затем среднее (как agreement score у Лейпхарта).</dd>
<dt>Год</dt>
<dd>Из даты голосования (в колонке <code>year</code> есть ошибки). 2024 год не включён — есть только до июня.</dd>
<dt>Страны</dt>
<dd>СССР и Россия в данных — один код. Место Китая до 1971 года занимала Китайская Республика (Тайвань),
с 1971 года — КНР.</dd>
<dt>Темы</dt>
<dd>Отметки автора датасета, сделанные поиском по описаниям: Палестина и Ближний Восток, ядерное оружие,
разоружение, колониализм, права человека, экономическое развитие. Около 30% голосований без темы,
у 25% — несколько тем.</dd>
</dl>
<p class="small">Как читать: почти все резолюции ГА принимаются, поэтому высокая доля «за» в основном значит,
что страна голосует вместе с большинством ООН, а низкая — что она часто в меньшинстве.</p>

<h2 id="trend">2. Доля голосов «за» по годам</h2>
{img("yes_share_by_year.png", "Линейный график доли голосов «за» по годам для четырёх стран")}
<div class="table-wrap">{period_table}</div>
<p class="small">Средняя по годам доля «за», %. Китай* — Китайская Республика (до 1971).</p>
<ul class="findings">
<li><b>1946–1950-е:</b> в ООН мало стран, большинство ближе к Западу; США чаще всех голосуют «за»,
СССР — реже всех. Резкие скачки — из-за малого числа голосований (в 1951 году их всего 6–7).</li>
<li><b>1960-е:</b> с деколонизацией в ООН входят десятки новых государств, большинство меняется:
доля «за» у СССР растёт, у США и Франции падает.</li>
<li><b>1971–1991:</b> самый большой разрыв. КНР и СССР голосуют «за» в 80–98% случаев, США к концу
1980-х — примерно в 10%.</li>
<li><b>1991:</b> самый резкий излом — доля «за» у России падает с ~95% до ~45%, у Франции и США растёт.</li>
<li><b>1992–2023:</b> устойчивый порядок Китай &gt; Россия &gt; Франция &gt; США; США остаются в меньшинстве
чаще всех, хотя в 2021–2023 годах их доля «за» выросла до ~33%.</li>
</ul>

<h2 id="topics">3. Сравнение по темам</h2>
<h3>Доля «за» по темам</h3>
{img("topic_yes_share.png", "Столбиковая диаграмма доли «за» по темам, 1971–1991 и 1992–2023")}
<h3>Насколько одинаково голосуют пары стран</h3>
{img("topic_agreement.png", "Тепловая карта индекса совпадения шести пар стран по темам")}

<h3>Где сближаются</h3>
<ul class="findings">
<li><b>Россия и Китай</b> — самая согласованная пара в обоих периодах (индекс 84 и 83 из 100). В холодную войну
почти полное совпадение по колониализму (97), Ближнему Востоку (96) и правам человека (92).</li>
<li><b>США и Франция</b> сильнее всего совпадают по ядерному оружию (83 → 86) и разоружению (80 и 80).</li>
<li><b>Ядерное оружие после 1991 года:</b> Россия стала голосовать почти как западные ядерные державы —
её доля «за» упала с 78% до 30%, совпадение с Францией выросло с 41 до 80, с США — с 35 до 67.
Китай остался ближе к большинству (69% «за»). Похоже, по этой теме страны делятся скорее на
«ядерные — неядерные», чем на «Запад — не Запад», но это предположение надо проверять на текстах резолюций.</li>
<li><b>Франция и Россия</b> после 1991 года заметно сблизились почти по всем темам (в среднем 53 → 70).</li>
</ul>

<h3>Где расходятся сильнее всего</h3>
<ul class="findings">
<li><b>Палестина и Ближний Восток</b> — самая острая тема. После 1991 года США голосуют «за» лишь в 3% случаев,
а Китай — в 100%. Индекс США–Китай — 8, США–Россия — 21. Франция здесь ушла от США (совпадение 53 → 20)
и голосует почти как Россия (94) и Китай (88).</li>
<li><b>Права человека:</b> США–Китай — 11, второе самое низкое значение во всей таблице; Франция–Китай — 42.</li>
<li><b>Колониализм и развитие:</b> США в меньшинстве (10% и 21% «за»), совпадение с Китаем — 17 и 18.</li>
<li>В целом пара <b>США–Китай</b> разошлась сильнее, чем в холодную войну: 34 → 24.</li>
</ul>

<h2 id="check">4. Ручная проверка: пять случайных голосований</h2>
<p>Пять голосований выбраны случайно (seed 2026) из тех же данных, что и графики. Номер резолюции — ссылка
на поиск в <a href="https://digitallibrary.un.org">UN Digital Library</a>: там у резолюции есть запись
голосования (Voting Data) с голосами каждой страны. Сверьте голоса, итоговый счёт и дату.</p>
<p class="small scroll-hint">Таблица шире экрана — её можно прокрутить вбок.</p>
<div class="table-wrap"><table>
<thead><tr><th>Резолюция</th><th>Дата в данных</th>
<th>США</th><th>Франция</th><th>СССР/ Россия</th><th>Китай</th><th>Итог: за–против–возд.</th></tr></thead>
<tbody>{''.join(check_rows)}</tbody></table></div>
<p class="small">Буквы в конце номера (например, 37/99<b>J</b>) — часть резолюции из серии; в библиотеке ищите полный номер.
Четыре из пяти дат в данных приходятся на воскресенье — см. ограничения.</p>

<h2 id="conclusions">5. Выводы</h2>
<ol>
<li>Из четырёх стран США чаще всего оказываются в меньшинстве ГА: примерно 22% голосов «за» и в холодную войну,
и после неё. Китай, наоборот, почти всегда с большинством.</li>
<li>Россия и Китай голосуют наиболее согласованно на протяжении всех 50 лет.</li>
<li>Конец холодной войны сильнее всего изменил голосование России: она стала реже голосовать «за»
и сблизилась с Францией, а по ядерным вопросам — с западными ядерными державами.</li>
<li>Франция после 1991 года — «посередине»: с США по ядерному оружию и разоружению, с Россией и Китаем —
по Ближнему Востоку.</li>
<li>Главная линия раскола — Палестина и Ближний Восток, где США почти в одиночестве; затем права человека
(США против Китая).</li>
</ol>

<h2 id="limits">6. Ограничения метода</h2>
<ul>
<li><b>Это описание, а не объяснение.</b> Графики показывают, как голосовали страны, но не почему.
Объяснения в тексте — гипотезы.</li>
<li><b>Доля «за» зависит от повестки:</b> какие резолюции выносят на голосование, решает большинство ГА.
Рост доли «за» может означать как изменение позиции страны, так и изменение повестки.</li>
<li><b>Только поимённые голосования.</b> Резолюции, принятые без голосования (консенсусом), — а это
большинство резолюций ГА — в данные не входят. В 1985–1996 годах удалены и единогласные голосования.</li>
<li><b>Данные заканчиваются 2023 годом</b> (версия 33). Новые голосования — в базе UNGA-DM (unvotes.unige.ch).</li>
<li><b>Темы определены автоматически</b> поиском по описаниям и, по словам автора, могут быть неточны.</li>
<li><b>Даты до 2000 года неточны:</b> 25–35% из них выпадают на выходные. На годовые доли это почти не влияет.</li>
<li><b>Номера резолюций до 1985 года</b> в данных не всегда совпадают с настоящими (замечание автора датасета).</li>
<li><b>Голоса «за» неравноценны:</b> важная резолюция и процедурная весят одинаково.</li>
<li><b>В отдельные годы мало голосований</b> (особенно в 1940–1950-х), поэтому годовые значения скачут.</li>
</ul>

<h2 id="sources">7. Источники</h2>
<ul class="small">
<li>Voeten, E. United Nations General Assembly Voting Data. Harvard Dataverse, doi:10.7910/DVN/LEJUQZ (v33, 2024).</li>
<li>Bailey, M. A., Strezhnev, A., Voeten, E. (2017). Estimating dynamic state preferences from United Nations
voting data. <i>Journal of Conflict Resolution</i>, 61(2), 430–456.</li>
<li>Lijphart, A. (1963). The analysis of bloc voting in the General Assembly. <i>American Political Science Review</i>, 57(4), 902–917.</li>
<li>Код и данные проекта: <a href="https://github.com/Pisandras/un-votes">github.com/Pisandras/un-votes</a>.</li>
</ul>
</main>
</body>
</html>
"""
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page, encoding="utf-8")
print(f"Готово: {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} КБ)")
