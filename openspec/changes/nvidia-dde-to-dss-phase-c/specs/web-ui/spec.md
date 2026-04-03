## ADDED Requirements

### Requirement: Web UI Homepage
系統 SHALL 提供首頁展示最近審查記錄，讓使用者快速了解系統狀態。

#### Scenario: Display recent reviews
- **WHEN** user visits `/`
- **THEN** system displays the 10 most recent review records with project name, status, and timestamp

#### Scenario: Empty state handling
- **WHEN** no reviews exist in database
- **THEN** system displays friendly message indicating no reviews yet

### Requirement: Review Submission Page
系統 SHALL 提供表單讓使用者提交新審查，包含專案名稱與規格輸入欄位。

#### Scenario: Submit new review
- **WHEN** user fills project name and specification at `/review/new`
- **THEN** system creates review task and redirects to progress page

#### Scenario: Form validation
- **WHEN** user submits form without required fields
- **THEN** system displays validation errors and prevents submission

### Requirement: Review Detail Page
系統 SHALL 提供審查詳情頁面，以可視化方式展示完整 JSON 結果。

#### Scenario: View review details
- **WHEN** user visits `/review/{id}`
- **THEN** system displays complete review result with collapsible JSON viewer

#### Scenario: Review not found
- **WHEN** requested review ID does not exist
- **THEN** system displays 404 error page

### Requirement: Knowledge Base Browser
系統 SHALL 提供知識庫唯讀瀏覽頁面，展示現有風險模板與角色定義。

#### Scenario: Browse knowledge base
- **WHEN** user visits `/knowledge`
- **THEN** system displays list of available knowledge files organized by category

#### Scenario: View knowledge file
- **WHEN** user selects a knowledge file
- **THEN** system displays file content in readable format

### Requirement: Async Review Progress
系統 SHALL 在背景執行審查任務，並在網頁上顯示即時進度。

#### Scenario: Track review progress
- **WHEN** review is processing in background
- **THEN** system displays progress indicator with status updates

#### Scenario: Review completion notification
- **WHEN** review completes
- **THEN** system notifies user and provides link to view results
