#!/usr/bin/env python3
"""
ETL-загрузчик: читает marketing_campaigns.csv и загружает в PostgreSQL.
Запускается как Job в Kubernetes.
"""

import csv
import os
import sys
import time
import psycopg2

DB_HOST = os.getenv("DB_HOST", "db-service")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "marketing_db")
DB_USER = os.getenv("POSTGRES_USER", "marketing_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "changeme")
CSV_PATH = os.getenv("CSV_PATH", "/data/marketing_campaigns.csv")

DDL = """
CREATE TABLE IF NOT EXISTS marketing_campaigns (
    campaign_id   INT PRIMARY KEY,
    date          DATE NOT NULL,
    channel       VARCHAR(50) NOT NULL,
    region        VARCHAR(50) NOT NULL,
    product       VARCHAR(50) NOT NULL,
    impressions   INT NOT NULL,
    clicks        INT NOT NULL,
    spend         INT NOT NULL,
    revenue       INT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_channel_date ON marketing_campaigns(channel, date);
"""


def wait_for_db(max_retries: int = 30, delay: int = 2):
    """Ожидание готовности PostgreSQL."""
    for attempt in range(1, max_retries + 1):
        try:
            conn = psycopg2.connect(
                host=DB_HOST, port=DB_PORT,
                dbname=DB_NAME, user=DB_USER, password=DB_PASS,
            )
            conn.close()
            print(f"[Loader] БД доступна (попытка {attempt})")
            return True
        except psycopg2.OperationalError:
            print(f"[Loader] Ожидание БД... ({attempt}/{max_retries})")
            time.sleep(delay)
    print("[Loader] БД недоступна, завершение.")
    return False


def generate_sample_data():
    """Генерация тестовых данных, если CSV не найден"""
    print("[Loader] CSV не найден, генерируем тестовые данные")
    import random
    from datetime import datetime, timedelta

    channels = ["Social Media", "Google Ads", "Email", "TV", "Billboard", "Partners"]
    regions = ["North", "South", "East", "West", "Central"]
    products = ["Product_A", "Product_B", "Product_C", "Product_D"]

    data = []
    start_date = datetime(2023, 1, 1)

    for i in range(1, 2001):
        campaign_date = start_date + timedelta(days=random.randint(0, 730))
        channel = random.choice(channels)
        impressions = random.randint(1000, 100000)
        clicks = int(impressions * random.uniform(0.01, 0.15))
        spend = int(clicks * random.uniform(0.5, 2.5))
        revenue = int(spend * random.uniform(1.5, 4.0))

        data.append({
            "campaign_id": i,
            "date": campaign_date.strftime("%Y-%m-%d"),
            "channel": channel,
            "region": random.choice(regions),
            "product": random.choice(products),
            "impressions": impressions,
            "clicks": clicks,
            "spend": spend,
            "revenue": revenue
        })

    return data


def load_data():
    """Загрузка данных в БД"""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )
    cur = conn.cursor()

    # Создание таблицы
    cur.execute(DDL)
    conn.commit()

    # Проверка наличия данных
    cur.execute("SELECT COUNT(*) FROM marketing_campaigns;")
    if cur.fetchone()[0] > 0:
        print("[Loader] Таблица уже содержит данные — пропуск загрузки.")
        cur.close()
        conn.close()
        return 0

    # Загрузка данных
    if os.path.exists(CSV_PATH):
        print(f"[Loader] Загрузка из CSV: {CSV_PATH}")
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            data = list(reader)
    else:
        print("[Loader] CSV не найден, используем сгенерированные данные")
        data = generate_sample_data()

    count = 0
    for row in data:
        cur.execute("""
            INSERT INTO marketing_campaigns 
            (campaign_id, date, channel, region, product, impressions, clicks, spend, revenue)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (campaign_id) DO NOTHING;
        """, (
            int(row["campaign_id"]), row["date"], row["channel"],
            row["region"], row["product"], int(row["impressions"]),
            int(row["clicks"]), int(row["spend"]), int(row["revenue"])
        ))
        count += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"[Loader] Загружено {count} строк в таблицу marketing_campaigns.")
    return count


def main():
    if wait_for_db():
        load_data()
    print("[Loader] Готово.")


if __name__ == "__main__":
    main()