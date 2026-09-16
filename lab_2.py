"""
1.	Гарантия наличия каждого типа. Сначала берём по одному случайному символу из каждого выбранного набора, потом добираем остаток из общего пула и перемешиваем. 
Это тот самый «крайний случай», о котором говорилось в совете: без него при длине 8 и 4 типах можно случайно получить пароль без спецсимволов.
2.	Криптографически стойкая случайность. Вместо random используется модуль secrets. Он берёт энтропию из ОС (os.urandom) и предназначен именно для паролей и токенов. 
random.choice для паролей - плохая практика, даже если алгоритм кажется «достаточно случайным».
3.	Проверка крайних случаев.
o	Если выбранных типов больше, чем длина пароля - понятная ошибка, а не «тихо сломается».
o	Если после фильтрации неоднозначных символов набор пуст - тоже явная ошибка.
o	Если не выбран ни один тип - сообщение и выход с кодом 1.
4.	Оценка стойкости. Небольшая эвристика по длине и разнообразию символов. Приятный бонус для пользователя.
5.	Два режима работы.
o	CLI: python password_gen.py -l 20 --exclude-ambiguous -n 5
o	Интерактив: python password_gen.py или с флагом --interactive
6.	Полезные мелочи. Флаг --exclude-ambiguous убирает l, 1, I, O, 0, o — те символы, которые легко перепутать при ручном вводе. Флаг -n генерирует сразу несколько паролей.
Примеры запуска
bash
# Один пароль длиной 20, все типы символов
python password_gen.py -l 20
# Пять паролей без спецсимволов и без похожих символов
python password_gen.py -l 16 --no-special --exclude-ambiguous -n 5
# Интерактивный режим — отвечаем на вопросы
python password_gen.py --interactive
"""

import argparse
import secrets
import string
import logging
import sys

# --- Настройка логирования ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# --- Наборы символов ---
CHARSETS = {
    'lower':   string.ascii_lowercase,
    'upper':   string.ascii_uppercase,
    'digits':  string.digits,
    'special': string.punctuation,
}

def build_charset(use_lower: bool, use_upper: bool, use_digits: bool, use_special: bool) -> dict:
    """Возвращает словарь {имя_типа: строка_символов} для выбранных типов."""
    selected = {}
    if use_lower:
        selected['lower'] = CHARSETS['lower']
    if use_upper:
        selected['upper'] = CHARSETS['upper']
    if use_digits:
        selected['digits'] = CHARSETS['digits']
    if use_special:
        selected['special'] = CHARSETS['special']
    return selected

def generate_password(length: int, selected: dict, exclude_ambiguous: bool = False) -> str:
    """
    Генерирует пароль заданной длины.
    Гарантирует наличие хотя бы одного символа каждого выбранного типа.
    """
    if not selected:
        raise ValueError("Не выбран ни один тип символов.")

    if length < len(selected):
        raise ValueError(
            f"Длина пароля ({length}) меньше числа выбранных типов ({len(selected)}). "
            f"Нужно минимум {len(selected)} символов, чтобы каждый тип был представлен."
        )

    # Собираем общий пул символов и, при необходимости, чистим неоднозначные
    ambiguous = 'Il1O0o'
    pool_parts = []
    type_parts = {}
    for name, chars in selected.items():
        filtered = ''.join(c for c in chars if c not in ambiguous) if exclude_ambiguous else chars
        if not filtered:
            raise ValueError(f"После исключения неоднозначных символов набор '{name}' пуст.")
        type_parts[name] = filtered
        pool_parts.append(filtered)

    full_pool = ''.join(pool_parts)

    # 1) По одному символу каждого типа — гарантия требований
    password_chars = [secrets.choice(type_parts[name]) for name in type_parts]

    # 2) Добираем остаток из общего пула
    remaining = length - len(password_chars)
    password_chars.extend(secrets.choice(full_pool) for _ in range(remaining))

    # 3) Перемешиваем, чтобы первые символы не выдавали структуру
    #    secrets не умеет shuffle, используем классический подход через SystemRandom
    secrets.SystemRandom().shuffle(password_chars)

    return ''.join(password_chars)

def evaluate_strength(password: str) -> str:
    """Простая оценка стойкости по длине и разнообразию."""
    has_lower   = any(c.islower() for c in password)
    has_upper   = any(c.isupper() for c in password)
    has_digit   = any(c.isdigit() for c in password)
    has_special = any(c in string.punctuation for c in password)
    variety = sum([has_lower, has_upper, has_digit, has_special])

    if len(password) >= 16 and variety == 4:
        return "Очень надёжный"
    if len(password) >= 12 and variety >= 3:
        return "Надёжный"
    if len(password) >= 8 and variety >= 2:
        return "Средний"
    return "Слабый"

def interactive_mode() -> dict:
    """Спрашивает параметры у пользователя, если аргументы не переданы."""
    print("=== Генератор паролей ===")

    while True:
        try:
            length = int(input("Длина пароля (по умолчанию 16): ").strip() or "16")
            if length <= 0:
                print("Длина должна быть положительным числом.")
                continue
            break
        except ValueError:
            print("Введите целое число.")

    def ask(prompt: str, default: bool = True) -> bool:
        answer = input(f"{prompt} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
        if not answer:
            return default
        return answer in ('y', 'yes', 'д', 'да')

    use_lower   = ask("Включать строчные буквы?")
    use_upper   = ask("Включать заглавные буквы?")
    use_digits  = ask("Включать цифры?")
    use_special = ask("Включать спецсимволы?")

    return {
        'length': length,
        'lower': use_lower,
        'upper': use_upper,
        'digits': use_digits,
        'special': use_special,
        'exclude_ambiguous': False,
    }

def main():
    parser = argparse.ArgumentParser(
        description="Генератор надёжных паролей.",
        epilog="Без аргументов запускается интерактивный режим."
    )
    parser.add_argument('-l', '--length', type=int, help="Длина пароля (по умолчанию 16)")
    parser.add_argument('--no-lower',   action='store_true', help="Не использовать строчные буквы")
    parser.add_argument('--no-upper',   action='store_true', help="Не использовать заглавные буквы")
    parser.add_argument('--no-digits',  action='store_true', help="Не использовать цифры")
    parser.add_argument('--no-special', action='store_true', help="Не использовать спецсимволы")
    parser.add_argument('-n', '--count', type=int, default=1, help="Сколько паролей сгенерировать")
    parser.add_argument('--exclude-ambiguous', action='store_true',
                        help="Исключить похожие символы (l, 1, I, O, 0, o)")
    parser.add_argument('--interactive', action='store_true', help="Интерактивный режим")

    args = parser.parse_args()

    # Если явно запрошен интерактив или вообще ничего не передали
    if args.interactive or len(sys.argv) == 1:
        params = interactive_mode()
    else:
        params = {
            'length': args.length if args.length else 16,
            'lower':   not args.no_lower,
            'upper':   not args.no_upper,
            'digits':  not args.no_digits,
            'special': not args.no_special,
            'exclude_ambiguous': args.exclude_ambiguous,
        }

    selected = build_charset(
        params['lower'], params['upper'], params['digits'], params['special']
    )

    if not selected:
        logging.error("Не выбран ни один тип символов. Нечего генерировать.")
        sys.exit(1)

    try:
        for i in range(args.count if not (args.interactive or len(sys.argv) == 1) else 1):
            password = generate_password(
                params['length'], selected, params['exclude_ambiguous']
            )
            strength = evaluate_strength(password)
            print(f"\nПароль:   {password}")
            print(f"Стойкость: {strength}")
    except ValueError as e:
        logging.error(e)
        sys.exit(1)

if __name__ == '__main__':
    main()
