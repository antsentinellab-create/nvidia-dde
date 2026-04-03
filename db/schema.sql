-- Design Review Support System 資料庫結構
-- 版本：1.0
-- 建立日期：2026-04-03

-- 審查歷史記錄表
CREATE TABLE IF NOT EXISTS reviews (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project     TEXT NOT NULL,        -- 專案名稱
    reviewed_at TEXT NOT NULL,        -- ISO8601 時間戳
    risk_high   INTEGER DEFAULT 0,    -- 高風險數量
    risk_medium INTEGER DEFAULT 0,    -- 中風險數量
    risk_low    INTEGER DEFAULT 0,    -- 低風險數量
    verdict     TEXT,                 -- Aggregator 最終裁決摘要
    result_json TEXT NOT NULL,        -- 完整 Aggregator JSON（用於詳細查詢）
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引：加速查詢
CREATE INDEX IF NOT EXISTS idx_reviews_reviewed_at ON reviews(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_reviews_project ON reviews(project);
CREATE INDEX IF NOT EXISTS idx_reviews_risk_high ON reviews(risk_high);

-- 觸發程序：自動更新 updated_at
CREATE TRIGGER IF NOT EXISTS update_reviews_updatedat 
AFTER UPDATE ON reviews
BEGIN
    UPDATE reviews SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
