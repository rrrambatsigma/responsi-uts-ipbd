from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import requests
import psycopg2


API_URL = "http://host.docker.internal:8000/articles"


def extract_articles(**context):
    response = requests.get(API_URL)
    data = response.json()

    articles = data.get("data", [])
    context['ti'].xcom_push(key='articles', value=articles)


def transform_articles(**context):
    articles = context['ti'].xcom_pull(key='articles')

    cleaned = []

    for article in articles:
        try:
            scraped_at = article.get("scraped_at")

            # convert ke datetime
            parsed_date = datetime.fromisoformat(scraped_at)

            article["scraped_at"] = parsed_date
            cleaned.append(article)

        except Exception:
            continue

    context['ti'].xcom_push(key='cleaned_articles', value=cleaned)


def load_to_postgres(**context):
    articles = context['ti'].xcom_pull(key='cleaned_articles')

    conn = psycopg2.connect(
        host="postgres_etl",
        database="responsi_ipbd",
        user="etl_user",
        password="etl_pass",
        port=5432
    )

    cursor = conn.cursor()

    for article in articles:
        try:
            cursor.execute("""
                INSERT INTO wired_articles (title, url, description, author, scraped_at, source)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
            """, (
                article.get("title"),
                article.get("url"),
                article.get("description"),
                article.get("author"),
                article.get("scraped_at"),
                article.get("source"),
            ))
        except Exception:
            continue

    conn.commit()
    cursor.close()
    conn.close()


with DAG(
    dag_id="wired_pipeline_dag",
    start_date=datetime(2026, 4, 21),
    schedule=None,
    catchup=False,
) as dag:

    extract = PythonOperator(
        task_id="extract_articles",
        python_callable=extract_articles
    )

    transform = PythonOperator(
        task_id="transform_articles",
        python_callable=transform_articles
    )

    load = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_to_postgres
    )

    extract >> transform >> load