````md
# 📰 Wired Data Pipeline (Big Data Infrastructure)

Project ini merupakan implementasi pipeline data end-to-end untuk mengambil, memproses, dan menyimpan data artikel dari Wired.com menggunakan teknologi Big Data.

---

## 🚀 Tools & Teknologi

- Python 3.11
- Selenium (Web Scraping)
- FastAPI (API Service)
- Docker & Docker Compose
- Apache Airflow (Orchestration)
- PostgreSQL (Database)
- SQL (Reporting)

---

## 🔄 Alur Pipeline

```text
Scraping → JSON/CSV → FastAPI → Airflow DAG → PostgreSQL → SQL Query
````

## Cara Menjalankan Program

### Aktifkan Virtual Environment

```bash
.\.venv\Scripts\activate
```

---

### Jalankan FastAPI

```bash
uvicorn api.main:app --reload
```

Akses API:

```
http://127.0.0.1:8000/articles
```

---

### Jalankan Docker (Airflow + PostgreSQL)

```bash
docker compose up -d
```

Akses Airflow:

```
http://localhost:8088
```

Login:

```
username: admin
password: admin
```

---

### Jalankan DAG

* Masuk ke Airflow UI
* Aktifkan DAG `wired_pipeline_dag`
* Klik **Trigger DAG**

---

### Cek Database

Connect ke PostgreSQL:

```
Host: localhost
Port: 5441
User: etl_user
Password: etl_pass
Database: responsi_ipbd
```

---

## Query SQL (Reporting)

### 1. Clean Author

```sql
SELECT
    title,
    TRIM(REPLACE(author, 'By', '')) AS clean_author
FROM wired_articles;
```

---

### 2. Top 3 Author

```sql
SELECT
    TRIM(REPLACE(author, 'By', '')) AS clean_author,
    COUNT(*) AS total_articles
FROM wired_articles
GROUP BY clean_author
ORDER BY total_articles DESC
LIMIT 3;
```

---

### 3. Keyword Search

```sql
SELECT
    title,
    author,
    description
FROM wired_articles
WHERE
    title ILIKE '%AI%' OR
    title ILIKE '%Climate%' OR
    title ILIKE '%Security%' OR
    description ILIKE '%AI%' OR
    description ILIKE '%Climate%' OR
    description ILIKE '%Security%';
```

---

## 🧠 Langkah Singkat yang Dilakukan

1. Melakukan scraping artikel dari Wired menggunakan Selenium
2. Menyimpan data ke format JSON dan CSV
3. Membuat API menggunakan FastAPI (`GET /articles`)
4. Setup Airflow dan PostgreSQL menggunakan Docker
5. Membuat DAG untuk:

   * Extract data dari API
   * Transform format tanggal
   * Load ke database PostgreSQL
6. Menjalankan query SQL untuk analisis data

````