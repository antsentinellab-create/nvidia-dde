## ADDED Requirements

### Requirement: Git Repository Synchronization
系統 SHALL 支援從遠端 Git 倉庫同步 knowledge/ 目錄。

#### Scenario: Pull from remote repository
- **WHEN** `pull_knowledge(remote_url)` is called
- **THEN** system fetches latest changes from remote and merges into local knowledge/ directory

#### Scenario: Push to remote repository
- **WHEN** `push_knowledge(remote_url)` is called
- **THEN** system commits local changes and pushes to remote repository

#### Scenario: Handle merge conflicts
- **WHEN** pull encounters merge conflicts
- **THEN** system aborts merge and reports conflict files to user

### Requirement: CLI Knowledge Sync Menu
系統 SHALL 在 CLI 知識庫選單新增 [3-6] 同步選項。

#### Scenario: Display sync submenu
- **WHEN** user selects [3-6] in knowledge management menu
- **THEN** system shows pull/push options

#### Scenario: Execute pull
- **WHEN** user selects pull option with remote URL
- **THEN** system executes pull_knowledge() and displays result

#### Scenario: Execute push
- **WHEN** user selects push option with remote URL
- **THEN** system executes push_knowledge() and displays result

### Requirement: Remote URL Configuration
系統 SHALL 允許透過環境變數或配置文件指定遠端 Git 倉庫 URL。

#### Scenario: Use environment variable
- **WHEN** KNOWLEDGE_REMOTE_URL is set
- **THEN** system uses this URL as default remote

#### Scenario: Manual URL input
- **WHEN** user provides URL via CLI prompt
- **THEN** system uses provided URL for current operation

### Requirement: Git Authentication Support
系統 SHALL 支援基本的 Git 認證方式（SSH keys 或 HTTPS credentials）。

#### Scenario: SSH key authentication
- **WHEN** remote uses SSH URL and ~/.ssh/id_rsa exists
- **THEN** system authenticates using SSH key

#### Scenario: HTTPS authentication
- **WHEN** remote uses HTTPS URL
- **THEN** system uses git credential helper for authentication
