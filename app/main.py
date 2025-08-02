from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from app.utils import check_payments
import logging

# Настройка логгера приложения
logger = logging.getLogger("FastAPI_automation_rental_payments")
logger.setLevel(logging.DEBUG)

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def upload_form():
    return """
    <html>
      <head><title>Проверка оплат аренды гаражей</title></head>
      <body>
        <h2>Загрузите файлы arenda.xlsx и print-2.xlsx</h2>
        <form action="/analyze/" enctype="multipart/form-data" method="post">
            <input name="arenda_file" type="file" required><br><br>
            <input name="bank_file" type="file" required><br><br>
            <button type="submit">Проверить</button>
        </form>
      </body>
    </html>
    """


@app.post("/analyze/")
async def analyze(arenda_file: UploadFile, bank_file: UploadFile):
    try:
        arenda_content = await arenda_file.read()
        bank_content = await bank_file.read()

        logger.info(
            f"Получены файлы: {arenda_file.filename} ({len(arenda_content)} байт), {bank_file.filename} ({len(bank_content)} байт)"
        )

        result_bytes = check_payments(arenda_content, bank_content)
        logger.info("Формирование отчёта завершено успешно.")

        return StreamingResponse(
            result_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment;filename=garage_payments_report.xlsx"
            },
        )
    except ValueError as ve:
        logger.error(f"Ошибка обработки: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
