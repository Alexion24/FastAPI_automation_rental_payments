import pandas as pd
from datetime import datetime, timedelta
import calendar
from io import BytesIO
import logging

# Настройка логгера
logger = logging.getLogger("FastAPI_automation_rental_payments")
logger.setLevel(logging.DEBUG)  # можно поменять на INFO для менее подробного лога
ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def correct_payment_date(expected_date):
    """
    Коррекция даты оплаты:
    Если день больше количества дней в месяце, возвращаем последний день месяца.
    """
    day = expected_date.day
    month = expected_date.month
    year = expected_date.year
    last_day = calendar.monthrange(year, month)[1]
    if day > last_day:
        logger.debug(f"Коррекция даты с {day} на последний день месяца {last_day}")
        return expected_date.replace(day=last_day)
    return expected_date


def parse_amount(amount_str):
    """
    Преобразует строку формата "+2 800,00" в float 2800.00
    """
    try:
        cleaned = amount_str.replace("+", "").replace(",", ".").replace(" ", "").strip()
        amount = float(cleaned)
        return amount
    except Exception as e:
        logger.error(f"Ошибка преобразования суммы '{amount_str}': {e}")
        raise


def load_arenda_data(file_content):
    """
    Загрузка и проверка данных аренды из Excel.
    Проверяет наличие нужных колонок.
    """
    try:
        df = pd.read_excel(BytesIO(file_content))
    except Exception as e:
        logger.error(f"Ошибка чтения файла аренды: {e}")
        raise ValueError("Файл аренды не удалось прочитать как Excel")

    required_columns = {"Гараж", "Сумма", "Первоначальная дата"}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        logger.error(f"В файле аренды отсутствуют колонки: {missing}")
        raise ValueError(f"В файле аренды отсутствуют необходимые колонки: {missing}")

    logger.info(f"Файл аренды успешно загружен, строк: {len(df)}")
    return df


def prepare_bank_data(bank_file_content):
    """
    Обрабатывает выписку из банка.
    Находит операции с поступлениями (отрицательные суммы игнорируются).
    Возвращает список словарей с датами и суммами платежей.
    """
    try:
        bank_df = pd.read_excel(BytesIO(bank_file_content), header=None)
    except Exception as e:
        logger.error(f"Ошибка чтения файла выписки: {e}")
        raise ValueError("Файл банковской выписки не удалось прочитать как Excel")

    payments = []
    logger.info(f"Загружена банковская выписка, всего строк: {len(bank_df)}")

    for idx, row in bank_df.iterrows():
        try:
            # Проверяем, что в строке есть дата (в 0-м столбце)
            if not isinstance(row[0], str):
                continue
            if not any(ch.isdigit() for ch in row[0]):
                continue
            # Проверяем, есть ли 5-й столбец и содержит ли он "+"
            if len(row) <= 4 or not isinstance(row[4], str) or "+" not in row[4]:
                continue

            date_str = row[0].split()[0]  # берём только дату, без времени
            date = datetime.strptime(date_str, "%d.%m.%Y")
            amount = parse_amount(row[4])

            payments.append({"date": date, "amount": amount})

        except Exception as e:
            logger.warning(f"Ошибка обработки строки {idx} в выписке: {e}")
            continue

    if not payments:
        logger.warning("Выписка не содержит поступлений или не удалось найти платежи.")
    else:
        logger.info(f"Найдено платежей в выписке: {len(payments)}")

    return payments


def check_payments(arenda_file_content, bank_file_content):
    """
    Основной алгоритм проверки платежей.
    Возвращает BytesIO с готовым Excel отчетом.
    """
    arenda_df = load_arenda_data(arenda_file_content)
    payments = prepare_bank_data(bank_file_content)
    today = datetime.now()
    results = []

    logger.info("Начинаем анализ оплат по каждому гаражу")

    for idx, row in arenda_df.iterrows():
        try:
            garage = str(row["Гараж"])
            expected_sum = float(row["Сумма"])
            first_date = pd.to_datetime(row["Первоначальная дата"])

            # Формируем ожидаемую дату оплаты для текущего месяца с учётом коррекции
            expected_date = correct_payment_date(
                datetime(today.year, today.month, first_date.day)
            )
            logger.debug(
                f"Гараж {garage} ожидает оплату {expected_date.strftime('%Y-%m-%d')} на сумму {expected_sum}"
            )

            # Находим платежи с подходящей суммой +/- 1 рубль и датой +-31 день от ожидаемой
            matching = [
                p
                for p in payments
                if abs(p["amount"] - expected_sum) < 1.0
                and abs((p["date"] - expected_date).days) <= 31
            ]

            if matching:
                payment_date = min(
                    matching, key=lambda p: abs((p["date"] - expected_date).days)
                )["date"]
                if payment_date <= expected_date + timedelta(days=3):
                    status = "получен"
                else:
                    status = "просрочен"

                logger.debug(
                    f"Гараж {garage} платеж найден на дату {payment_date.strftime('%Y-%m-%d')} - статус: {status}"
                )
            else:
                if today < expected_date:
                    status = "срок не наступил"
                else:
                    status = "просрочен"
                logger.debug(f"Гараж {garage} платеж не найден - статус: {status}")

            results.append(
                {
                    "Гараж": garage,
                    "Дата оплаты": expected_date.strftime("%Y-%m-%d"),
                    "Сумма": expected_sum,
                    "Статус": status,
                }
            )
        except Exception as e:
            logger.error(f"Ошибка при обработке строки {idx} из файла аренды: {e}")
            continue

    logger.info("Анализ оплат завершён")
    result_df = pd.DataFrame(results)
    out_bytes = BytesIO()
    result_df.to_excel(out_bytes, index=False)
    out_bytes.seek(0)
    return out_bytes
