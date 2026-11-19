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
        self.constants = {}
        self.values = []

    def start(self, tree):
        """Обрабатывает объявления и формирует TOML."""
        self.visit_children(tree)
        result = dict(self.constants)
        if self.values:
            result["_values"] = self.values
        return "".join(f"{k} = {encode_toml(v)}\n" for k, v in result.items())

    def declaration(self, tree):
        """Вычисляет и сохраняет объявление константы."""
        name_node, value = tree.children
        name = self.visit(name_node)
        if name in self.constants:
            raise ConfigError(f"{location(tree)}: повторное объявление {name}")
        self.constants[name] = self.visit(value)

    def standalone(self, tree):
        """Сохраняет отдельное значение верхнего уровня."""
        self.values.append(self.visit(tree.children[0]))

    def name(self, tree):
        """Возвращает идентификатор как строку."""
        return str(tree.children[0])

    def integer(self, tree):
        """Преобразует токен целого числа."""
        return int(tree.children[0])

    def string(self, tree):
        """Декодирует строковый литерал."""
        value = json.loads(tree.children[0][1:])
        if any("\ud800" <= char <= "\udfff" for char in value):
            raise ConfigError(f"{location(tree)}: недопустимый символ Unicode")
        return value

    def array(self, tree):
        """Вычисляет элементы массива."""
        return [self.visit(value) for value in tree.children[1:]]


def encode_toml(value):
    """Кодирует целое, вещественное число, строку или массив TOML."""
    if isinstance(value, list):
        return "[" + ", ".join(map(encode_toml, value)) + "]"
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
