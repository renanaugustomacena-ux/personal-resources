# Capstone — Data Engineering e Scienza dei Dati

## Progetto Finale

**Obiettivo**: Costruire una pipeline dati completa che integri tutti i pilastri della encyclopedia.

## Requisiti

### Infrastruttura
- PostgreSQL come source database
- MongoDB per document store
- Apache Kafka per event streaming
- ClickHouse per analytics
- dbt + Airflow per orchestrazione

### Pipeline
1. CDC da PostgreSQL via Debezium → Kafka
2. Spark Streaming per elaborazione
3. Data quality checks con Great Expectations
4. dbt transformations
5. ClickHouse per OLAP queries

### Security & Compliance
- RBAC implementation
- Column-level encryption
- Audit logging
- GDPR compliance (right to erasure, data portability)

### Output
- Infrastructure as Code (Terraform/Pulumi)
- Docker containers
- Monitoring con Prometheus/Grafana
- Documentation operative

## Valutazione
- Pipeline funzionante end-to-end
- Test coverage > 80%
- Runbook per operazioni
- Post-mortem template