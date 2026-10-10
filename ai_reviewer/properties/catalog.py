import json
import re
from pathlib import Path

from .definition import AgentDefinition
from .errors import PropertyCatalogError
from .names import PropertyNames

IO_STRUCTURE_FILE = "IO-structure.md"
INSTRUCTION_FILE = "instruction.md"
REFERENCE_FILE = "reference.md"
TRANSLATION_DIR = "translation"
VIOLATION_TYPES_HEADING = "## Violation types"
TYPE_HEADING = re.compile(r"^### (\d+)\. ")

type Translations = tuple[dict[str, str], dict[str, dict[str, str]]]


class PropertyCatalog:
    """
    Reads the property catalog: one subdirectory per property with its
    ``instruction.md`` and ``reference.md``, the shared ``IO-structure.md``
    and translations ``translation/<language>.json``.
    """

    def __init__(self, root: Path):
        """
        :param root: catalog directory
        """
        self._root = root

    def agents(self) -> tuple[AgentDefinition, ...]:
        """
        Collect the agent definitions of all properties.

        :raises PropertyCatalogError: when the catalog directory cannot be
            listed

        :return: definitions sorted by property id
        """
        try:
            directories = [path for path in self._root.iterdir() if path.is_dir()]
        except OSError as error:
            raise PropertyCatalogError(
                f"cannot read {self._root}: {error}"
            ) from error
        return tuple(
            AgentDefinition(
                id=directory.name,
                io_structure=self._root / IO_STRUCTURE_FILE,
                instruction=directory / INSTRUCTION_FILE,
                reference=directory / REFERENCE_FILE,
            )
            for directory in sorted(directories, key=lambda path: path.name)
            if self._is_property(directory)
        )

    def names(self, language: str) -> PropertyNames:
        """
        Collect the property and claim type names in one language.

        A missing translation file means no translations.

        :param language: language code, the translation file name

        :raises PropertyCatalogError: when the catalog, a ``reference.md`` or
            the translation file cannot be read, or the translation file has
            an unexpected shape

        :return: type numbers of every property and the translations
        """
        numbers = {
            agent.id: self._type_numbers(agent.reference)
            for agent in self.agents()
        }
        path = self._root / TRANSLATION_DIR / f"{language}.json"
        properties, types = self._translations(path) if path.exists() else ({}, {})
        return PropertyNames(numbers, properties, types)

    @staticmethod
    def _is_property(directory: Path) -> bool:
        """
        Tell whether a catalog subdirectory is a property.

        :param directory: catalog subdirectory

        :return: True when it holds ``instruction.md`` and ``reference.md``
        """
        if directory.name == TRANSLATION_DIR:
            return False
        return (directory / INSTRUCTION_FILE).is_file() and (
            directory / REFERENCE_FILE
        ).is_file()

    @staticmethod
    def _read(path: Path) -> str:
        """
        Read a catalog file.

        :param path: file to read

        :raises PropertyCatalogError: when the file cannot be read as UTF-8

        :return: the file text
        """
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise PropertyCatalogError(f"cannot read {path}: {error}") from error

    def _type_numbers(self, reference: Path) -> tuple[str, ...]:
        """
        Collect the ``### N.`` headings of the ``## Violation types`` section.

        :param reference: ``reference.md`` of a property

        :raises PropertyCatalogError: when the file cannot be read

        :return: type numbers in file order; empty without the section
        """
        numbers = []
        inside = False
        for line in self._read(reference).splitlines():
            if line.startswith("## "):
                inside = line.rstrip() == VIOLATION_TYPES_HEADING
            elif inside and (match := TYPE_HEADING.match(line)):
                numbers.append(match.group(1))
        return tuple(numbers)

    def _translations(self, path: Path) -> Translations:
        """
        Read a translation file.

        :param path: ``translation/<language>.json``

        :raises PropertyCatalogError: when the file cannot be read or has an
            unexpected shape

        :return: property names and type names by property id
        """
        try:
            root = json.loads(self._read(path))
        except ValueError as error:
            raise PropertyCatalogError(f"{path}: invalid JSON: {error}") from error
        if not isinstance(root, dict):
            raise PropertyCatalogError(f"{path}: root is not an object")
        properties: dict[str, str] = {}
        types: dict[str, dict[str, str]] = {}
        for property_id, entry in root.items():
            reason = self._entry_error(entry)
            if reason:
                raise PropertyCatalogError(f"{path}: {property_id!r}: {reason}")
            properties[property_id] = entry["name"]
            types[property_id] = entry["types"]
        return properties, types

    @staticmethod
    def _entry_error(entry: object) -> str | None:
        """
        Check the shape of one translation entry.

        :param entry: value of a property id in the translation file

        :return: why the entry is invalid, or None when it is valid
        """
        if not isinstance(entry, dict):
            return "entry is not an object"
        if not isinstance(entry.get("name"), str):
            return "name is not a string"
        types = entry.get("types")
        if not isinstance(types, dict) or not all(
            isinstance(name, str) for name in types.values()
        ):
            return "types is not an object of strings"
        return None
