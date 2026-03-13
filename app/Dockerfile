# ============================================================
# Dockerfile — marketing_roi_app с ML-моделью
# Вариант 7: Маркетинговая аналитика с ML
# ============================================================

FROM python:3.11-slim

LABEL maintainer="student" \
      description="Marketing ROI analytics with ML model"

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Создание непривилегированного пользователя
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 -m appuser

WORKDIR /app

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения и ML-модели
COPY dashboard.py loader.py ml_model.py ./

COPY assets/ ./assets/

RUN test -f assets/style.css || (echo "ERROR: style.css missing" && exit 1) && \
    test -f assets/custom.js || (echo "ERROR: custom.js missing" && exit 1)

# Создаем пустой pkl-файл и даем права на запись
RUN touch roi_model.pkl && chown appuser:appuser roi_model.pkl && chmod 666 roi_model.pkl
# Даем права на всю директорию appuser'у
RUN chown -R appuser:appuser /app

# Переключение на непривилегированного пользователя
USER appuser

# Порт, на котором работает Dash (по умолчанию 8050)
EXPOSE 8050

# Точка входа по умолчанию — дашборд через gunicorn

CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--timeout", "120", "dashboard:server"]

