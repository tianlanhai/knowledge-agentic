# 知识库智能体 - 故障排查指南

**上海宇羲伏天智能科技有限公司出品**

本文档提供常见问题的排查和解决方案。

---

## 目录

1. [后端问题](#后端问题)
2. [前端问题](#前端问题)
3. [数据库问题](#数据库问题)
4. [LLM/Embedding 问题](#llmembedding-问题)
5. [性能问题](#性能问题)

---

## 后端问题

### 1. 服务启动失败

#### 症状
- 执行 `uvicorn app.main:app --reload` 后服务无法启动
- 报错 `ModuleNotFoundError` 或 `ImportError`

#### 排查步骤
1. 检查 Python 版本（需要 3.10+）
   ```bash
   python --version
   ```

2. 检查依赖是否安装
   ```bash
   pip list | grep fastapi
   ```

3. 重新安装依赖
   ```bash
   cd code
   pip install -e .
   ```

#### 常见错误

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `ModuleNotFoundError: No module named 'app'` | 未正确安装包 | 执行 `pip install -e .` |
| `ImportError: cannot import name 'xxx'` | 依赖版本不匹配 | 更新依赖版本 |
| `Address already in use` | 端口被占用 | 更改端口或关闭占用进程 |

---

### 2. API 请求超时

#### 症状
- API 请求长时间无响应
- 返回 504 Gateway Timeout

#### 排查步骤
1. 检查日志中的错误信息
2. 检查 LLM 服务是否可访问
3. 检查数据库连接状态

#### 解决方案
```python
# 增加超时时间（在代码中配置）
TIMEOUT = 60  # 秒
```

---

### 3. 敏感信息过滤不生效

#### 症状
- API 响应中包含未脱敏的手机号/邮箱

#### 排查步骤
1. 检查 `.env` 配置
   ```bash
   ENABLE_SENSITIVE_DATA_FILTER=True
   FILTER_MOBILE=True
   FILTER_EMAIL=True
   ```

2. 检查过滤策略配置
   ```bash
   SENSITIVE_DATA_MASK_STRATEGY=full  # full/partial/hash
   ```

---

## 前端问题

### 1. 页面无法加载

#### 症状
- 浏览器显示空白页面
- 控制台报错

#### 排查步骤
1. 检查 API 代理配置（`vite.config.ts`）
2. 检查后端服务是否运行
3. 检查浏览器控制台错误

#### 解决方案
```typescript
// 确保 proxy 配置正确
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8010',
      changeOrigin: true,
    }
  }
}
```

---

### 2. 组件渲染错误

#### 症状
- 页面部分内容不显示
- React 报错

#### 排查步骤
1. 检查浏览器控制台错误
2. 检查组件 props 类型是否正确
3. 检查 Zustand store 状态

---

### 3. 打包后样式丢失

#### 症状
- `pnpm build` 后样式不生效

#### 解决方案
```bash
# 清理缓存后重新构建
rm -rf dist node_modules/.vite
pnpm build
```

---

## 数据库问题

### 1. 连接失败

#### 症状
- 报错 `could not connect to server`

#### 排查步骤
1. 检查数据库服务状态
   ```bash
   # PostgreSQL
   pg_isready -h localhost -p 5432
   ```

2. 检查 `.env` 配置
   ```bash
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=knowledge_db
   DB_USER=postgres
   DB_PASSWORD=test
   ```

3. 测试连接
   ```bash
   psql -h localhost -U postgres -d knowledge_db
   ```

---

### 2. 查询性能慢

#### 症状
- API 响应时间过长

#### 排查步骤
1. 启用查询日志
2. 检查是否缺少索引
3. 检查是否存在 N+1 查询

#### 解决方案
```sql
-- 添加索引示例
CREATE INDEX idx_vector_mapping_document_id ON vector_mapping(document_id);
CREATE INDEX idx_document_created_at ON document(created_at);
```

---

### 3. 迁移失败

#### 症状
- 数据库迁移执行报错

#### 解决方案
```bash
# 回滚迁移
alembic downgrade -1

# 检查迁移文件
alembic history

# 重新执行迁移
alembic upgrade head
```

---

## LLM/Embedding 问题

### 1. Ollama 连接失败

#### 症状
- 报错 `无法连接Ollama服务`

#### 排查步骤
1. 检查 Ollama 服务状态
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. 检查 `.env` 配置
   ```bash
   OLLAMA_BASE_URL=http://localhost:11434
   ```

3. Docker 环境使用 host.docker.internal
   ```bash
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   ```

---

### 2. 模型加载失败

#### 症状
- 模型响应报错或超时

#### 排查步骤
1. 检查模型是否已下载
   ```bash
   ollama list
   ```

2. 拉取缺失的模型
   ```bash
   ollama pull deepseek-r1:8b
   ```

3. 检查 GPU 显存
   ```bash
   nvidia-smi
   ```

#### 解决方案
```bash
# 调整 GPU 使用配置
OLLAMA_NUM_GPU=1
OLLAMA_GPU_MEMORY_UTILIZATION=0.9
```

---

### 3. API Key 错误

#### 症状
- 云 LLM 服务返回 401 或认证失败

#### 排查步骤
1. 检查 API Key 是否正确
2. 检查 Key 是否已过期
3. 检查账户余额

---

## 性能问题

### 1. 响应慢

#### 症状
- API 响应时间超过 10 秒

#### 排查步骤
1. 检查日志中的耗时信息
2. 使用性能分析工具
3. 检查数据库查询

#### 优化建议
- 使用流式响应（已实现）
- 添加缓存层
- 使用 CDN 分发静态资源

---

### 2. 内存占用高

#### 症状
- 服务进程内存持续增长

#### 排查步骤
1. 使用内存分析工具
2. 检查是否有内存泄漏
3. 检查向量数据库连接池

#### 解决方案
```python
# 配置连接池
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

---

### 3. 并发处理能力不足

#### 症状
- 高并发时响应变慢或超时

#### 解决方案
```python
# 使用异步处理
import asyncio

async def process_batch(items):
    tasks = [process_item(item) for item in items]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

---

## 调试技巧

### 1. 启用详细日志
```bash
# .env 配置
DEBUG=True
LOG_LEVEL=DEBUG
```

### 2. 使用 Mock 模式
```bash
# .env 配置
USE_MOCK=True
```

### 3. 检查服务健康
```bash
# 后端健康检查
curl http://localhost:8010/api/v1/version

# 前端健康检查
curl http://localhost:3000
```

---

## 获取帮助

如果以上方案无法解决问题：

1. 查看项目文档：[docs/README.md](./README.md)
2. 检查 GitHub Issues
3. 联系技术支持

---

**文档版本**: 1.0.0
**最后更新**: 2026-01-29
