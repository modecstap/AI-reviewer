import datetime
from dataclasses import dataclass, field

from .entities import ClaimType


@dataclass(frozen=True)
class ReportLabels:
    """Fixed labels of the printed report in one language."""

    language: str
    created: str
    total_claims: str
    chapter: str
    paragraph: str
    problem: str
    types: str
    quote: str
    corrections: str
    months: tuple[str, ...]
    date_pattern: str
    property_names: dict[str, str] = field(default_factory=dict)
    type_names: dict[str, dict[str, str]] = field(default_factory=dict)

    def property_name(self, name: str) -> str:
        """
        Translate a property name.

        :param name: property name as in ``report.json``

        :return: the translated name, or ``name`` without a translation
        """
        return self.property_names.get(name, name)

    def type_name(
        self, property_name: str, claim_type: ClaimType
    ) -> str | None:
        """
        Translate the name of a claim type by its number.

        :param property_name: property name as in ``report.json``
        :param claim_type: claim type to translate

        :return: the translated name, or the original name without a
            translation
        """
        names = self.type_names.get(property_name, {})
        if claim_type.number is None:
            return claim_type.name
        return names.get(claim_type.number, claim_type.name)

    def date(self, day: datetime.date) -> str:
        """
        Format a date in this language.

        :param day: date to format

        :return: the date by ``date_pattern``
        """
        return self.date_pattern.format(
            day=day.day,
            month=day.month,
            month_name=self.months[day.month - 1],
            year=day.year,
        )


RUSSIAN_LABELS = ReportLabels(
    language="ru",
    created="Дата создания",
    total_claims="Всего претензий",
    chapter="Глава",
    paragraph="Параграф",
    problem="Проблема",
    types="Типы",
    quote="Цитата",
    corrections="Корректировки",
    months=(
        "января",
        "февраля",
        "марта",
        "апреля",
        "мая",
        "июня",
        "июля",
        "августа",
        "сентября",
        "октября",
        "ноября",
        "декабря",
    ),
    date_pattern="{day:02}.{month:02}.{year}",
    property_names={
        "Caution": "Осторожность выводов",
        "Conciseness": "Лаконичность",
        "Consistency": "Логическая связность",
        "Correctness": "Терминологическая точность",
        "Impersonality": "Безличность изложения",
        "Literacy": "Грамотность",
        "Objectivity": "Объективность",
        "Structure": "Структура",
    },
    type_names={
        "Caution": {
            "1": "Гипотеза подана как установленный факт",
            "2": "Вывод шире данных",
            "3": "Пилотное исследование подано как доказательство",
            "4": "Единственное объяснение там, где возможны несколько",
            "5": "Рекомендация сильнее результата",
            "6": "Факт, интерпретация и гипотеза в одной нечёткой цепочке",
            "7": "Квантор всеобщности в выводе",
            "8": "Аннотация усиливает вывод",
        },
        "Conciseness": {
            "1": "Пустой зачин",
            "2": "Канцелярская цепочка",
            "3": "Риторический вопрос",
            "4": "Троекратный пересказ одного результата",
            "5": "Абзац повторён другими словами",
            "6": "Пустое усиление",
            "7": "Избыточное определение известного шага",
            "8": "Сокращение, уничтожающее информацию",
        },
        "Consistency": {
            "1": "Вывод раньше постановки задачи",
            "2": "Логический скачок между утверждениями",
            "3": "Обзор литературы не служит задаче",
            "4": "Результаты отвечают на другой вопрос",
            "5": "Противоречие между разделами",
            "6": "Порочный круг в рассуждении",
            "7": "Новое утверждение только в выводах",
            "8": "Нарушен порядок обоснования",
        },
        "Correctness": {
            "1": "Бытовое слово вместо термина",
            "2": "Избыточное нагромождение терминов",
            "3": "Подмена близким термином",
            "4": "Термины из другой аналитической операции",
            "5": "Многозначный термин без закреплённого значения",
            "6": "Термин меняет значение",
            "7": "Разные названия одного объекта",
            "8": "Неточная калька понятия",
            "9": "Узкий термин без нужного пояснения",
            "10": "Оценка без меры или критерия",
            "11": "«Значительно» без сравнения",
            "12": "Не указаны границы применимости",
            "13": "«Очевидно» вместо обоснования",
            "14": "Неясная отсылка",
        },
        "Impersonality": {
            "1": "Личное убеждение вместо результата",
            "2": "Разговорная оценка",
            "3": "«Мы» как носитель мнения",
            "4": "Допустимое и избыточное «мы» в одном фрагменте",
            "5": "Эмоциональная полемика",
            "6": "Риторическое обращение",
            "7": "Разговорный рассказ о ходе работы",
            "8": "Самопрезентация вместо описания вклада",
        },
        "Literacy": {
            "1": "Нарушение согласования",
            "2": "Нарушение управления",
            "3": "Нарушение лексической сочетаемости",
            "4": "Пароним меняет действие",
            "5": "Деепричастный оборот с несовпадающим субъектом",
            "6": "Нарушен ряд однородных членов",
            "7": "Пунктуация смещает границу мысли",
            "8": "Неоправданно перегруженное предложение",
        },
        "Objectivity": {
            "1": "Эмоционально окрашенная оценка",
            "2": "Категоричное утверждение без достаточных оснований",
            "3": "Личное мнение вместо научного вывода",
            "4": "Преувеличение значимости результатов",
            "5": "Оценочные характеристики вместо аргументации",
            "6": "Категоричное отрицание альтернативных подходов",
            "7": "Корреляция истолкована как причинность",
            "8": "Допущение подано как установленный факт",
        },
        "Structure": {
            "1": "Нет проверяемой задачи",
            "2": "Готовый результат во введении",
            "3": "Метод после интерпретации",
            "4": "Чужая и собственная работа не разделены",
            "5": "Результаты не связаны с задачей",
            "6": "Обсуждение лишь повторяет результаты",
            "7": "В выводах появляется новый материал",
            "8": "Пункт вывода не закрывает задачу",
        },
    },
)

ENGLISH_LABELS = ReportLabels(
    language="en",
    created="Created",
    total_claims="Total claims",
    chapter="Chapter",
    paragraph="Paragraph",
    problem="Problem",
    types="Types",
    quote="Quote",
    corrections="Corrections",
    months=(
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ),
    date_pattern="{month_name} {day}, {year}",
)
