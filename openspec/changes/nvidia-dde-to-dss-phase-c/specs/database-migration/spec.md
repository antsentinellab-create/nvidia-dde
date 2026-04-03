## ADDED Requirements

### Requirement: SQLite to PostgreSQL Migration Script
系統 SHALL 提供遷移腳本將現有 SQLite history.db 資料轉移至 PostgreSQL。

#### Scenario: Execute migration
- **WHEN** `python db/migrate.py` is run with PostgreSQL configured
- **THEN** system reads all records from SQLite and inserts into PostgreSQL

#### Scenario: Data integrity check
- **WHEN** migration completes
- **THEN** system verifies record counts match between source and destination

#### Scenario: Handle existing data
- **WHEN** PostgreSQL already has data
- **THEN** migration aborts with error to prevent data loss

### Requirement: Schema Compatibility
系統 SHALL 確保 PostgreSQL schema 與 SQLite 相容，支援相同的查詢操作。

#### Scenario: Create PostgreSQL schema
- **WHEN** migration runs for first time
- **THEN** system creates tables with PostgreSQL-compatible types

#### Scenario: Preserve data types
- **WHEN** migrating datetime fields
- **THEN** timestamps maintain timezone information

### Requirement: Rollback Capability
系統 SHALL 提供回滾機制，在遷移失敗時恢復原狀。

#### Scenario: Backup before migration
- **WHEN** migration starts
- **THEN** system creates backup of SQLite database

#### Scenario: Restore from backup
- **WHEN** migration fails
- **THEN** system can restore from backup file

### Requirement: Zero-Downtime Migration
系統 SHALL 支援在不中斷服務的情況下完成遷移。

#### Scenario: Read-only mode
- **WHEN** migration begins
- **THEN** system sets SQLite to read-only to prevent new writes

#### Scenario: Switch to PostgreSQL
- **WHEN** migration completes successfully
- **THEN** system atomically switches DATABASE_URL to PostgreSQL
