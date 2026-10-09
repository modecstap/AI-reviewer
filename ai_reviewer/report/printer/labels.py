import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class ReportLabels:
    """Fixed labels of the printed report in one language."""

    language: str
    created: str
    total_claims: str
    claims_by_property: str
    chapter: str
    paragraph: str
    problem: str
    types: str
    quote: str
    corrections: str
    months: tuple[str, ...]
    date_pattern: str

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
    claims_by_property="Претензии по свойствам",
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
)

ENGLISH_LABELS = ReportLabels(
    language="en",
    created="Created",
    total_claims="Total claims",
    claims_by_property="Claims by property",
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
