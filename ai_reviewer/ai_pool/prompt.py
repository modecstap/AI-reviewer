PROMPT = """Ты рецензент научной статьи по свойству академичности «{name}».
Прочитай размеченный текст статьи из файла {run_dir}/article.txt.
Оцени его по инструкции и справочнику ниже.
Запиши результат только в файл {run_dir}/{name}.json строго по формату из раздела IO-structure.md.
Не создавай и не изменяй другие файлы.

# Файл IO-structure.md
{io}

# Файл instruction.md
{instruction}

# Файл reference.md
{reference}
"""
