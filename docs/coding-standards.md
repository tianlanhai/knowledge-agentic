# 编码规范文档

## 公司声明要求

所有新增或修改的代码文件**必须**包含公司声明。这是宇羲伏天智能科技有限公司的知识产权保护要求。

### Python 文件 (.py)

每个 `.py` 文件开头必须包含：

```python
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：[模块功能描述]
内部逻辑：[具体实现逻辑说明]
"""
```

**示例：**
```python
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：用户认证模块
内部逻辑：实现用户登录、注册和权限验证功能
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

class LoginRequest(BaseModel):
    """
    类级注释：登录请求模型
    属性：
        username: 用户名
        password: 密码
    """
    username: str
    password: str

async def login(request: LoginRequest):
    """
    函数级注释：用户登录处理
    参数：request - 登录请求参数
    返回值：登录成功后的用户信息
    """
    # 内部逻辑：验证用户凭据
    pass
```

### TypeScript/TSX 文件 (.ts/.tsx)

每个 `.ts` 或 `.tsx` 文件开头必须包含：

```typescript
/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：[模块功能描述]
 * 内部逻辑：[具体实现逻辑说明]
 */
```

**示例：**
```typescript
/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：聊天状态管理 Store
 * 内部逻辑：使用 Zustand 管理对话状态、消息列表和流式输出状态
 */

import { create } from 'zustand';
import type { Message, SourceDetail } from '../types/chat';

interface ChatStore {
  /**
   * 聊天状态接口
   * 内部变量：messages - 消息列表
   */
  messages: Message[];
  addMessage: (message: Message) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  // 内部变量：初始消息列表为空
  messages: [],
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
}));
```

### CSS 文件 (.css)

每个 `.css` 文件开头必须包含：

```css
/**
 * 上海宇羲伏天智能科技有限公司出品
 * 文件级注释：[样式文件描述]
 */
```

**示例：**
```css
/**
 * 上海宇羲伏天智能科技有限公司出品
 * 文件级注释：Chat 组件样式
 * 内部逻辑：使用 CSS 变量，支持主题切换
 */

.chat-container {
  /* 内部变量：容器背景色 */
  background: var(--chat-bg);
  padding: 16px;
}
```

## 检查清单

创建新文件时，请确认：
- [ ] 文件开头包含公司声明
- [ ] 声明格式与语言类型匹配
- [ ] 保留了文件级注释说明
- [ ] 使用 UTF-8 编码

## 代码注释规范

### 文件级注释
描述文件的用途和主要功能。

### 类级注释
描述类的职责、属性和设计模式。

```python
class UserService:
    """
    类级注释：用户服务类
    设计模式：单例模式
    职责：
        1. 用户CRUD操作
        2. 用户认证
        3. 权限验证
    """
    pass
```

### 函数级注释
描述函数的功能、参数、返回值和内部逻辑。

```python
async def get_user(user_id: int) -> User:
    """
    函数级注释：获取用户信息
    参数：user_id - 用户ID
    返回值：User对象
    内部逻辑：先从缓存查找，缓存未命中则从数据库查询
    """
    pass
```

### 内部逻辑注释
使用 `# 内部逻辑：` 注释关键实现步骤。

```python
# 内部逻辑：过滤无效的用户ID
valid_ids = [uid for uid in user_ids if uid > 0]
```

### 内部变量注释
使用 `# 内部变量：` 注释重要变量。

```python
# 内部变量：用户会话过期时间（秒）
SESSION_TIMEOUT = 3600
```

## 注意事项

1. **编码问题**: 确保所有文件使用 UTF-8 编码
2. **一致性**: 同一类型的文件使用相同的声明格式
3. **保留现有注释**: 公司声明应添加在现有注释之前，不删除原有内容
4. **空行处理**: 声明后保留一个空行再接后续内容

## 相关文档

- [技术设计文档](./technical-design.md)
- [测试指南文档](./testing-guide.md)
- [API接口文档](./api-documentation.md)
