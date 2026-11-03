# 2 тапсырма Жобаның өзгерістер журналы

Python 3.11 немесе 3.12 қажет. Барлық дерек жергілікті сақталады.
Оқу жобасы ISO/IEC/IEEE 828 стандартын толық сәйкестікке сертификаттамайды.

## Орнату және тексеру
```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pip install -e . --no-build-isolation
.\.venv\Scripts\python -m pytest -v
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m application --help
```

## Консоль
`python -m application --store ЖОЛ ACTION key=value`
`--store` — дерекқор файлы не қолданба каталогы; әдепкісі `.data/store.db`.
Сандар мен `true`, `false`, `null`, JSON массивтері автоматты танылады.
Бос орындары бар мәнді PowerShell-де бір тырнақшаға алыңыз: `'name=Менің жобам'`.
Күрделі мәтін үшін UTF-8 JSON файл жасап, `ACTION --input request.json` қолданыңыз.
Қолданылатын әрекеттер:

- `add`
- `list`
- `transition`
- `history`
- `report`

Параметрлердің нақты қолтаңбалары `API.md` файлында жазылған.
Демонстрация қорытындылары `evidence/demo.json`, тексерулер `evidence/pytest.txt` ішінде.
Функциялар, тесттер және ережелер `SCMP.md` құжатымен байланыстырылған.
SQLite жазбаларын қолданбадан тыс тікелей өңдеу бақылау тәртібіне кірмейді.

## Git дәлелдері
```powershell
git log --all --graph --oneline
git branch -a
git tag -n
```

GitHub Actions іске қосылуларының тек шынайы URL-дері жалпы есепте беріледі.
Жергілікті журналды GitHub CI іске қосылуы деп санауға болмайды.
