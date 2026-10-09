from pathlib import Path

from ai_reviewer.ai_pool import AIPool, AgentDefinition
from ai_reviewer.splitter import ArticleRefiner

if __name__ == "__main__":
    refiner = ArticleRefiner()
    ai_pool = AIPool()

    descriptions = [
        AgentDefinition(
            io_structure=Path("D:/Projects/AI-reviewer/properties/IO-structure.md"),
            docs=Path("D:/Projects/AI-reviewer/properties/caution"),
            name="Caution"
        )
    ]
    output_dir = Path("D:/Projects/AI-reviewer/tests/temp_output")
    article_path = "D:/Projects/AI-reviewer/tests/data/test_article.docx"

    for description in descriptions:
        ai_pool.add_agent(description, output_dir)

    ai_pool.execute(refiner.refine(article_path))

