#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import subprocess
import tempfile
import sys
import zlib
from typing import List, Dict, Set, Optional
from datetime import datetime

def read_git_object(git_dir: str, sha: str) -> bytes:
    object_dir = os.path.join(git_dir, 'objects', sha[:2])
    object_file = os.path.join(object_dir, sha[2:])
    if not os.path.isfile(object_file):
        raise RuntimeError(f"Объект {sha} не найден.")
    with open(object_file, 'rb') as f:
        compressed_data = f.read()
    try:
        decompressed_data = zlib.decompress(compressed_data)
    except zlib.error as e:
        raise RuntimeError(f"Не удалось разархивировать объект {sha}: {e}")
    return decompressed_data

def parse_git_object(data: bytes) -> (str, str, bytes):
    null_byte_index = data.find(b'\x00')
    if null_byte_index == -1:
        raise RuntimeError("Некорректный формат объекта Git.")
    header = data[:null_byte_index].decode('utf-8')
    type_, size = header.split(' ')
    content = data[null_byte_index + 1:]
    return type_, size, content

def get_commit_info(git_dir: str, commit_sha: str) -> Dict[str, Optional[str]]:
    data = read_git_object(git_dir, commit_sha)
    type_, size, content = parse_git_object(data)
    if type_ != 'commit':
        raise RuntimeError(f"Объект {commit_sha} не является коммитом.")
    lines = content.decode('utf-8', errors='replace').splitlines()
    commit_info = {
        'hash': commit_sha,
        'parent': [],
        'author': None,
        'date': None
    }
    for line in lines:
        if line.startswith('parent '):
            parent_hash = line.split(' ')[1]
            commit_info['parent'].append(parent_hash)
        elif line.startswith('author '):
            parts = line.split(' ', 2)
            if len(parts) >= 3:
                author_info = parts[2]
                author_parts = author_info.rsplit(' ', 2)
                if len(author_parts) >= 3:
                    commit_info['author'] = author_parts[0]
                    timestamp = author_parts[1]
                    commit_info['date'] = datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    return commit_info

def get_commit_history(repo_path: str) -> List[str]:
    git_dir = os.path.join(repo_path, '.git')
    if not os.path.isdir(git_dir):
        raise RuntimeError(f"Путь {git_dir} не является git-репозиторием.")
    head_path = os.path.join(git_dir, 'HEAD')
    if not os.path.isfile(head_path):
        raise RuntimeError("Файл HEAD не найден в репозитории.")
    with open(head_path, 'r') as f:
        head_content = f.read().strip()
    if head_content.startswith('ref:'):
        ref_path = head_content.split(' ')[1]
        current_ref = os.path.join(git_dir, ref_path.replace('/', os.sep))
        if not os.path.isfile(current_ref):
            raise RuntimeError(f"Ссылка {ref_path} не найдена.")
        with open(current_ref, 'r') as f:
            current_commit = f.read().strip()
    else:
        current_commit = head_content
    commits = []
    visited = set()
    stack = [current_commit]
    while stack:
        commit_sha = stack.pop()
        if commit_sha in visited:
            continue
        visited.add(commit_sha)
        commits.append(commit_sha)
        commit_info = get_commit_info(git_dir, commit_sha)
        parents = commit_info.get('parent', [])
        for parent in parents:
            if parent and parent not in visited:
                stack.append(parent)
    return commits

def read_tree(git_dir: str, tree_sha: str) -> Dict[str, str]:
    tree_data = read_git_object(git_dir, tree_sha)
    type_, size, content = parse_git_object(tree_data)
    if type_ != 'tree':
        raise RuntimeError(f"Объект {tree_sha} не является деревом.")
    entries = {}
    i = 0
    while i < len(content):
        space_index = content.find(b' ', i)
        if space_index == -1:
            break
        mode = content[i:space_index].decode('utf-8')
        i = space_index + 1
        null_index = content.find(b'\x00', i)
        if null_index == -1:
            break
        name = content[i:null_index].decode('utf-8')
        i = null_index + 1
        hash_bytes = content[i:i+20]
        object_hash = ''.join(['{:02x}'.format(b) for b in hash_bytes])
        i += 20
        entries[name] = object_hash
    return entries

def diff_trees(parent_tree: Dict[str, str], current_tree: Dict[str, str]) -> List[str]:
    changed_files = []
    all_keys = set(parent_tree.keys()).union(set(current_tree.keys()))
    for key in all_keys:
        parent_hash = parent_tree.get(key)
        current_hash = current_tree.get(key)
        if parent_hash != current_hash:
            changed_files.append(key)
    return changed_files

def get_commit_changes(repo_path: str, commit_hash: str) -> List[str]:
    git_dir = os.path.join(repo_path, '.git')
    if not os.path.isdir(git_dir):
        raise RuntimeError(f"Путь {git_dir} не является git-репозиторием.")
    current_commit_obj = read_git_object(git_dir, commit_hash)
    type_, size, content = parse_git_object(current_commit_obj)
    if type_ != 'commit':
        raise RuntimeError(f"Объект {commit_hash} не является коммитом.")
    lines = content.decode('utf-8', errors='replace').splitlines()
    tree_hash = None
    parents = []
    for line in lines:
        if line.startswith('tree '):
            tree_hash = line.split(' ')[1]
        elif line.startswith('parent '):
            parent_hash = line.split(' ')[1]
            parents.append(parent_hash)
        elif line == '':
            break
    if not tree_hash:
        raise RuntimeError(f"Не удалось найти дерево в коммите {commit_hash}.")
    if parents:
        parent_commit = parents[0]
        parent_commit_obj = read_git_object(git_dir, parent_commit)
        type_p, size_p, content_p = parse_git_object(parent_commit_obj)
        if type_p != 'commit':
            raise RuntimeError(f"Объект {parent_commit} не является коммитом.")
        lines_p = content_p.decode('utf-8', errors='replace').splitlines()
        tree_hash_p = None
        for line in lines_p:
            if line.startswith('tree '):
                tree_hash_p = line.split(' ')[1]
            elif line == '':
                break
        if not tree_hash_p:
            raise RuntimeError(f"Не удалось найти дерево в родительском коммите {parent_commit}.")
        parent_tree = read_tree(git_dir, tree_hash_p)
    else:
        parent_tree = {}
    current_tree = read_tree(git_dir, tree_hash)
    changed_files = diff_trees(parent_tree, current_tree)
    return changed_files

def get_all_files_and_dirs(repo_path: str, commit_hash: str) -> (Set[str], Set[str]):
    git_dir = os.path.join(repo_path, '.git')
    current_commit_obj = read_git_object(git_dir, commit_hash)
    type_, size, content = parse_git_object(current_commit_obj)
    if type_ != 'commit':
        raise RuntimeError(f"Объект {commit_hash} не является коммитом.")
    lines = content.decode('utf-8', errors='replace').splitlines()
    tree_hash = None
    for line in lines:
        if line.startswith('tree '):
            tree_hash = line.split(' ')[1]
        elif line == '':
            break
    if not tree_hash:
        raise RuntimeError(f"Не удалось найти дерево в коммите {commit_hash}.")
    files = set()
    dirs = set()
    def traverse_tree(t_hash, prefix=""):
        t_data = read_tree(git_dir, t_hash)
        for name, obj_hash in t_data.items():
            obj_data = read_git_object(git_dir, obj_hash)
            t_, s_, c_ = parse_git_object(obj_data)
            path = name if prefix == "" else prefix + "/" + name
            if t_ == 'tree':
                dirs.add(path)
                traverse_tree(obj_hash, path)
            else:
                files.add(path)
                parts = path.split('/')
                for i in range(1, len(parts)):
                    d = '/'.join(parts[:i])
                    dirs.add(d)
    traverse_tree(tree_hash)
    return files, dirs

def build_dependency_graph(commits: List[str], repo_path: str) -> Dict[str, Dict[str, List[str]]]:
    graph_data = {
        "commits": {},
        "files": set(),
        "dirs": set()
    }

    for commit in commits:
        try:
            changed_files = get_commit_changes(repo_path, commit)
        except RuntimeError as e:
            print(f"Предупреждение: {e}", file=sys.stderr)
            changed_files = []
        graph_data["commits"][commit] = {"files": changed_files}
        for f in changed_files:
            graph_data["files"].add(f)
            parts = f.split('/')
            for i in range(1, len(parts)):
                d = '/'.join(parts[:i])
                graph_data["dirs"].add(d)

    if commits:
        all_files, all_dirs = get_all_files_and_dirs(repo_path, commits[0])
        for f in all_files:
            graph_data["files"].add(f)
            parts = f.split('/')
            for i in range(1, len(parts)):
                d = '/'.join(parts[:i])
                graph_data["dirs"].add(d)
        for d in all_dirs:
            graph_data["dirs"].add(d)

    return graph_data

def parent_directory(path: str) -> Optional[str]:
    parts = path.split('/')
    if len(parts) > 1:
        return '/'.join(parts[:-1])
    return None

def generate_dot_file(graph_data: Dict[str, Dict[str, List[str]]], output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("digraph dependencies {\n")
        f.write("  rankdir=TB;\n")
        f.write("  node [shape=rectangle, fontname=\"Helvetica\"];\n\n")

        # Коммиты
        for commit in graph_data["commits"].keys():
            f.write(f"  \"{commit}\" [label=\"{commit[:7]}\" style=filled fillcolor=lightblue];\n")
        f.write("\n")

        # Директории
        for directory in graph_data["dirs"]:
            f.write(f"  \"{directory}\" [label=\"{directory}\" style=filled fillcolor=orange];\n")
        f.write("\n")

        # Файлы
        for file_name in graph_data["files"]:
            f.write(f"  \"{file_name}\" [label=\"{file_name}\" style=filled fillcolor=lightgreen];\n")
        f.write("\n")

        # Ребра коммит -> директория или файл (если файл в корне)
        for commit, data in graph_data["commits"].items():
            changed_files = data["files"]
            for file_name in changed_files:
                pdir = parent_directory(file_name)
                if pdir:
                    f.write(f"  \"{commit}\" -> \"{pdir}\";\n")
                else:
                    # Файл находится в корне, создаём связь напрямую с файлом
                    f.write(f"  \"{commit}\" -> \"{file_name}\";\n")
        f.write("\n")

        # Ребра между директориями (родитель -> дочерняя директория)
        for directory in graph_data["dirs"]:
            pd = parent_directory(directory)
            if pd:
                f.write(f"  \"{pd}\" -> \"{directory}\";\n")
        f.write("\n")

        # Ребра директория -> файл
        for file_name in graph_data["files"]:
            pdir = parent_directory(file_name)
            if pdir:
                f.write(f"  \"{pdir}\" -> \"{file_name}\";\n")
        f.write("}\n")

def visualize_graph(graphviz_path: str, dot_file: str):
    png_file = dot_file + ".png"
    cmd = [graphviz_path, "-Tpng", dot_file, "-o", png_file]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Не удалось визуализировать граф: {result.stderr}")
    try:
        if sys.platform.startswith('darwin'):
            subprocess.run(['open', png_file], check=True)
        elif sys.platform.startswith('win'):
            os.startfile(png_file)
        else:
            subprocess.run(['xdg-open', png_file], check=True)
    except Exception:
        print(f"Граф сгенерирован и сохранен в {png_file}.")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Инструмент для визуализации графа зависимостей из git-репозитория.")
    parser.add_argument("--graphviz-path", required=True, help="Путь к программе dot (Graphviz).")
    parser.add_argument("--repo-path", required=True, help="Путь к анализируемому git-репозиторию.")
    return parser.parse_args()

def main():
    args = parse_args()
    if not os.path.isdir(args.repo_path):
        print(f"Указанный путь к репозиторию неверен: {args.repo_path}", file=sys.stderr)
        sys.exit(1)
    try:
        commits = get_commit_history(args.repo_path)
    except RuntimeError as e:
        print(f"Ошибка при получении истории коммитов: {e}", file=sys.stderr)
        sys.exit(1)
    if not commits:
        print("В репозитории нет коммитов для анализа.", file=sys.stderr)
        sys.exit(1)
    graph_data = build_dependency_graph(commits, args.repo_path)
    with tempfile.NamedTemporaryFile(suffix=".dot", delete=False) as tmp_file:
        dot_path = tmp_file.name
    try:
        generate_dot_file(graph_data, dot_path)
        visualize_graph(args.graphviz_path, dot_path)
    finally:
        if os.path.exists(dot_path):
            os.remove(dot_path)

if __name__ == "__main__":
    main()
