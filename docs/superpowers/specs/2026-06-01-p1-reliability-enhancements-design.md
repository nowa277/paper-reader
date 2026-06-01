# P1 可靠性增强设计

**日期:** 2026-06-01
**状态:** 设计完成

---

## 1. 概述

为 paper-reader 实现 5 个高优先级可靠性增强功能：
1. **Jina Reader API 速率控制** — 20 RPM 限制
2. **网络中断处理** — 重新下载策略
3. **自动创建归档目录** — 目录不存在时自动创建
4. **MinerU 进度反馈** — 处理耗时显示
5. **批量处理检查点** — 断点续传

---

## 2. 架构

所有新增模块集中在 `skills/fetch/` 下：

```
skills/fetch/
├── rate_limiter.py    # Jina API 速率控制
├── checkpoint.py      # 批量处理检查点
└── fetcher.py        # 统一获取逻辑
```

---

## 3. 速率控制 (rate_limiter.py)

### 3.1 算法

使用**令牌桶算法（Token Bucket）**变种 — 滑动窗口限速。

### 3.2 规格

- 限制: 20 请求/分钟
- 窗口: 60 秒滑动窗口
- 线程安全: 使用 threading.Lock
- 超限时: 自动等待直到可以发送

### 3.3 API

```python
class RateLimiter:
    def __init__(self, rpm: int = 20, window_seconds: float = 60.0):
        """初始化限速器。"""

    def acquire(self) -> None:
        """获取许可，如果超限则等待。"""

    def __enter__(self) -> "RateLimiter":
        """上下文管理器入口。"""

    def __exit__(self, *args) -> None:
        """释放许可。"""
```

### 3.4 使用示例

```python
with RateLimiter(rpm=20):
    response = call_jina_api(url)
```

### 3.5 状态

- 不保存持久化状态
- 进程重启后重置

---

## 4. 断点续传策略

### 4.1 策略选择

**重新下载（无断点续传）**

- 网络中断后，重新从头下载整个文件
- 简单可靠，不依赖 curl 的 `-C -` 特性
- 大文件下载前检查磁盘空间

### 4.2 实现

```python
def download_with_space_check(url: str, output_path: Path) -> Path:
    """下载文件，下载前检查磁盘空间。"""
    # 1. 发送 HEAD 请求获取 Content-Length
    # 2. 检查磁盘空间
    # 3. 空间不足则抛出异常
    # 4. 空间足够则下载
    # 5. 失败则抛出异常让调用方处理
```

---

## 5. 自动创建目录

### 5.1 规格

- 写入文件前检查目标目录是否存在
- 不存在时调用 `mkdir -p`（递归创建）
- 创建失败时抛出 `OSError`

### 5.2 实现

```python
def ensure_dir(path: Path) -> None:
    """确保目录存在，不存在则创建。"""
    path.mkdir(parents=True, exist_ok=True)
```

---

## 6. MinerU 进度反馈

### 6.1 策略

- 不显示百分比进度（MinerU 不提供实时进度）
- 显示**处理耗时**
- 仅在终端输出，不写入文件

### 6.2 实现

```python
def run_mineru_with_timing(pdf_path: Path, output_dir: Path, lang: str = "en") -> dict:
    """运行 MinerU，返回耗时信息。"""
    start_time = time.time()
    result = run_mineru(pdf_path, output_dir, lang)
    elapsed = time.time() - start_time
    logger.info(f"MinerU processing completed in {elapsed:.1f} seconds")
    result["elapsed_seconds"] = elapsed
    return result
```

---

## 7. 批量处理检查点 (checkpoint.py)

### 7.1 检查点文件

- 位置: `~/.paper-reader/batch_checkpoints.json`
- 格式: JSON 对象，key 为 batch_id，value 为已处理 paper ID 列表

```json
{
  "batch_2026-06-01_001": ["arxiv:2401.12345", "doi:10.1234/example"],
  "batch_2026-06-01_002": ["arxiv:2402.54321"]
}
```

### 7.2 API

```python
class BatchCheckpoint:
    def __init__(self, checkpoint_path: Path | None = None):
        """初始化检查点管理器。"""

    def get_processed(self, batch_id: str) -> set[str]:
        """获取指定批次的已处理 paper ID。"""

    def mark_processed(self, batch_id: str, paper_id: str) -> None:
        """标记 paper 已处理。"""

    def is_processed(self, batch_id: str, paper_id: str) -> bool:
        """检查 paper 是否已处理。"""

    def clear(self, batch_id: str) -> None:
        """清除指定批次的检查点。"""

    def list_batches(self) -> list[str]:
        """列出所有批次。"""
```

### 7.3 重启逻辑

```python
def process_batch(papers: list[str], batch_id: str) -> None:
    checkpoint = BatchCheckpoint()
    processed = checkpoint.get_processed(batch_id)

    for paper in papers:
        if checkpoint.is_processed(batch_id, paper):
            logger.info(f"Skipping already processed: {paper}")
            continue
        # 处理论文...
        checkpoint.mark_processed(batch_id, paper)
```

---

## 8. 文件结构

```
paper-reader/
├── skills/
│   └── fetch/
│       ├── __init__.py
│       ├── SKILL.md
│       ├── rate_limiter.py      # 新增
│       ├── checkpoint.py         # 新增
│       └── fetcher.py           # 新增
├── tests/
│   └── skills/
│       └── fetch/
│           ├── test_rate_limiter.py   # 新增
│           └── test_checkpoint.py      # 新增
└── docs/superpowers/specs/
    └── 2026-06-01-p1-reliability-enhancements-design.md
```

---

## 9. 实现顺序

1. `rate_limiter.py` — 速率控制
2. `checkpoint.py` — 检查点管理
3. `fetcher.py` — 统一获取逻辑（含目录自动创建）
4. 增强 `mineru/installer.py` — 添加耗时输出
5. 单元测试

---

## 10. 验收标准

- [ ] `RateLimiter.acquire()` 在 20 RPM 限制内执行
- [ ] 下载前检查磁盘空间，空间不足时抛出异常
- [ ] 归档目录不存在时自动创建
- [ ] MinerU 处理完成后输出耗时
- [ ] 批量处理重启时跳过已完成的 paper ID
- [ ] 所有新模块单元测试覆盖率 ≥ 80%
