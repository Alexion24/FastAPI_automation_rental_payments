# Garage Rent Payments Service

**Этот сервис автоматизирует проверку своевременности оплат за аренду гаражей и формирует отчёты о статусах платежей на основе таблицы аренды и банковской выписки.**

## 1. Клонирование репозитория

```bash
git clone https://github.com/Alexion24/FastAPI_automation_rental_payments.git
cd FastAPI_automation_rental_payments
```

## 2. Установка зависимостей

**Рекомендуется использовать виртуальное окружение:**

```bash
python3 -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate # Windows
```

**Установка библиотек:**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Запуск сервиса в режиме разработки

Запустите сервер FastAPI командой:
```bash
uvicorn app.main:app --reload
```

- По умолчанию сервис будет доступен на [`http://127.0.0.1:8000`](http://127.0.0.1:8000)
- Флаг `--reload` обеспечивает автоматическую перезагрузку при изменениях в исходном коде.

## 4. Использование и тестирование

### 4.1 Форма загрузки файлов

- Перейдите в браузере на: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Загрузите два файла:  
    - `arenda.xlsx` — исходная таблица гаражей
    - `print-2.xlsx` — выписка операций из Сбербанка
- После отправки формы автоматически начнётся обработка данных и будет загружен итоговый отчёт `garage_payments_report.xlsx`.

### 4.2 API (если нужно тестировать вручную)

- Эндпоинт для POST-запроса с файлами: `/analyze/`
- Пример запроса с использованием `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/analyze/"
-F "arenda_file=@/путь/к/arenda.xlsx"
-F "bank_file=@/путь/к/print-2.xlsx"
--output result.xlsx
```


