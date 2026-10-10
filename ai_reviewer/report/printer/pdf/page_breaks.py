import re

BLOCK_ID = re.compile(r"paragraph-(\d+)-(\d+)")


class ParagraphPageBreaks:
    """Chooses the paragraph blocks that must start on a new page."""

    @staticmethod
    def block_id(chapter: int, position: int) -> str:
        """
        Build the id of a paragraph block.

        :param chapter: position of the chapter in the report, from 1
        :param position: position of the block in its chapter, from 1

        :return: the block id
        """
        return f"paragraph-{chapter}-{position}"

    @staticmethod
    def text_end_id(chapter: int, position: int) -> str:
        """
        Build the id of the marker at the end of a paragraph block text.

        :param chapter: position of the chapter in the report, from 1
        :param position: position of the block in its chapter, from 1

        :return: the marker id
        """
        return f"{ParagraphPageBreaks.block_id(chapter, position)}-text-end"

    def next_moves(
        self, page_anchors: list[dict[str, tuple[float, ...]]], moved: set[str]
    ) -> set[str]:
        """
        Find the blocks to move next: their caption and text cross a page.

        :param page_anchors: anchors of every page, in page order
        :param moved: ids of the blocks already moved to a new page

        :return: ids of the blocks to move, empty when nothing must move
        """
        first_page: dict[str, int] = {}
        for index, anchors in enumerate(page_anchors):
            for name in anchors:
                first_page.setdefault(name, index)
        # Moving a block shifts every later block of its chapter, and chapters
        # never share a page, so only the first offender per chapter is known.
        offenders: dict[int, tuple[int, str]] = {}
        for name, page in first_page.items():
            match = BLOCK_ID.fullmatch(name)
            if match is None or match[2] == "1" or name in moved:
                continue
            chapter, position = int(match[1]), int(match[2])
            end_page = first_page.get(self.text_end_id(chapter, position))
            if end_page is None or end_page <= page:
                continue
            if chapter not in offenders or position < offenders[chapter][0]:
                offenders[chapter] = (position, name)
        return {name for _, name in offenders.values()}

    @staticmethod
    def stylesheet(moved: set[str]) -> str:
        """
        Build the CSS that starts the moved blocks on a new page.

        :param moved: ids of the moved blocks

        :return: one ``break-before: page`` rule per block, empty without
            blocks
        """
        return "".join(
            f"#{name} {{ break-before: page; }}\n" for name in sorted(moved)
        )
