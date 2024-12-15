
# Визуализатор Графа Зависимостей Git-Репозитория

## Описание

Этот инструмент командной строки предназначен для визуализации графа зависимостей коммитов в Git-репозитории с использованием Graphviz. Он анализирует историю коммитов, определяет изменённые файлы и строит граф, отображающий связи между коммитами, файлами и директориями.

## Возможности

- **Анализ коммитов:** Извлекает историю коммитов из указанного Git-репозитория.
- **Определение зависимостей:** Определяет изменённые файлы для каждого коммита и строит зависимости между коммитами и файлами.
- **Визуализация графа:** Генерирует графическое изображение зависимостей с помощью Graphviz.
- **Поддержка транзитивных зависимостей:** Отображает зависимости между файлами и директориями.
- **Тестирование:** Включает тесты для основных функций инструмента.

## Требования

Перед началом использования убедитесь, что на вашем компьютере установлены следующие программы:

- **Python 3** (рекомендуется версия 3.6 и выше)
- **Git**
- **Graphviz**

## Установка

### 1. Установка Python 3

Скачайте и установите Python 3 с [официального сайта Python](https://www.python.org/downloads/).

### 2. Установка Git

Скачайте и установите Git с [официального сайта Git](https://git-scm.com/downloads).

### 3. Установка Graphviz

**Для Windows:**

1. Скачайте установщик Graphviz с [официального сайта Graphviz](https://graphviz.org/download/).
2. Установите Graphviz, следуя инструкциям установщика.
3. Добавьте путь к `dot.exe` (например, `C:\Program Files\Graphviz\bin`) в переменную окружения `PATH`.

**Для macOS:**

Используйте Homebrew для установки Graphviz:

```bash
brew install graphviz
```

**Для Linux (Debian/Ubuntu):**

```bash
sudo apt-get update
sudo apt-get install graphviz
```

### 4. Клонирование Репозитория

Склонируйте этот репозиторий на ваш локальный компьютер:

```bash
git clone https://github.com/ваш-пользователь/визуализатор-графа-зависимостей.git
cd визуализатор-графа-зависимостей
```

### 5. Установка Зависимостей

Для данного инструмента не требуется установка дополнительных Python-библиотек, так как используются стандартные библиотеки Python. Однако, рекомендуется использовать виртуальное окружение:

```bash
python3 -m venv venv
source venv/bin/activate  # Для Unix или macOS
venv\Scripts\activate     # Для Windows
```

## Использование

### Синтаксис Команды

```bash
python3 visualize_deps.py --graphviz-path <ПУТЬ_К_dot> --repo-path <ПУТЬ_К_РЕПО>
```

### Параметры

- `--graphviz-path`: Полный путь к исполняемому файлу `dot` из Graphviz.
- `--repo-path`: Полный путь к Git-репозиторию, для которого необходимо построить граф зависимостей.

### Примеры

**Пример 1: Использование полного пути к `dot`**

```bash
python3 visualize_deps.py --graphviz-path /usr/bin/dot --repo-path /home/user/my_git_repo
```

**Пример 2: Если `dot` добавлен в переменную PATH**

```bash
python3 visualize_deps.py --graphviz-path dot --repo-path /home/user/my_git_repo
```

**Пример 3: Для Windows**

```bash
python visualize_deps.py --graphviz-path "C:\Program Files\Graphviz\bin\dot.exe" --repo-path "C:\Projects\sample_git_repo"
```

### Что Происходит При Запуске

1. **Извлечение Коммитов:** Скрипт извлекает историю коммитов из указанного Git-репозитория.
2. **Анализ Изменений:** Для каждого коммита определяется список изменённых файлов.
3. **Построение Графа:** Формируется структура графа зависимостей, где узлами являются коммиты, файлы и директории.
4. **Генерация DOT-Файла:** Создаётся файл в формате DOT, описывающий граф.
5. **Визуализация Графа:** С помощью Graphviz (`dot`) генерируется графическое изображение (PNG).
6. **Открытие Изображения:** Автоматически открывается сгенерированный PNG-файл с графом.

## Создание Примерного Git-Репозитория

Если у вас ещё нет репозитория для тестирования, вы можете создать его, следуя этим шагам:

### Шаг 1: Открытие Командной Строки

Откройте командную строку (cmd) на Windows или терминал на Unix-подобных системах.

### Шаг 2: Создание и Инициализация Репозитория

```cmd
cd %USERPROFILE%\Desktop
mkdir sample_git_repo
cd sample_git_repo
git init
```

### Шаг 3: Создание Директорий и Файлов

```cmd
mkdir src
mkdir docs

echo def hello_world(): > src\main.py
echo     print('Hello, World!') >> src\main.py

echo def add(a, b): > src\utils.py
echo     return a + b >> src\utils.py

echo # Sample Git Repository > docs\README.md
```

### Шаг 4: Первоначальный Коммит

```cmd
git add .
git commit -m "Initial commit: Add project structure with src and docs directories"
```

### Шаг 5: Добавление Новых Файлов и Коммитов

**Коммит 2: Добавление `goodbye.py`**

```cmd
echo def goodbye_world(): > src\goodbye.py
echo     print('Goodbye, World!') >> src\goodbye.py

git add src\goodbye.py
git commit -m "Add goodbye_world function to src\goodbye.py"
```

**Коммит 3: Изменение `utils.py`**

```cmd
> src\utils.py echo def add(a, b):
>> src\utils.py echo     if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
>> src\utils.py echo         raise ValueError('Both arguments must be numbers')
>> src\utils.py echo     return a + b

git add src\utils.py
git commit -m "Update add function in utils.py to include type checking"
```

**Коммит 4: Добавление `main.md` в `docs`**

```cmd
echo # Main Module > docs\main.md
echo This module contains the main entry point of the application. >> docs\main.md

git add docs\main.md
git commit -m "Add documentation for main.py in docs\main.md"
```

**Коммит 5: Рефакторинг `main.py`**

```cmd
echo from utils import add >> src\main.py
echo. >> src\main.py
echo def main(): >> src\main.py
echo     result = add(5, 7) >> src\main.py
echo     print(f'Result of add: {result}') >> src\main.py
echo. >> src\main.py
echo if __name__ == '__main__': >> src\main.py
echo     main() >> src\main.py

git add src\main.py
git commit -m "Refactor main.py to use add function from utils.py"
```

### Шаг 6: Проверка Истории Коммитов

```cmd
git log --oneline
```

**Ожидаемый Вывод:**

```
abcdef4 Refactor main.py to use add function from utils.py
abcdef3 Add documentation for main.py in docs/main.md
abcdef2 Update add function in utils.py to include type checking
abcdef1 Add goodbye_world function to src/goodbye.py
abcdef0 Initial commit: Add project structure with src and docs directories
```

## Пример Итогового Графа

На основе созданного примерного Git-репозитория итоговый граф зависимостей будет содержать следующие узлы и рёбра:

### Узлы

- **Коммиты:**
  - `abcdef0`
  - `abcdef1`
  - `abcdef2`
  - `abcdef3`
  - `abcdef4`

- **Файлы:**
  - `src/main.py`
  - `src/utils.py`
  - `src/goodbye.py`
  - `docs/README.md`
  - `docs/main.md`

- **Директории:**
  - `src`
  - `docs`

### Рёбра

- **Коммиты → Файлы:**
  - `abcdef0` → `docs/README.md`
  - `abcdef0` → `src/main.py`
  - `abcdef0` → `src/utils.py`
  - `abcdef1` → `src/goodbye.py`
  - `abcdef2` → `src/utils.py`
  - `abcdef3` → `docs/main.md`
  - `abcdef4` → `src/main.py`

- **Файлы → Директории:**
  - `docs/README.md` → `docs`
  - `docs/main.md` → `docs`
  - `src/main.py` → `src`
  - `src/utils.py` → `src`
  - `src/goodbye.py` → `src`

## Тестирование

Для тестов воспользуйтесь фреймворком pytest. Создайте файл `test_visualize_deps.py` с примерными тестами.

## Лицензия

MIT
