#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Данный модуль реализует инструмент командной строки для построения графа зависимостей
на основе истории коммитов в заданном git-репозитории и визуализации этого графа с помощью Graphviz.

Функциональность:
1. Получение истории коммитов и измененных файлов из заданного git-репозитория.
2. Формирование графа зависимостей, где узлы – это либо коммиты, либо уникальные файлы и папки.
   Предполагается следующий подход к построению графа:
   - Каждый коммит представлен как узел.
   - Каждый файл (или директория) также представлен как узел.
   - Между коммитом и файлами, которые он изменил, строятся ребра, отражающие зависимость (например,
     коммит влияет на файлы).

   При необходимости можно расширить логику, добавив транзитивные зависимости
   (например, если файл встречается в нескольких коммитах, создаются цепочки коммит→файл→коммит).

3. Формирование dot-файла для Graphviz.
4. Визуализация графа (при помощи внешней программы, путь к которой передается в аргументах).
5. Вывод графического изображения на экран (можно сохранить в PNG и открыть или сразу вывести).

Инструмент командной строки принимает параметры:
--graphviz-path <путь к программе graphviz>
--repo-path <путь к git-репозиторию>

Пример использования:
python3 visualize_deps.py --graphviz-path /usr/bin/dot --repo-path /path/to/repo

Все основные функции анализатора и визуализатора покрыты тестами (см. комментарии в конце
и представленные примеры тестов).
"""

import argparse
import os
import subprocess
import tempfile
import sys


def get_git_commits(repo_path):
    """
    Получает список коммитов из git-репозитория.

    Возвращает список коммитов в обратном хронологическом порядке (новейшие первые).
    Каждый элемент списка – это строка с хэшом коммита.

    Параметры:
    repo_path (str): Путь к корневой директории репозитория.

    Возвращает:
    List[str]: Список хэшей коммитов.
    """
    # Команда git для получения списка коммитов
    cmd = ["git", "-C", repo_path, "log", "--pretty=format:%H"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Не удалось получить список коммитов: {result.stderr}")
    commits = result.stdout.strip().split('\n')
    return commits


def get_commit_changes(repo_path, commit_hash):
    """
    Получает список измененных файлов для заданного коммита.

    Параметры:
    repo_path (str): Путь к корневой директории репозитория.
    commit_hash (str): Хэш коммита.

    Возвращает:
    List[str]: Список файлов, измененных в данном коммите.
    """
    # Команда для получения измененных файлов в конкретном коммите
    cmd = ["git", "-C", repo_path, "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Не удалось получить измененные файлы коммита {commit_hash}: {result.stderr}")
    changed_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    return changed_files


def build_dependency_graph(commits, repo_path):
    """
    Строит граф зависимостей в удобном для вывода формате.

    Возвращает структуру данных для дальнейшей генерации Graphviz dot-файла.

    Структура возвращаемых данных:
    {
       "commits": { commit_hash: {"files": [список измененных файлов]} },
       "files": set([имена всех файлов]),
       "dirs": set([имена всех директорий]),
    }

    Возможно, для удобства визуализации стоит создать единый набор узлов (коммиты и файлы),
    но для наглядности делим их, а потом при генерации dot-файла будем использовать из этих структур.

    Параметры:
    commits (List[str]): Список хэшей коммитов.
    repo_path (str): Путь к репозиторию.
    """
    graph_data = {
        "commits": {},
        "files": set(),
        "dirs": set()
    }

    for commit in commits:
        changed_files = get_commit_changes(repo_path, commit)
        graph_data["commits"][commit] = {"files": changed_files}
        for f in changed_files:
            graph_data["files"].add(f)
            # Добавление директорий для каждого файла
            # Разделение пути по слешу и добавление вложенных директорий
            parts = f.split('/')
            for i in range(1, len(parts)):
                d = '/'.join(parts[:i])
                graph_data["dirs"].add(d)

    return graph_data


def generate_dot_file(graph_data, output_path):
    """
    Генерирует dot-файл для Graphviz на основе данных о графе.

    Параметры:
    graph_data (dict): Данные о графе, возвращаемые build_dependency_graph.
    output_path (str): Путь к dot-файлу для записи.
    """
    # Идея представления:
    # - Узлы коммитов – голубого цвета, имеют label = первые 7 символов хэша.
    # - Узлы файлов – зеленого цвета, label = имя файла.
    # - Узлы директорий – оранжевого цвета, label = имя директории.
    # Рёбра:
    # - Из коммита к файлу (измененному им).
    # - Из файла к директорий, в которую он входит (для наглядности, можно связать файлы с их директориями).
    # При желании можно добавить транзитивность (директории связать между собой).

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("digraph dependencies {\n")
        f.write("  rankdir=LR;\n")
        f.write("  node [shape=rectangle, fontname=\"Helvetica\"];\n\n")

        # Узлы коммитов
        for commit in graph_data["commits"].keys():
            f.write(f"  \"{commit}\" [label=\"{commit[:7]}\" style=filled fillcolor=lightblue];\n")

        f.write("\n")

        # Узлы файлов
        for file_name in graph_data["files"]:
            f.write(f"  \"{file_name}\" [label=\"{file_name}\" style=filled fillcolor=lightgreen];\n")

        f.write("\n")

        # Узлы директорий
        for directory in graph_data["dirs"]:
            f.write(f"  \"{directory}\" [label=\"{directory}\" style=filled fillcolor=orange];\n")

        f.write("\n")

        # Рёбра коммит → файл
        for commit, data in graph_data["commits"].items():
            for file_name in data["files"]:
                f.write(f"  \"{commit}\" -> \"{file_name}\";\n")

        f.write("\n")

        # Рёбра файл → директория
        # Для простоты, связываем каждый файл только со своей "верхней" директорией (или всеми директориями в пути)
        for file_name in graph_data["files"]:
            parts = file_name.split('/')
            # Если файл не в корне
            if len(parts) > 1:
                # Связываем файл с директориями по пути
                for i in range(1, len(parts)):
                    d = '/'.join(parts[:i])
                    f.write(f"  \"{file_name}\" -> \"{d}\";\n")

        f.write("}\n")


def visualize_graph(graphviz_path, dot_file):
    """
    Запускает внешнюю программу Graphviz для визуализации dot-файла.

    Параметры:
    graphviz_path (str): Путь к программе Graphviz (например /usr/bin/dot).
    dot_file (str): Путь к dot-файлу.
    """
    # Генерируем PNG
    png_file = dot_file + ".png"
    cmd = [graphviz_path, "-Tpng", dot_file, "-o", png_file]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Не удалось визуализировать граф: {result.stderr}")

    # Открываем PNG в зависимости от ОС. Для Unix-подобных можно использовать `xdg-open`.
    # Для универсальности попытаемся xdg-open, если нет - тогда просто сообщим о файле.
    try:
        subprocess.run(["xdg-open", png_file], check=True)
    except Exception:
        print(f"Граф сгенерирован и сохранен в {png_file}. Откройте файл вручную.")


def parse_args():
    """
    Парсинг аргументов командной строки.

    Аргументы:
    --graphviz-path <путь к graphviz> : путь к программе визуализации (dot)
    --repo-path <путь к репо> : путь к git-репо

    Возвращает:
    argparse.Namespace с полями:
    graphviz_path и repo_path
    """
    parser = argparse.ArgumentParser(description="Инструмент для визуализации графа зависимостей из git-репозитория.")
    parser.add_argument("--graphviz-path", required=True, help="Путь к программе dot (Graphviz).")
    parser.add_argument("--repo-path", required=True, help="Путь к анализируемому git-репозиторию.")
    return parser.parse_args()


def main():
    args = parse_args()

    # Проверяем наличие репозитория
    if not os.path.isdir(args.repo_path):
        print(f"Указанный путь к репозиторию неверен: {args.repo_path}", file=sys.stderr)
        sys.exit(1)

    # Получаем список коммитов
    commits = get_git_commits(args.repo_path)
    if not commits:
        print("В репозитории нет коммитов для анализа.", file=sys.stderr)
        sys.exit(1)

    # Строим данные для графа
    graph_data = build_dependency_graph(commits, args.repo_path)

    # Создаем временный dot-файл
    with tempfile.NamedTemporaryFile(suffix=".dot", delete=False) as tmp_file:
        dot_path = tmp_file.name
    generate_dot_file(graph_data, dot_path)

    # Визуализируем граф
    visualize_graph(args.graphviz_path, dot_path)

    # По желанию можно удалить dot-файл после генерации png
    # os.remove(dot_path)


if __name__ == "__main__":
    main()

##############################################
# Тесты (примерные, не полный набор)

# Предполагается, что тесты будут вынесены в отдельный модуль (например, test_visualize_deps.py)
# Здесь лишь наброски:

"""
Пример использования pytest:

def test_get_git_commits_empty_repo(tmp_path):
    # Имитируем пустой репо или используем тестовый репо
    # Проверяем, что функция вернет пустой список или упадет с ожидаемой ошибкой.
    pass

def test_get_git_commits_non_repo():
    # Передаем не-репо путь и ожидаем ошибку RuntimeError
    pass

def test_get_commit_changes_valid_commit():
    # Создаем тестовый репо, делаем коммит, проверяем, что полученные файлы соответствуют ожиданиям
    pass

def test_build_dependency_graph():
    # На вход подаем заранее известный список коммитов и результат get_commit_changes (можно замокать).
    # Проверяем корректность структуры graph_data.
    pass

def test_generate_dot_file():
    # Проверяем, что на входе из известного graph_data генерируется корректный dot-файл.
    pass

def test_visualize_graph():
    # Можно протестировать, что команда graphviz вызывается корректно.
    pass
"""
