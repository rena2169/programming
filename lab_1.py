"""
1.	Сортировка по категориям. Файлы раскладываются по папкам Images, Documents, Archives, Videos, Audio, Programs и Other (для всего, что не подошло).
2.	Защита от перезаписи. Функция get_unique_destination проверяет, есть ли уже файл с таким именем в целевой папке. Если есть - добавляет суффикс _1, _2 и так далее. 
Это гораздо безопаснее, чем просто shutil.move(), который может молча перезаписать данные.
3.	Логирование. Все действия записываются в консоль и в файл organizer.log с метками времени. 
4.	Интерфейс командной строки. Через argparse можно передать путь к папке и флаг --dry-run:
# Посмотреть, что будет сделано (безопасно)
python lab_1.py ~/Downloads --dry-run
# Реально отсортировать
python lab_1.py ~/Downloads
5.	Если путь не указан, по умолчанию берется ~/Downloads.
6.	Кроссплатформенность. Используются pathlib.Path и проверка через os.name в оригинале, здесь же путь по умолчанию строится через Path.home(), 
что работает и на Windows, и на macOS, и на Linux
"""

import os
import shutil
import argparse
import logging
from pathlib import Path
from collections import defaultdict

# --- Настройка логирования ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("organizer.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# --- Определение категорий файлов ---
CATEGORIES = {
    'Images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.heic'},
    'Documents': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv', '.rtf', '.odt'},
    'Archives': {'.zip', '.rar', '.tar', '.gz', '.7z'},
    'Videos': {'.mp4', '.mov', '.wmv', '.flv', '.avi', '.mkv', '.webm'},
    'Audio': {'.mp3', '.wav', '.aac', '.ogg', '.flac'},
    'Programs': {'.exe', '.msi', '.bat', '.sh', '.dmg', '.app', '.deb', '.rpm', '.apk'},
}


def get_category(file_path: Path) -> str:
    """Возвращает категорию файла на основе его расширения."""
    ext = file_path.suffix.lower()
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return 'Other'


def get_unique_destination(dest_dir: Path, filename: str) -> Path:
    """Если файл с таким именем уже существует, добавляет числовой суффикс."""
    dest_path = dest_dir / filename
    if not dest_path.exists():
        return dest_path

    stem = dest_path.stem
    suffix = dest_path.suffix
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = dest_dir / new_name
        if not new_path.exists():
            return new_path
        counter += 1


def organize_folder(source_dir: Path, dry_run: bool = False) -> None:
    """Основная функция организации файлов."""
    if not source_dir.exists():
        logging.error(f"Папка не найдена: {source_dir}")
        return
    if not source_dir.is_dir():
        logging.error(f"Указанный путь не является папкой: {source_dir}")
        return

    logging.info(f"Начинаю сортировку в: {source_dir}")
    if dry_run:
        logging.info("РЕЖИМ ПРЕДПРОСМОТРА (файлы не будут перемещены)")

    # Создаем папки для всех категорий + Other
    for category in list(CATEGORIES.keys()) + ['Other']:
        category_dir = source_dir / category
        if not category_dir.exists():
            if not dry_run:
                category_dir.mkdir(exist_ok=True)
            logging.debug(f"Создана папка: {category_dir}")

    moved_count = 0
    skipped_count = 0

    for item in source_dir.iterdir():
        # Пропускаем папки и сам скрипт
        if item.is_dir() or item.name == Path(__file__).name:
            continue

        category = get_category(item)
        dest_dir = source_dir / category
        dest_path = get_unique_destination(dest_dir, item.name)

        if dry_run:
            logging.info(f"[ПРЕДПРОСМОТР] {item.name} → {category}/")
        else:
            try:
                shutil.move(str(item), str(dest_path))
                logging.info(f"Перемещен: {item.name} → {category}/")
                moved_count += 1
            except Exception as e:
                logging.error(f"Ошибка при перемещении {item.name}: {e}")
                skipped_count += 1

    if not dry_run:
        logging.info(f"Готово! Перемещено: {moved_count}, ошибок: {skipped_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Сортировщик файлов: раскладывает файлы по папкам в зависимости от расширения."
    )
    parser.add_argument(
        'path',
        nargs='?',
        default=str(Path.home() / 'Downloads'),
        help='Путь к папке для сортировки (по умолчанию: ~/Downloads)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Показать, что будет сделано, без фактического перемещения файлов'
    )

    args = parser.parse_args()
    source_path = Path(args.path).expanduser().resolve()

    organize_folder(source_path, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
