## ADDED Requirements

### Requirement: Background Task Execution
系統 SHALL 使用非同步方式在背景執行審查任務，避免阻塞 Web 請求。

#### Scenario: Submit async review
- **WHEN** user submits review via web form
- **THEN** system queues task and immediately returns response with task ID

#### Scenario: Task processing
- **WHEN** task is in queue
- **THEN** background worker processes task without blocking HTTP requests

### Requirement: Task Queue Management
系統 SHALL 實作簡單的任務佇列機制來管理背景審查工作。

#### Scenario: Queue creation
- **WHEN** server starts
- **THEN** task queue is initialized and ready to accept jobs

#### Scenario: Add task to queue
- **WHEN** new review is submitted
- **THEN** task is added to queue with unique ID

#### Scenario: Task status tracking
- **WHEN** user queries task status
- **THEN** system returns current state: pending, processing, completed, or failed

### Requirement: Progress Reporting
系統 SHALL 提供任務執行進度資訊給前端顯示。

#### Scenario: Update progress
- **WHEN** review engine processes each role
- **THEN** task updates progress percentage and current stage

#### Scenario: Polling for updates
- **WHEN** frontend polls /task/{id}/status endpoint
- **THEN** system returns current progress and status

### Requirement: Concurrent Task Limits
系統 SHALL 限制同時執行的審查任務數量以避免資源耗盡。

#### Scenario: Max concurrent tasks
- **WHEN** max_workers (default 3) tasks are running
- **THEN** new tasks wait in queue until worker becomes available

#### Scenario: Configurable worker count
- **WHEN** MAX_WORKERS environment variable is set
- **THEN** system uses specified number of workers
