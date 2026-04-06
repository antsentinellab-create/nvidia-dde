## ADDED Requirements

### Requirement: SQLAlchemy ORM Models
系統 SHALL 使用 SQLAlchemy ORM 抽象資料庫操作，支援 PostgreSQL 與 SQLite 雙重後端。

#### Scenario: Define Review model
- **WHEN** application starts
- **THEN** SQLAlchemy Review model is defined with columns: id, project_name, specification, result, created_at

#### Scenario: Database abstraction
- **WHEN** repository methods are called
- **THEN** same interface works for both PostgreSQL and SQLite backends

### Requirement: Environment-Based Database Selection
系統 SHALL 透過環境變數 `DATABASE_URL` 控制資料庫連接，預設使用 SQLite。

#### Scenario: Default to SQLite
- **WHEN** DATABASE_URL is not set
- **THEN** system uses `sqlite:///db/history.db` as default

#### Scenario: Use PostgreSQL when configured
- **WHEN** DATABASE_URL is set to PostgreSQL connection string
- **THEN** system connects to PostgreSQL database

#### Scenario: SQLite fallback
- **WHEN** PostgreSQL connection fails
- **THEN** system logs warning and falls back to SQLite (optional based on configuration)

### Requirement: Repository ORM Migration
系統 SHALL 將現有 repository.py 方法改為 SQLAlchemy ORM 操作，保持 API 不變。

#### Scenario: Create review
- **WHEN** `create_review()` is called
- **THEN** SQLAlchemy session adds and commits new Review object

#### Scenario: Get reviews
- **WHEN** `get_reviews(limit)` is called
- **THEN** SQLAlchemy query returns list of Review objects ordered by created_at DESC

#### Scenario: Get review by ID
- **WHEN** `get_review_by_id(id)` is called
- **THEN** SQLAlchemy query returns single Review object or None

### Requirement: Connection Pool Management
系統 SHALL 配置適當的資料庫連線池參數以支援多人並發訪問。

#### Scenario: Configure pool size
- **WHEN** using PostgreSQL
- **THEN** connection pool size is set to 10 with max_overflow of 20

#### Scenario: Handle concurrent writes
- **WHEN** multiple users submit reviews simultaneously
- **THEN** connection pool manages concurrent sessions without errors
