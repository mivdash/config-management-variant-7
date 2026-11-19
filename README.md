# Конфигурационное управление · Вариант 7

CLI читает конфигурационный файл в UTF-8, разбирает его с помощью Lark,
выводит TOML в стандартный вывод.

## Установка и запуск

Требуется Python 3.11 или новее. Компиляция не требуется.

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\run.bat --input examples/server.cfg
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Linux/macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
./run.sh --input examples/server.cfg
.venv/bin/python -m unittest discover -s tests -v
```

| Ключ | Назначение |
| --- | --- |
| `-i PATH`, `--input PATH` | Обязательный путь к входному файлу UTF-8 |
| `-h`, `--help` | Справка CLI |

При успехе код завершения равен 0. Ошибки чтения или трансляции
выводятся в stderr с кодом 1. Ошибки аргументов CLI дают код 2.

## Этап 3

Добавлены объявления констант.

## Документирование кода

Назначение модулей, классов и функций описано строками документации
Python (docstring). Для содержания использована рекомендация
[ГОСТ 19.401-78](https://protect.gost.ru/gost/details/e71e0951-ee1a-441f-b0c0-be3f3681c2f0)
описывать функциональное назначение частей программы.
