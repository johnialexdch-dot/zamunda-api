
# Използваме официално Python изображение
FROM python:3.11-slim

# Задаваме работна директория
WORKDIR /app

# Копираме файловете от текущата директория
COPY . .

# Инсталираме зависимостите
RUN pip install --no-cache-dir fastapi uvicorn zamunda-api

# Отваряме порт 8000 (Render използва този порт)
EXPOSE 8000

# Командата за стартиране на FastAPI сървъра
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
