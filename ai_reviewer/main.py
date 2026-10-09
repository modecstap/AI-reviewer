from pathlib import Path

from cursor_sdk import ModelParameterValue, ModelSelection

from ai_reviewer.ai_pool import AIPool, AgentDefinition
from ai_reviewer.splitter import ArticleRefiner

if __name__ == "__main__":
    refiner = ArticleRefiner()
    model = ModelSelection(
        id="composer-2.5",
        params=(
            ModelParameterValue(id="fast", value="false"),
        ),
    )

    ai_pool = AIPool(model=model)

    descriptions = [
        AgentDefinition(
            io_structure=Path("./properties/IO-structure.md"),
            docs=Path("./properties/caution"),
            name="Caution"
        )
    ]
    output_dir = Path("./tests/temp_output")
    article_path = "./tests/data/test_article.docx"

    for description in descriptions:
        ai_pool.add_agent(description, output_dir)

    ai_pool.execute(refiner.refine(article_path))

