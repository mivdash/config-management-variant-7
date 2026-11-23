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

    def test_nested_expressions_and_constants(self):
        """Проверяет порядок вычисления."""
        source = """
        base := 16
        a := .{+ .{sqrt(base)}. .{- 7 2}.}.
        b := list(.{sqrt 2}., list(.{- a -1}.))
        """
        result = tomllib.loads(convert(source))
        self.assertEqual(result["a"], 9.0)
        self.assertAlmostEqual(result["b"][0], 2 ** 0.5)
        self.assertEqual(result["b"][1], [10.0])

    def test_standalone_values_and_keyword_names(self):
        """Проверяет имена и вывод значений."""
        source = 'sqrt := 16 list := .{+ sqrt 1}. .{- list 2}. @"да"'
        result = tomllib.loads(convert(source))
        self.assertEqual(result, {"sqrt": 16, "list": 17,
                                  "_values": [15, "да"]})

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

    def test_evaluation_errors(self):
        """Проверяет диагностику вычислений."""
        cases = ("a := .{+ b 1}. b := 2", "a := 1 a := 2",
                 ".{sqrt(-1)}.", '.{+ @"x" 1}.', ".{- list(1) 1}.",
                 r'@"\ud800"')
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaisesRegex(ConfigError, r"1:\d+:"):
                    convert(source)


class CliTests(unittest.TestCase):
    """Проверки выполнения CLI в отдельном процессе."""

    def invoke(self, path):
        """Запускает CLI с исследуемым путём."""
        return subprocess.run(
            [sys.executable, str(ROOT / "src" / "main.py"), "-i", str(path)],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )

    def test_examples(self):
        """Проверяет вывод TOML для трёх примеров."""
        cases = (("server", "connections", 150),
                 ("warehouse", "available", 85),
                 ("geometry", "side", 50 ** 0.5))
        for name, key, expected in cases:
            with self.subTest(name=name):
                process = self.invoke(ROOT / "examples" / f"{name}.cfg")
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assertEqual(process.stderr, "")
                self.assertEqual(tomllib.loads(process.stdout)[key], expected)

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
