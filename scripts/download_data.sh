#!/usr/bin/env bash
# Скачивает все файлы текущей версии датасета Voeten
# "United Nations General Assembly Ideal Points" (Harvard Dataverse,
# doi:10.7910/DVN/LEJUQZ) в папку data/raw/.
# Запуск из корня проекта:  bash scripts/download_data.sh
set -euo pipefail

DOI="doi:10.7910/DVN/LEJUQZ"
API="https://dataverse.harvard.edu/api"
OUT="data/raw"
mkdir -p "$OUT"

# Получаем список файлов (id и имя) последней опубликованной версии
curl -sSf "$API/datasets/:persistentId/versions/:latest-published/files?persistentId=$DOI" |
python3 -c '
import json, sys
for f in json.load(sys.stdin)["data"]:
    df = f["dataFile"]
    print(df["id"], df["filename"], sep="\t")
' | while IFS=$'\t' read -r id name; do
  if [[ -s "$OUT/$name" ]]; then
    echo "уже есть: $name"
  else
    echo "скачиваю: $name"
    curl -sSfL "$API/access/datafile/$id" -o "$OUT/$name"
  fi
done
echo "Готово. Файлы лежат в $OUT/"

# --- Сырые голоса из старой версии 33 (июнь 2024, сессии 1–78) ---
# В текущей версии их нет, поэтому берём по id файла из версии 33.
OLD="$OUT/v33"
mkdir -p "$OLD"
for pair in "10295576 UNVotes-1.RData" "10295577 Codebook-1.docx"; do
  id=${pair%% *}; name=${pair#* }
  if [[ -s "$OLD/$name" ]]; then echo "уже есть: v33/$name"
  else echo "скачиваю: v33/$name"; curl -sSfL "$API/access/datafile/$id" -o "$OLD/$name"; fi
done
