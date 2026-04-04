/**
 * 統一前端日誌工具（與後端 JSON 格式一致）
 * 
 * 格式規範：
 * {
 *   "ts": "2026-03-16T02:04:22+0800",      // ISO 8601 時間戳記
 *   "lvl": "INFO",                          // 日誌層級 (INFO/WARN/ERROR)
 *   "script": "filename.js",                // 腳本檔案名稱
 *   "fn": "functionName",                   // 函數名稱
 *   "msg": "日誌訊息",                       // 日誌訊息
 *   "extra": {},                            // 額外結構化資料（可選）
 *   "elapsed_ms": 141                       // 執行耗時（毫秒）
 * }
 */

// 全域起始時間（用於計算 elapsed_ms）
const __LOG_START_TIME__ = performance.now();

/**
 * 輸出 JSON 格式日誌
 * @param {string} level - 日誌層級 (info/warn/error)
 * @param {string} msg - 日誌訊息
 * @param {Object} extra - 額外結構化資料
 * @param {string} scriptName - 腳本檔案名稱（可選，預設從呼叫堆疊獲取）
 * @param {string} fnName - 函數名稱（可選，預設從呼叫堆疊獲取）
 */
function log(level, msg, extra = {}, scriptName = null, fnName = null) {
    // 獲取時間戳記（ISO 8601 格式 + 時區）
    const timestamp = new Date().toISOString().replace(/\.\d{3}Z/, '+0800');
    
    // 嘗試從呼叫堆疊獲取 script 和 fn 名稱
    let script = scriptName || 'unknown';
    let fn = fnName || 'anonymous';
    
    if (!scriptName || !fnName) {
        try {
            const stackLines = new Error().stack.split('\n');
            // 跳過 log() 本身和 call stack 的前幾行
            const callerLine = stackLines[2] || stackLines[1];
            if (callerLine) {
                // 解析堆疊資訊：at functionName (http://.../script.js:line:col)
                const match = callerLine.match(/at\s+(\S+)\s+\(([^)]+)\)/) || 
                             callerLine.match(/at\s+([^)]+)/);
                if (match) {
                    if (!fnName && match[1] && match[1] !== '') {
                        fn = match[1].replace('global code', 'global');
                    }
                    if (!scriptName && match[2]) {
                        const urlMatch = match[2].match(/([^\/]+\.(js|html))(?::\d+:\d+)/);
                        if (urlMatch) {
                            script = urlMatch[1];
                        }
                    }
                }
            }
        } catch (e) {
            // 如果無法解析堆疊，使用預設值
        }
    }
    
    // 計算耗時
    const elapsed = Math.round(performance.now() - __LOG_START_TIME__);
    
    // 建立日誌物件
    const logEntry = {
        ts: timestamp,
        lvl: level.toUpperCase(),
        script: script,
        fn: fn,
        msg: msg,
        extra: extra,
        elapsed_ms: elapsed
    };
    
    // 輸出 JSON 格式日誌
    const logStr = JSON.stringify(logEntry, null, 2);
    
    // 根據層級輸出到不同的 console
    switch (level.toLowerCase()) {
        case 'error':
            console.error(logStr);
            break;
        case 'warn':
            console.warn(logStr);
            break;
        case 'info':
            console.info(logStr);
            break;
        default:
            console.log(logStr);
    }
    
    return logEntry;
}

/**
 * 便捷函數：INFO 層級日誌
 */
function logInfo(msg, extra = {}) {
    return log('info', msg, extra);
}

/**
 * 便捷函數：WARN 層級日誌
 */
function logWarn(msg, extra = {}) {
    return log('warn', msg, extra);
}

/**
 * 便捷函數：ERROR 層級日誌
 */
function logError(msg, extra = {}) {
    return log('error', msg, extra);
}

/**
 * 便捷函數：任務開始日誌
 */
function logTaskStart(taskId, projectName = '') {
    return log('info', `🚀 開始執行任務：${taskId}`, {
        task_id: taskId,
        project: projectName,
        stage: '',
        progress: 0
    });
}

/**
 * 便捷函數：任務進度日誌
 */
function logTaskProgress(taskId, stage, progress, additionalData = {}) {
    return log('info', `📊 進度更新：${progress}%`, {
        task_id: taskId,
        stage: stage,
        progress: progress,
        ...additionalData
    });
}

/**
 * 便捷函數：任務完成日誌
 */
function logTaskComplete(taskId, reviewId = null) {
    return log('info', '✅ 任務完成', {
        task_id: taskId,
        review_id: reviewId,
        status: 'COMPLETED'
    });
}

/**
 * 便捷函數：任務失敗日誌
 */
function logTaskFailed(taskId, errorMsg, errorStack = null) {
    const extra = {
        task_id: taskId,
        error: errorMsg,
        status: 'FAILED'
    };
    if (errorStack) {
        extra.stack = errorStack;
    }
    return log('error', `❌ 任務失敗：${errorMsg}`, extra);
}
