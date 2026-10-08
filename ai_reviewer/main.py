from ai_reviewer.ai_pool import AIPool
from ai_reviewer.splitter import ArticleRefiner

if __name__ == "__main__":
    refiner = ArticleRefiner()
    ai_pool = AIPool()

    descriptions = []
    article_path = "articles/article.docx"

    for description in descriptions:
        ai_pool.add_agent(description.IO, description.docs, description.name, description.output_dir)
    ai_pool.execute(refiner.refine(article_path))
