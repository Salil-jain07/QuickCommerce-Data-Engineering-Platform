# QuickCommerce Data Engineering Platform

**Live Demo:** [Open QuickCommerce Dashboard](https://quickcommerce-data-engineering-platform.onrender.com)

An end-to-end data engineering platform that simulates large-scale quick-commerce operations inspired by Blinkit, Swiggy Instamart, and Flipkart Minutes.

The project demonstrates how large volumes of synthetic transactional data can be generated, ingested, stored, transformed, validated, and converted into analytics-ready datasets using a modern cloud-based data engineering architecture.

It implements a multi-layer data lake architecture (Bronze, Silver, and Gold), DuckDB-based transformations, Google Cloud Storage for data lake storage, Neon PostgreSQL as an analytical warehouse, and an interactive Streamlit dashboard for business analytics.

Apache Airflow orchestrates the local Bronze-to-Silver-to-Gold ETL pipeline, while a separate GitHub Actions workflow automates the cloud warehouse process.

> **Data disclaimer:** All transaction, customer, product, store, payment, and delivery records are synthetically generated. They do not represent actual business transactions or customer information from Blinkit, Swiggy Instamart, or Flipkart Minutes.

---

## Table of Contents

1. Project Overview
2. Project Goals
3. Architecture
4. Technology Stack
5. Dataset and Data Scale
6. Data Lake Architecture
7. ETL Pipeline
8. Data Quality and Validation
9. Analytics Warehouse
10. Business Analytics and Dashboard
11. Pipeline Automation
12. Docker Deployment
13. Project Structure
14. Environment Configuration
15. Running the Project
16. Current Implementation Status
17. Design Decisions
18. Current Limitations
19. Future Improvements
20. Security
21. Author

---

## 1. Project Overview

Quick-commerce platforms process large volumes of orders, payments, inventory movements, and deliveries across multiple stores and geographical locations.

This project simulates that environment by generating synthetic quick-commerce datasets and processing them through an end-to-end data engineering pipeline.

The platform follows a layered data architecture:

- **Bronze Layer:** Stores raw datasets in Google Cloud Storage.
- **Silver Layer:** Cleans, validates, and transforms raw data using DuckDB.
- **Gold Layer:** Produces aggregated and analytics-ready Parquet datasets.
- **Data Warehouse:** Loads curated analytical datasets into Neon PostgreSQL.
- **Analytics Layer:** Provides SQL-based analytical views.
- **Visualization Layer:** Presents business insights through an interactive Streamlit dashboard.

The objective is to demonstrate practical data engineering concepts, including cloud storage, ETL development, large-scale data processing, data quality validation, analytical modeling, workflow automation, and containerization.

## 2. Project Goals

- Generate realistic synthetic quick-commerce transactional data.
- Process millions of records through an ETL pipeline.
- Implement a Bronze, Silver, and Gold data lake architecture.
- Store raw and processed datasets in Google Cloud Storage.
- Use DuckDB for efficient analytical transformations.
- Store processed data in compressed Parquet format.
- Implement data quality checks at different pipeline stages.
- Build an analytical warehouse using Neon PostgreSQL.
- Create reusable SQL views for business analytics.
- Develop an interactive Streamlit dashboard.
- Orchestrate ETL transformations and validation using Apache Airflow.
- Automate the separate cloud warehouse workflow using GitHub Actions.
- Containerize the dashboard using Docker.

## 3. Architecture

The QuickCommerce Data Engineering Platform follows a cloud-based data lake and analytical warehouse architecture. It simulates quick-commerce operations across Blinkit, Swiggy Instamart, and Flipkart Minutes using synthetic datasets.

The platform uses Medallion Architecture (Bronze, Silver, and Gold) to organize data from raw ingestion to cleaned datasets and analytics-ready aggregations.

### 3.1 High-Level Architecture

```text
             SYNTHETIC DATA GENERATION
                        |
                        v
                 RAW CSV DATASETS
                        |
                        v
                  DATA INGESTION
                        |
                        v
              GOOGLE CLOUD STORAGE
                  BRONZE LAYER
                        |
                        v
               AIRFLOW ORCHESTRATION
                  13 TASKS / DAG
                        |
                        v
                DUCKDB TRANSFORMATIONS
                        |
                        v
                   SILVER LAYER
              Cleaned Parquet Data
                        |
                        v
                DUCKDB TRANSFORMATIONS
                        |
                        v
                    GOLD LAYER
             Aggregated Parquet Data
                        |
             +----------+----------+
             |                     |
             v                     v
      GOOGLE CLOUD STORAGE    GITHUB ACTIONS
         SILVER / GOLD              |
                                   v
                           NEON POSTGRESQL
                            DATA WAREHOUSE
                                   |
                                   v
                            ANALYTICAL VIEWS
             |                     |
             +----------+----------+
                        |
                        v
                STREAMLIT DASHBOARD
                        |
                        v
                 BUSINESS ANALYTICS
```

### 3.2 Data Orchestration with Apache Airflow

Apache Airflow 3.4.0 orchestrates the Bronze-to-Silver-to-Gold ETL workflow.

The DAG is named quickcommerce_etl_pipeline and is defined in:

`airflow/dags/quickcommerce_pipeline.py`

It contains 13 tasks connected through explicit dependencies:

1. `transform_customers`
2. `transform_orders`
3. `transform_products`
4. `transform_stores`
5. `transform_order_items`
6. `transform_payments`
7. `transform_deliveries`
8. `verify_silver`
9. `transform_gold_orders`
10. `transform_gold_sales`
11. `transform_gold_payments`
12. `transform_gold_deliveries`
13. `verify_gold`

Airflow provides:
- Centralized workflow orchestration.
- Task-level execution monitoring.
- Configurable retries for failed tasks.
- Dependency management between transformations.
- Manual execution through the Airflow web interface.
The current DAG uses `schedule=None`, meaning it is triggered manually rather than running on a recurring schedule. This is appropriate for the current fixed historical dataset.

The Airflow DAG handles Silver and Gold transformations and their validation. It does not load data into Neon PostgreSQL; that responsibility belongs to the separate GitHub Actions warehouse workflow.

### 3.3 Warehouse Automation with GitHub Actions

GitHub Actions manages a separate cloud warehouse workflow.

Its responsibilities include:
1. Checking out the project repository.
2. Setting up the Python environment.
3. Installing project dependencies.
4. Authenticating with Google Cloud.
5. Executing the configured Silver and Gold transformation workflow.
6. Validating transformed datasets.
7. Connecting to Neon PostgreSQL.
8. Creating warehouse schemas and tables.
9. Loading selected Gold datasets.
10. Creating analytical SQL views.
11. Verifying warehouse data.
12. Testing analytical views.

The GitHub Actions workflow is separate from the local Airflow DAG. It is responsible for the configured cloud warehouse process.

The workflow is defined in:

`.github/workflows/quickcommerce_pipeline.yml`

It supports manual execution using `workflow_dispatch`. Google Cloud authentication is configured through Workload Identity Federation (WIF), and the GitHub-hosted workflow has been successfully executed against the configured GCS bucket and Neon PostgreSQL warehouse.

### 3.4 Cloud Data Storage and Analytics

Google Cloud Storage acts as the data lake and stores Bronze, Silver, and Gold Parquet datasets.

DuckDB performs analytical transformations using SQL and processes Parquet data efficiently.

Neon PostgreSQL serves as the cloud analytical warehouse. Selected curated Gold datasets are loaded into warehouse tables, and SQL views provide an additional layer for dashboard analytics.

The detailed order-level Gold dataset remains in Parquet format in Google Cloud Storage rather than being fully loaded into PostgreSQL.

### 3.5 Application and Container Architecture

Docker Compose manages the local application services:
- Dashboard service: Runs the Streamlit analytics application on port 8501.
- Airflow service: Runs the Airflow standalone environment and exposes its web interface on port 8080.
The services run in separate containers and use the required project data and configuration through Docker volumes and environment variables.

The local Docker environment requires the host machine and Docker services to remain running during execution.

## 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data generation and ETL development |
| Pandas | Data manipulation |
| DuckDB | Analytical transformations and processing |
| Apache Parquet | Columnar data storage |
| PyArrow | Parquet processing |
| Google Cloud Storage | Cloud data lake |
| Google Cloud Authentication | Secure cloud authentication |
| Neon PostgreSQL | Analytical data warehouse |
| SQLAlchemy | PostgreSQL connectivity |
| Psycopg | PostgreSQL data loading |
| Streamlit | Interactive dashboard |
| Plotly | Interactive visualizations |
| Apache Airflow | Local ETL orchestration |
| GitHub Actions | Cloud warehouse workflow automation |
| Docker | Dashboard and Airflow containerization |
| Git and GitHub | Version control and source code management |

---

## 5. Dataset and Data Scale

The project uses synthetically generated datasets representing different entities in a quick-commerce ecosystem.

The data generator produces records for:

- Customers
- Products
- Stores
- Orders
- Order items
- Payments
- Deliveries

### Dataset Scale

The implemented Silver layer contains approximately:

| Dataset | Records |
|---|---:|
| Customers | 1,000,000 |
| Products | 50,000 |
| Stores | 1,000 |
| Orders | 10,000,000 |
| Order Items | 30,000,938 |
| Payments | 10,000,000 |
| Deliveries | 10,000,000 |

**Total:** More than 51 million records across the Silver datasets.

The Gold layer produces four analytical datasets:

| Gold Dataset | Records |
|---|---:|
| Gold Order Summary | 10,000,000 |
| Gold Sales Summary | 24,084 |
| Gold Payment Summary | 120,420 |
| Gold Delivery Summary | 1,535,453 |

The Gold datasets are stored in Parquet format and uploaded to Google Cloud Storage.

The order summary retains detailed order-level information, while the other Gold datasets provide aggregated analytical data.

> The dataset is historical and synthetic. It is not a live transactional feed from an actual quick-commerce platform.

---

## 6. Data Lake Architecture

The project follows a Medallion-style architecture with three processing layers.

### 6.1 Bronze Layer – Raw Data

The Bronze layer stores the original generated datasets in Google Cloud Storage.

Responsibilities:

- Preserve the original source data.
- Maintain a centralized cloud storage location.
- Store raw data in Parquet format.
- Provide a consistent source for downstream transformations.

**Storage:** Private Google Cloud Storage bucket.

### 6.2 Silver Layer – Cleaned and Standardized Data

The Silver layer processes Bronze datasets using DuckDB.

Transformations include:

- Reading source Parquet files from Google Cloud Storage.
- Standardizing and transforming data.
- Handling data types.
- Validating important fields.
- Preparing structured datasets for analytical processing.
- Writing transformed datasets in Parquet format.
- Uploading processed files to Google Cloud Storage.

Silver datasets include customers, products, stores, orders, order items, payments, and deliveries.

### 6.3 Gold Layer – Analytics-Ready Data

The Gold layer creates business-oriented datasets from the Silver layer.

It produces:

1. **Gold Order Summary:** Detailed order-level analytical dataset.
2. **Gold Sales Summary:** Aggregated sales information.
3. **Gold Payment Summary:** Payment performance and transaction summaries.
4. **Gold Delivery Summary:** Delivery performance and operational summaries.

The Gold layer is designed to simplify downstream analytical queries and dashboard development.

---

## 7. ETL Pipeline

The ETL pipeline is implemented using Python and DuckDB.

The transformations are divided into individual scripts to maintain modularity and make each processing stage easier to understand and maintain.

### 7.1 Silver Transformations

The Silver pipeline processes the datasets sequentially:

| Execution Order | Script | Responsibility |
|---|---|---|
| 1 | `bronze_to_silver.py` | Customer transformation |
| 2 | `orders_to_silver.py` | Order transformation |
| 3 | `products_to_silver.py` | Product transformation |
| 4 | `stores_to_silver.py` | Store transformation |
| 5 | `order_items_to_silver.py` | Order item transformation |
| 6 | `payments_to_silver.py` | Payment transformation |
| 7 | `deliveries_to_silver.py` | Delivery transformation |
| 8 | `verify_silver.py` | Silver layer validation |

### 7.2 Gold Transformations

The Gold pipeline generates analytical datasets:

| Execution Order | Script | Responsibility |
|---|---|---|
| 1 | `orders_to_gold.py` | Generate order-level Gold dataset |
| 2 | `sales_to_gold.py` | Generate sales summary |
| 3 | `payments_to_gold.py` | Generate payment summary |
| 4 | `deliveries_to_gold.py` | Generate delivery summary |
| 5 | `verify_gold.py` | Validate Gold layer outputs |

DuckDB is used for analytical processing, while Parquet provides efficient columnar storage.

The transformation scripts share a DuckDB database and are executed from the transformations directory to maintain a consistent processing environment.

### 7.3 Cloud Storage Integration

Google Cloud Storage is used to store the Bronze, Silver, and Gold datasets.

The Python pipeline uses Google Cloud authentication and the appropriate storage libraries to access cloud objects.

The project uses Google Application Default Credentials for local cloud access.

For automated execution, GitHub Actions is configured to use Google Cloud Workload Identity Federation rather than relying on a permanent service-account JSON key.

---

## 8. Data Quality and Validation

Data quality is an important part of the ETL pipeline.

The project includes validation scripts to verify that transformations produce the expected outputs.

### Silver Layer Validation

The Silver validation stage checks the processed datasets and verifies their availability and expected structure.

### Gold Layer Validation

The Gold validation stage verifies that all required analytical Parquet files have been generated and uploaded to Google Cloud Storage.

### Warehouse Validation

The warehouse verification stage checks the expected row counts of the loaded analytical tables.

### Why Data Quality Matters

Without validation, a pipeline can complete execution while still producing incomplete or incorrect datasets.

Separating validation from transformation makes it easier to identify which processing stage has failed.

The project can be extended with additional checks for:

- Null values in critical columns.
- Duplicate business keys.
- Invalid quantities and monetary values.
- Referential integrity.
- Unexpected changes in record counts.
- Data freshness.
- Aggregation consistency.

---

## 9. Analytics Warehouse

Neon PostgreSQL is used as the analytical warehouse.

The warehouse stores selected Gold datasets that support business-level SQL analysis.

### Warehouse Tables

The project creates the following tables under the `quickcommerce` schema:

| Table | Description |
|---|---|
| `gold_order_summary` | Order-level analytical table |
| `gold_sales_summary` | Aggregated sales data |
| `gold_payment_summary` | Payment analytical data |
| `gold_delivery_summary` | Delivery analytical data |

The three aggregated Gold datasets are loaded into PostgreSQL.

The detailed 10-million-row Gold order dataset remains in Parquet format in Google Cloud Storage and is not fully loaded into the warehouse.

### Data Loading

The warehouse loading scripts use:

- SQLAlchemy and Psycopg for PostgreSQL connectivity.
- DuckDB for reading Parquet datasets.
- PostgreSQL `COPY` for efficient bulk loading.
- Batch processing to transfer records.

The loaders use transactions and rollback handling to avoid leaving partially loaded data after a failed load.

### Analytical SQL Views

The warehouse includes five analytical views:

| View | Purpose |
|---|---|
| `v_sales_kpis` | Overall sales performance indicators |
| `v_daily_sales_trend` | Daily sales trends |
| `v_payment_method_performance` | Payment method analysis |
| `v_delivery_city_performance` | City-level delivery analysis |
| `v_delivery_condition_performance` | Delivery condition analysis |

These views provide reusable SQL logic for the dashboard and business reporting.

---

## 10. Business Analytics and Dashboard

The project uses Streamlit and Plotly to present business insights through an interactive dashboard.

The dashboard connects the analytical warehouse with the detailed Gold order dataset.

### Business Analytics

The implemented analytics include:

- Total orders and sales performance.
- Average order value.
- Daily sales trends.
- Payment method performance.
- City-level delivery performance.
- Delivery condition analysis.
- Detailed order exploration.

### Dashboard

The Streamlit application provides a visual interface for exploring business metrics and order-level information.

The dashboard is containerized using Docker and can be run locally.

**Local dashboard URL:**

`http://localhost:8501`

The detailed order explorer uses the local Gold order-summary Parquet dataset, while the warehouse-backed analytics use Neon PostgreSQL.

---

## 11. Pipeline Automation

The project uses two separate automation mechanisms for different responsibilities:

- **Apache Airflow:** Orchestrates the local Bronze-to-Silver-to-Gold ETL pipeline.
- **GitHub Actions:** Runs the configured cloud warehouse workflow, including Neon PostgreSQL operations.

These workflows operate independently. The local Airflow DAG does not trigger the GitHub Actions workflow.

### 11.1 Apache Airflow ETL Orchestration

Apache Airflow 3.4.0 is used to manage dependencies and execution of the local ETL pipeline.

- DAG ID: `quickcommerce_etl_pipeline`
- DAG file: `airflow/dags/quickcommerce_pipeline.py`
- Trigger: Manual (`schedule=None`)

The DAG contains 13 tasks:

1. `transform_customers`
2. `transform_orders`
3. `transform_products`
4. `transform_stores`
5. `transform_order_items`
6. `transform_payments`
7. `transform_deliveries`
8. `verify_silver`
9. `transform_gold_orders`
10. `transform_gold_sales`
11. `transform_gold_payments`
12. `transform_gold_deliveries`
13. `verify_gold`

The tasks execute in dependency order. The pipeline uses task-level retries and sequential execution settings.

Airflow handles the local ETL transformations and GCS output verification. Neon warehouse loading is handled separately by GitHub Actions.

### 11.2 GitHub Actions Warehouse Workflow

GitHub Actions is used for the separate cloud warehouse workflow.

- Workflow file: `.github/workflows/quickcommerce_pipeline.yml`
- Trigger: Manual (`workflow_dispatch`)

The configured workflow covers:

1. Repository checkout and Python setup.
2. Dependency installation and Google Cloud authentication.
3. Silver and Gold transformation steps.
4. Data validation.
5. Neon PostgreSQL connectivity verification.
6. Warehouse schema and table creation.
7. Loading selected Gold datasets.
8. Analytical view creation and verification.

This workflow is independent of the local Airflow DAG.

### 11.3 Why Use Both?

The two tools serve different purposes:

- **Airflow** provides task dependencies, retries, execution monitoring, and orchestration for the local ETL pipeline.
- **GitHub Actions** provides repository-based automation for the cloud warehouse workflow.

This separation keeps ETL orchestration distinct from warehouse deployment and loading.

> **Implementation status:** The Airflow Docker image has been built, the container has been started, and the DAG has been detected with all 13 tasks. The DAG has not yet been executed. The GitHub Actions workflow has been locally validated for syntax and linting; cloud authentication and a successful GitHub-hosted end-to-end execution are still pending.

---

## 12. Docker Deployment

Docker Compose is used to containerize and manage the project's local services.

The project runs two services:

| Service | Purpose | Local URL |
|---|---|---|
| `dashboard` | Streamlit analytics dashboard | `http://localhost:8501` |
| `airflow` | ETL orchestration and DAG monitoring | `http://localhost:8080` |

### 12.1 Docker Configuration

The project includes:

- `Dockerfile` for building the Streamlit dashboard image.
- `airflow/Dockerfile` for building the Apache Airflow image.
- `docker-compose.yml` for managing both services.
- `.dockerignore` for excluding unnecessary files from the dashboard build context.

Generated datasets and local DuckDB database files are excluded from the dashboard build context. Required datasets and project directories are mounted into the respective containers at runtime.

### 12.2 Build Docker Images

Build both service images:

```bash
docker compose build dashboard airflow
12.3 Start Services
Start the dashboard and Airflow:
docker compose up -d dashboard airflow


12.4 Check Running Containers
Verify the service status:
docker compose ps


12.5 Access the Applications
- Streamlit dashboard: http://localhost:8501
- Apache Airflow UI: http://localhost:8080
12.6 View Container Logs
Dashboard logs:
docker compose logs -f dashboard


Airflow logs:
docker compose logs -f airflow


12.7 Stop Services
Stop and remove the running containers:
docker compose down


Important: The dashboard and locally hosted Airflow require the host machine, WSL, and Docker to remain running. Local Airflow DAG execution cannot continue when the laptop is switched off. Cloud resources such as Google Cloud Storage and Neon PostgreSQL are hosted separately.


## 13. Project Structure

QuickCommerce-Data-Engineering-Platform/
│
├── .github/
│   └── workflows/
│       └── quickcommerce_pipeline.yml
│
├── airflow/
│   ├── dags/
│   │   └── quickcommerce_pipeline.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── backend/
│   ├── config/
│   │   └── config.py
│   │
│   ├── ingestion/
│   │   ├── test_gcs_connection.py
│   │   ├── upload_to_gcs.py
│   │   └── verify_gcs_upload.py
│   │
│   ├── transformations/
│   │   ├── bronze_to_silver.py
│   │   ├── orders_to_silver.py
│   │   ├── products_to_silver.py
│   │   ├── stores_to_silver.py
│   │   ├── order_items_to_silver.py
│   │   ├── payments_to_silver.py
│   │   ├── deliveries_to_silver.py
│   │   ├── verify_silver.py
│   │   ├── orders_to_gold.py
│   │   ├── sales_to_gold.py
│   │   ├── payments_to_gold.py
│   │   ├── deliveries_to_gold.py
│   │   └── verify_gold.py
│   │
│   └── warehouse/
│       ├── test_neon_connection.py
│       ├── create_schema.py
│       ├── create_warehouse_tables.py
│       ├── load_gold_sales.py
│       ├── load_gold_payments.py
│       ├── load_gold_deliveries.py
│       ├── create_analytics_views.py
│       ├── verify_warehouse.py
│       ├── test_analytics_views.py
│       ├── check_warehouse_storage.py
│       └── inspect_gold_schema.py
│
├── datasets/
│   └── data_generator/
│       ├── config.py
│       ├── generate_customers.py
│       ├── generate_products.py
│       ├── generate_stores.py
│       ├── generate_orders.py
│       ├── generate_order_items.py
│       ├── generate_payments.py
│       ├── generate_deliveries.py
│       └── validate_master_data.py
│
├── docs/
│
├── frontend/
│   ├── app.py
│   └── pages/
│       ├── dashboard.py
│       └── order_explorer.py
│
├── main.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-etl.txt
├── .dockerignore
├── .gitignore
├── .env.example
└── README.md

Generated datasets, local DuckDB files, credentials, and Python virtual environments are intentionally excluded from version control.

---

## 14. Environment Configuration

The project uses environment variables to manage cloud and database configuration.

Create a `.env` file in the project root using `.env.example` as a reference.

Required configuration includes:

```env
# Google Cloud
GCP_PROJECT_ID=your_gcp_project_id
GCS_BUCKET_NAME=your_gcs_bucket_name

# Neon PostgreSQL
DATABASE_URL=your_neon_database_url

# Pipeline configuration
BATCH_SIZE=10000
```

The project also uses `GCS_REGION` where required by the cloud configuration.

Never commit the actual `.env` file or any cloud credentials.

### Python Environment

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Activate it on Linux or WSL:

```bash
source .venv/bin/activate
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

For ETL-only execution:

```bash
pip install -r requirements-etl.txt
```

---

## 15. Running the Project

The following describes the major execution stages.

### Step 1: Generate Synthetic Data

Run the data generation scripts inside:

```text
datasets/data_generator/
```

The generated datasets provide the source data for the pipeline.

### Step 2: Configure Google Cloud Storage

Configure Google Cloud authentication and ensure that the required GCS bucket is accessible.

The bucket is private and should be accessed using authorized credentials.

### Step 3: Run the ETL Pipeline with Apache Airflow

Start the Airflow service:

```bash
docker compose up -d airflow
```

Open the Airflow web interface:

```text
http://localhost:8080
```

Locate the DAG `quickcommerce_etl_pipeline` and trigger it manually. The DAG orchestrates the Silver transformations, Silver validation, Gold transformations, and Gold validation in the configured dependency order.

Monitor task execution and logs through the Airflow interface.

### Optional: Run Transformations Manually

For debugging or individual transformation testing, the scripts can also be executed manually in their defined order from:

```text
backend/transformations/
```

The scripts share a local DuckDB database, so preserve their execution order. Run the Silver and Gold validation scripts after their respective transformation stages.

### Step 4: Configure Neon PostgreSQL

Provide the Neon connection string through `DATABASE_URL`.

### Step 5: Create the Warehouse

Execute the warehouse scripts to:

- Create the `quickcommerce` schema.
- Create the Gold warehouse tables.
- Load the aggregated Gold datasets.
- Create analytical SQL views.
- Verify the loaded data.

### Step 6: Run the Dashboard

Start the Streamlit dashboard using Docker Compose or the appropriate Streamlit application command.

The dashboard requires access to the configured warehouse and the detailed Gold Parquet dataset.

> Reproducing the full pipeline requires access to the private GCS bucket and a configured Neon database. The GitHub Actions cloud deployment additionally requires GitHub repository secrets and Google Cloud Workload Identity Federation configuration.

---

## 16. Current Implementation Status

| Component | Status |
|---|---|
| Project structure | Completed |
| Synthetic data generation | Implemented |
| Google Cloud Storage integration | Implemented |
| Bronze layer storage | Implemented |
| Silver transformations | Implemented |
| Gold transformations | Implemented |
| Parquet data storage | Implemented |
| Silver validation | Implemented |
| Gold validation | Implemented |
| Neon PostgreSQL connection | Implemented |
| Warehouse schema and tables | Implemented |
| Gold sales loading | Implemented |
| Gold payment loading | Implemented |
| Gold delivery loading | Implemented |
| Analytical SQL views | Implemented |
| Warehouse verification | Implemented |
| Streamlit dashboard | Implemented |
| Docker dashboard deployment | Built and locally tested |
| Apache Airflow Docker service | Built and locally tested |
| Airflow ETL DAG (13 tasks) | Configured and detected; execution pending |
| GitHub Actions workflow | Created and locally validated |
| GitHub-hosted end-to-end execution | Pending |
| Workload Identity Federation setup | Pending |

---

## 17. Design Decisions

### Parquet for Data Lake Storage

Parquet was selected because it provides columnar storage, compression, and efficient analytical reads.

It is particularly suitable for large datasets that are frequently queried by analytical engines.

### DuckDB for Transformations

DuckDB provides an analytical SQL engine that can process Parquet datasets efficiently without requiring a separate distributed processing cluster.

It also allows the project to perform substantial data transformations using a lightweight local processing engine.

### Google Cloud Storage for the Data Lake

GCS provides centralized cloud object storage for the different data lake layers.

It separates data storage from the local processing environment.

### Neon PostgreSQL for the Warehouse

Neon provides a managed PostgreSQL environment for storing curated analytical datasets and exposing reusable SQL views.

### Apache Airflow for ETL Orchestration and GitHub Actions for Warehouse Automation

Apache Airflow orchestrates the local Bronze-to-Silver-to-Gold ETL pipeline. It manages task dependencies, sequential execution, retries, and pipeline monitoring.

GitHub Actions handles the separate cloud warehouse workflow, including the configured Neon PostgreSQL loading and validation process.

This separation assigns ETL orchestration and cloud warehouse automation to dedicated tools.

### Docker for Dashboard Deployment

Docker provides a consistent environment for running the dashboard and makes local deployment easier.

---

## 18. Current Limitations

- The project uses synthetic historical data rather than a live production data feed.
- The current pipeline is designed primarily for batch processing.
- Airflow currently runs locally in Docker and requires the host machine to remain available during DAG execution.
- The Airflow DAG is manually triggered and has not yet completed a full execution.
- The GitHub Actions workflow has not yet completed a full cloud execution.
- Cloud authentication for GitHub Actions requires Workload Identity Federation configuration.
- The detailed Gold order dataset remains in Parquet rather than being fully loaded into PostgreSQL.
- The order explorer depends on access to the local Gold Parquet dataset.
- GitHub Actions hosted runners have finite memory, execution time, and disk capacity, so large-scale ETL execution must be validated in that environment.
- Advanced incremental processing and change-data capture are not part of the current implementation.
- Pipeline monitoring and alerting can be expanded.

---

## 19. Future Improvements

- Complete GitHub Actions cloud authentication and end-to-end execution.
- Add scheduled pipeline execution where required.
- Improve incremental ETL processing.
- Introduce more comprehensive automated data quality tests.
- Add pipeline execution history and failure notifications.
- Improve dashboard performance for large order-level datasets.
- Implement partition pruning and more efficient Parquet reads.
- Add data freshness and pipeline monitoring metrics.
- Deploy Apache Airflow in a managed or remote environment to support cloud-hosted orchestration independent of the developer laptop.
- Expand business analytics with inventory optimization, customer segmentation, and demand forecasting.

---

## 20. Security

Security is important because the project integrates cloud storage and a managed database.

The following practices are followed:

- Keep the Google Cloud Storage bucket private.
- Store database credentials in environment variables.
- Exclude `.env` from Git.
- Never commit service-account private keys or cloud credentials.
- Use GitHub repository secrets for sensitive workflow configuration.
- Use Workload Identity Federation for GitHub Actions authentication rather than a long-lived service-account JSON key.
- Apply appropriate access permissions to cloud resources.
- Exclude generated datasets and local database files from source control.

---

## 21. Author

**Salil Jain**

Data Engineering Project

---

*This project is developed for learning and portfolio demonstration purposes. All generated business data is synthetic.*
