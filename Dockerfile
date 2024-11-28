# Използваме официалния Python образ като базов
FROM python:3.9-slim

# Задаваме работната директория в контейнера
WORKDIR /app

# Копираме requirements файла в контейнера
COPY requirements.txt .

# Инсталираме необходимите зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копираме целия проект в контейнера
COPY . .

# Отваряме порт 8000 за достъп до приложението
EXPOSE 8000

# Стартираме приложението чрез Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]