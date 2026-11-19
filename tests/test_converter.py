"""Тесты грамматики, вычисления, сериализации и интерфейса CLI."""

import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from converter import ConfigError, convert


class ConverterTests(unittest.TestCase):
    """Проверки исходных конструкций и ошибок трансляции."""

    def test_comments_and_empty_input(self):
        """Проверяет комментарии и пустой файл."""
        self.assertEqual(convert("* комментарий\n\n"), "")
        self.assertEqual(tomllib.loads(convert("a := 1 * хвост")), {"a": 1})

    def test_integers_and_strings(self):
        """Проверяет знаки и экранирование строк."""
        source = r'text := @"Привет * \"мир\"\n" nums := list(+7,-3,-0,0)'
        result = tomllib.loads(convert(source))
        self.assertEqual(result, {"text": 'Привет * "мир"\n',
                                  "nums": [7, -3, 0, 0]})
        self.assertEqual(tomllib.loads(convert(r'@"\u007f"'))["_values"],
                         [chr(127)])

    def test_nested_arrays_and_empty_array(self):
        """Проверяет пустые и вложенные массивы."""
        source = 'items := list(list(), list(@"x", list(-1)), 0)'
        result = tomllib.loads(convert(source))
        self.assertEqual(result, {"items": [[], ["x", [-1]], 0]})

    def test_declarations(self):
        """Проверяет ключи TOML и повторное объявление."""
        output = tomllib.loads(convert("port := 8080"))
        self.assertEqual(output, {"port": 8080})
        with self.assertRaisesRegex(ConfigError, "повторное объявление"):
            convert("port := 8080 port := 80")

    def test_syntax_errors(self):
        """Проверяет позицию синтаксической ошибки."""
        cases = ("A := 1", "a1 := 1", "a := 01", "a := +01",
                 "a := 1b := 2", "list(1,)", "list(1 2)",
                 '.{+ 1}.', ".{sqrt()}.", ".{* 2 3}.", '@"без кавычки',
                 ".{+ 1 2}", "a : 1")
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaisesRegex(ConfigError, r"1:\d+: синтакс"):
                    convert(source)


class CliTests(unittest.TestCase):
    """Проверки выполнения CLI в отдельном процессе."""

    def invoke(self, path):
        """Запускает CLI с исследуемым путём."""
        return subprocess.run(
            [sys.executable, str(ROOT / "src" / "main.py"), "-i", str(path)],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )

    def test_cli_error(self):
        """Проверяет код возврата и потоки при ошибке."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.cfg"
            path.write_text("a := 01", encoding="utf-8")
            process = self.invoke(path)
            self.assertEqual(process.returncode, 1)
            self.assertEqual(process.stdout, "")
            self.assertIn("синтаксическая ошибка", process.stderr)

    def test_missing_file(self):
        """Проверяет диагностику отсутствующего файла."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "absent.cfg"
            process = self.invoke(path)
            self.assertEqual(process.returncode, 1)
            self.assertEqual(process.stdout, "")
            self.assertIn(path.name, process.stderr)
