"""Преобразование учебного конфигурационного языка в TOML."""

import json
from pathlib import Path

from lark import Lark, Token, Tree, UnexpectedInput
from lark.visitors import Interpreter

GRAMMAR = Path(__file__).with_name("config.lark")
PARSER = Lark.open(
    GRAMMAR, parser="lalr", propagate_positions=True,
    maybe_placeholders=False,
)


class ConfigError(ValueError):
    """Ошибка синтаксиса или вычисления в исходном файле."""


def location(item):
    """Возвращает позицию токена или узла."""
    position = item if isinstance(item, Token) else item.meta
    return f"{position.line}:{position.column}"


class Evaluator(Interpreter):
    """Вычисляет дерево разбора в порядке исходных объявлений."""

    def __init__(self):
        """Создаёт состояние для одного входного файла."""
        super().__init__()
        self.values = []

    def start(self, tree):
        """Обрабатывает значения и формирует TOML."""
        self.visit_children(tree)
        result = {}
        if self.values:
            values = ", ".join(map(encode_toml, self.values))
            result["_values"] = f"[{values}]"
        return "".join(f"{k} = {v}\n" for k, v in result.items())

    def standalone(self, tree):
        """Сохраняет отдельное значение верхнего уровня."""
        self.values.append(self.visit(tree.children[0]))

    def integer(self, tree):
        """Преобразует токен целого числа."""
        return int(tree.children[0])

    def string(self, tree):
        """Декодирует строковый литерал."""
        value = json.loads(tree.children[0][1:])
        if any("\ud800" <= char <= "\udfff" for char in value):
            raise ConfigError(f"{location(tree)}: недопустимый символ Unicode")
        return value


def encode_toml(value):
    """Кодирует целое, вещественное число, строку или массив TOML."""
    if isinstance(value, str):
        encoded = json.dumps(value, ensure_ascii=False)
        return encoded.replace("\x7f", r"\u007F")
    return str(value)


def convert(source):
    """Разбирает исходный текст и возвращает готовый TOML."""
    try:
        tree = PARSER.parse(source)
    except UnexpectedInput as error:
        context = error.get_context(source).rstrip()
        position = f"{error.line}:{error.column}"
        message = f"{position}: синтаксическая ошибка\n{context}"
        raise ConfigError(message) from error
    return Evaluator().visit(tree)
