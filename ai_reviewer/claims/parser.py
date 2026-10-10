import json
import logging

from .claim import Claim, Place
from .errors import ClaimsFormatError

logger = logging.getLogger(__name__)


class ClaimsParser:
    """Parses the claim array of one property file."""

    def check(self, text: str) -> None:
        """
        Check that the text is a JSON array.

        :param text: property file content

        :raises ClaimsFormatError: when the text is invalid JSON or its root
            is not an array
        """
        self._array(text)

    def parse(self, text: str, property_id: str) -> list[Claim]:
        """
        Parse the claims; skip and log claims with an invalid place.

        The place is not checked against the article.

        :param text: property file content
        :param property_id: property the file belongs to, for the log

        :raises ClaimsFormatError: when the text is invalid JSON or its root
            is not an array

        :return: claims in file order
        """
        claims = []
        for item in self._array(text):
            claim = self._claim_of(item)
            if isinstance(claim, str):
                logger.warning("%s: skip claim: %s", property_id, claim)
            else:
                claims.append(claim)
        return claims

    @staticmethod
    def _array(text: str) -> list[object]:
        """
        Parse the text as a JSON array.

        :param text: property file content

        :raises ClaimsFormatError: when the text is invalid JSON or its root
            is not an array

        :return: the array items
        """
        try:
            root = json.loads(text)
        except ValueError as error:
            raise ClaimsFormatError(f"invalid JSON: {error}") from error
        if not isinstance(root, list):
            raise ClaimsFormatError("JSON root is not an array")
        return root

    @staticmethod
    def _claim_of(item: object) -> Claim | str:
        """
        Convert one raw claim.

        :param item: raw claim from the property file

        :return: the claim, or why it is skipped
        """
        if not isinstance(item, dict):
            return "claim is not an object"
        place = item.get("place")
        if not isinstance(place, dict):
            return "no place"
        chapter = place.get("chapter")
        if not isinstance(chapter, str):
            return f"unknown chapter {chapter!r}"
        paragraph = place.get("paragraph")
        # bool and float pass `in` checks: True in {1}, 3.0 in {3}.
        if type(paragraph) is not int:
            return f"unknown paragraph {paragraph!r} in chapter {chapter!r}"
        fields = {key: value for key, value in item.items() if key != "place"}
        return Claim(Place(chapter, paragraph), fields)
