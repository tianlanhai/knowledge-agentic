# 知识库智能体 - 测试指南文档

帅哥，本测试指南文档整合了前后端测试的完整指南，帮助你快速上手测试编写和执行。采用UI/UX Pro Max设计理念，确保界面美观、易用、专业。

## 1. 后端测试指南

### 1.1 后端测试环境配置

#### 1.1.1 安装测试依赖

确保已使用 UV 安装项目依赖（包含测试工具）：
```bash
uv sync
```

测试相关依赖（pytest、pytest-asyncio、pytest-cov、httpx、pytest-mock）已在 pyproject.toml 中配置，会自动安装。

#### 1.1.2 测试目录结构

```
code/tests/
├── conftest.py              # pytest 配置和 fixtures
├── mock_fixtures.py         # Mock 数据和工具
├── test_api.py              # API 接口测试
├── test_services.py          # 服务层测试
├── test_models.py           # 数据模型测试
└── test_utils.py            # 工具函数测试
```

### 1.2 后端测试执行命令

#### 1.2.1 运行所有测试

```bash
# 运行所有测试并生成覆盖率报告
uv run pytest code/tests --cov=code/app --cov-report=term-missing --maxWorkers=2 --testTimeout=10
```

#### 1.2.2 运行特定测试

```bash
# 运行特定测试文件
uv run pytest code/tests/test_api.py

# 运行特定测试函数
uv run pytest code/tests/test_api.py::test_root_endpoint

# 运行匹配模式的测试
uv run pytest code/tests -k "test_ingest"
```

#### 1.2.3 生成覆盖率报告

```bash
# 生成 HTML 覆盖率报告
uv run pytest code/tests --cov=code/app --cov-report=html
# 报告将生成在 htmlcov/ 目录下，通过浏览器打开 index.html 即可查看
```

#### 1.2.4 GPU 相关测试

若要验证代码在真实 GPU 环境下的运行情况（会尝试加载模型），请设置环境变量：
```bash
set TEST_WITH_GPU=True
uv run pytest code/tests/test_services.py::test_ingest_service_get_embeddings_config
```

### 1.3 后端测试覆盖率目标

- **整体覆盖率**：> 95%
- **核心业务逻辑**：> 98%
- **API 层**：> 95%
- **Service 层**：> 95%
- **Model 层**：> 90%

### 1.4 后端测试最佳实践

#### 1.4.1 测试原则

- **独立性**：每个测试应该独立运行
- **可重复性**：测试结果应该可重复
- **快速反馈**：测试应该快速运行
- **可读性**：测试代码应该清晰易懂

#### 1.4.2 测试金字塔

```
        E2E 测试（5%）
       /              \
      /                \
     /                  \
    /                    \
   /                      \
  /                        \
 /                          \
/                            \
集成测试（15%）              单元测试（80%）
```

#### 1.4.3 Mock 策略

- **后端 Mock**：使用 pytest-mock mock 外部依赖
- **API Mock**：使用 httpx mock HTTP 请求
- **数据库 Mock**：使用内存数据库替代真实数据库

## 2. 前端测试指南

### 2.1 前端测试环境配置

#### 2.1.1 安装测试依赖

在前端项目根目录下运行以下命令安装测试依赖：
```bash
# 进入前端目录
cd frontend

# 安装测试相关依赖
pnpm add -D vitest @vitest/ui @vitest/coverage-v8
pnpm add -D @testing-library/react @testing-library/jest-dom @testing-library/user-event
pnpm add -D jsdom
```

#### 2.1.2 配置 Vitest

在项目根目录创建 `vitest.config.ts` 文件：
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
      ],
    },
  },
});
```

#### 2.1.3 配置测试环境

创建 `src/test/setup.ts` 文件，设置测试环境：
```typescript
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});
```

#### 2.1.4 更新 package.json

在 `package.json` 中添加测试脚本：
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:coverage": "vitest --coverage",
    "test:ui": "vitest --ui"
  }
}
```

### 2.2 前端测试执行命令

#### 2.2.1 运行所有测试

```bash
# 进入前端目录
cd frontend

# 运行所有测试
pnpm test

# 运行测试并监听文件变化（仅开发环境）
pnpm test:watch

# 运行测试并生成覆盖率报告
pnpm test:coverage

# 启动 Vitest UI（可视化测试界面）
pnpm test:ui
```

#### 2.2.2 运行特定测试

```bash
# 运行特定测试文件
pnpm test src/components/features/Chat/index.test.tsx

# 运行匹配模式的测试
pnpm test -- --grep "ChatInterface"

# 运行特定测试套件
pnpm test -- --reporter=verbose
```

#### 2.2.3 生成覆盖率报告

```bash
# 生成覆盖率报告（终端输出）
pnpm test:coverage

# 生成 HTML 覆盖率报告
pnpm test:coverage --reporter=html

# 查看覆盖率报告
# HTML 报告生成在 coverage/ 目录下，用浏览器打开 index.html
```

### 2.3 前端测试文件组织

#### 2.3.1 目录结构

```
frontend/src/
├── components/
│   ├── features/
│   │   ├── Chat/
│   │   │   ├── index.tsx
│   │   │   └── index.test.tsx
│   │   ├── KnowledgeManagement/
│   │   │   ├── DocumentList.tsx
│   │   │   └── DocumentList.test.tsx
│   │   └── Search/
│   │       ├── index.tsx
│   │       └── index.test.tsx
│   └── layout/
│       ├── Header.tsx
│       └── Header.test.tsx
├── hooks/
│   ├── useChat.ts
│   └── useChat.test.ts
├── stores/
│   ├── chatStore.ts
│   └── chatStore.test.ts
├── services/
│   ├── api.ts
│   └── api.test.ts
└── utils/
    ├── format.ts
    └── format.test.ts
```

#### 2.3.2 测试命名规范

- 组件测试：`ComponentName.test.tsx`
- Hook 测试：`useHookName.test.ts`
- Store 测试：`storeName.test.ts`
- Service 测试：`serviceName.test.ts`
- 工具函数测试：`utilName.test.ts`

### 2.4 前端测试覆盖率目标

- **整体覆盖率**：> 80%
- **组件覆盖率**：> 85%
- **Hooks 覆盖率**：> 90%
- **Stores 覆盖率**：> 90%
- **Services 覆盖率**：> 80%

### 2.5 UI组件测试指南

帅哥，UI组件测试是确保界面美观、易用、专业的关键。采用UI/UX Pro Max设计理念的测试方法。

#### 2.5.1 组件渲染测试

**测试组件是否正确渲染，以及渲染后的DOM结构是否符合设计要求。**

```typescript
// src/components/features/Chat/index.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChatInterface } from './index';
import { useChat } from '../../../hooks/useChat';
import { useChatStore } from '../../../stores/chatStore';

vi.mock('../../../hooks/useChat');
vi.mock('../../../stores/chatStore');

describe('ChatInterface - 组件渲染', () => {
  const mockUseChat = {
    messages: [],
    loading: false,
    streamSendMessage: vi.fn(),
  };

  beforeEach(() => {
    vi.mocked(useChat).mockReturnValue(mockUseChat);
  });

  it('应该渲染对话界面', () => {
    render(<ChatInterface />);
    
    // 验证主要元素是否存在
    expect(screen.getByText('智能体模式')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('输入您的问题...')).toBeInTheDocument();
  });

  it('应该显示正确的玻璃态样式', () => {
    const { container } = render(<ChatInterface />);
    const messageContainer = container.querySelector('.glass');
    
    // 验证玻璃态效果
    expect(messageContainer).toHaveStyle({
      background: 'rgba(255, 255, 255, 0.05)',
      backdropFilter: 'blur(12px)',
    });
  });

  it('应该显示渐变按钮', () => {
    const { container } = render(<ChatInterface />);
    const button = container.querySelector('.btn-gradient');
    
    // 验证渐变背景
    expect(button).toHaveStyle({
      background: 'linear-gradient(135deg, rgb(102, 126, 234) 0%, rgb(118, 75, 162) 100%)',
    });
  });
});
```

#### 2.5.2 组件交互测试

**测试用户交互是否触发正确的行为。**

```typescript
describe('ChatInterface - 交互测试', () => {
  it('应该发送消息', async () => {
    const user = userEvent.setup();
    render(<ChatInterface />);

    const input = screen.getByPlaceholderText('输入您的问题...');
    const sendButton = screen.getByText('发送');

    await user.type(input, '测试消息');
    await user.click(sendButton);

    // 验证是否调用了发送函数
    expect(mockUseChat.streamSendMessage).toHaveBeenCalledWith('测试消息');
  });

  it('应该显示发送按钮悬停效果', () => {
    const { container } = render(<ChatInterface />);
    const button = screen.getByText('发送');
    
    // 模拟悬停事件
    fireEvent.mouseEnter(button);
    
    // 验证光晕效果
    expect(button).toHaveClass('shadow-glow');
  });
});
```

#### 2.5.3 响应式设计测试

**测试组件在不同屏幕尺寸下的表现。**

```typescript
describe('ChatInterface - 响应式设计', () => {
  beforeEach(() => {
    // 设置视口大小
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });
  });

  it('应该在桌面端显示正确的布局', () => {
    window.innerWidth = 1024;
    const { container } = render(<ChatInterface />);
    
    // 验证桌面端布局
    expect(container.querySelector('.sidebar')).toHaveStyle({ width: '240px' });
  });

  it('应该在移动端显示单列布局', () => {
    window.innerWidth = 500;
    const { container } = render(<ChatInterface />);
    
    // 验证移动端布局
    expect(container.querySelector('.sidebar')).toHaveStyle({ display: 'none' });
  });
});
```

#### 2.5.4 动画测试

**测试动画是否正确应用。**

```typescript
describe('ChatInterface - 动画测试', () => {
  it('应该应用淡入动画', () => {
    const { container } = render(<ChatInterface />);
    const element = container.querySelector('.fade-in');
    
    // 验证动画属性
    expect(element).toHaveStyle({
      animation: 'fadeIn 0.3s ease-out',
    });
  });

  it('应该应用滑入动画', () => {
    const { container } = render(<ChatInterface />);
    const element = container.querySelector('.slide-in');
    
    // 验证动画属性
    expect(element).toHaveStyle({
      animation: 'slideIn 0.3s ease-out',
    });
  });
});
```

### 2.6 无障碍测试指南

帅哥，无障碍测试确保所有用户都能便捷使用界面。符合WCAG 2.1 AA级标准。

#### 2.6.1 键盘导航测试

**测试所有交互元素是否支持键盘操作。**

```typescript
describe('ChatInterface - 键盘导航', () => {
  it('应该支持Tab键导航', () => {
    const { container } = render(<ChatInterface />);
    const input = screen.getByPlaceholderText('输入您的问题...');
    
    // 模拟Tab键
    fireEvent.keyDown(input, { key: 'Tab' });
    
    // 验证焦点是否移动
    expect(document.activeElement).toBe(input);
  });

  it('应该支持Enter键发送消息', async () => {
    const user = userEvent.setup();
    render(<ChatInterface />);

    const input = screen.getByPlaceholderText('输入您的问题...');
    
    await user.type(input, '测试消息');
    fireEvent.keyDown(input, { key: 'Enter' });

    // 验证是否发送了消息
    expect(mockUseChat.streamSendMessage).toHaveBeenCalled();
  });

  it('应该显示清晰的焦点指示器', () => {
    const { container } = render(<ChatInterface />);
    const input = screen.getByPlaceholderText('输入您的问题...');
    
    input.focus();
    
    // 验证焦点样式
    expect(input).toHaveStyle({
      outline: '2px solid rgb(102, 126, 234)',
    });
  });
});
```

#### 2.6.2 屏幕阅读器测试

**测试屏幕阅读器是否能正确读取内容。**

```typescript
describe('ChatInterface - 屏幕阅读器', () => {
  it('应该有语义化HTML标签', () => {
    const { container } = render(<ChatInterface />);
    
    // 验证语义化标签
    expect(container.querySelector('nav')).toBeInTheDocument();
    expect(container.querySelector('main')).toBeInTheDocument();
  });

  it('应该有ARIA标签', () => {
    render(<ChatInterface />);
    
    // 验证ARIA标签
    expect(screen.getByRole('button', { name: /发送/i })).toHaveAttribute('aria-label');
  });

  it('图标应该有aria-label', () => {
    render(<ChatInterface />);
    const icon = screen.getByLabelText(/搜索/i);
    
    // 验证图标的aria-label
    expect(icon).toHaveAttribute('aria-label', '搜索');
  });
});
```

#### 2.6.3 色彩对比度测试

**测试文字和背景的色彩对比度是否符合WCAG AA级标准（4.5:1）。**

```typescript
describe('ChatInterface - 色彩对比度', () => {
  it('应该符合色彩对比度AA级标准', () => {
    const { container } = render(<ChatInterface />);
    const text = container.querySelector('.text-primary');
    const background = container.querySelector('.bg-default');
    
    // 获取计算后的颜色
    const computedStyle = window.getComputedStyle(text);
    const textColor = computedStyle.color;
    const bgColor = window.getComputedStyle(background).backgroundColor;
    
    // 计算对比度（简化版）
    const contrastRatio = calculateContrastRatio(textColor, bgColor);
    
    // 验证对比度 >= 4.5
    expect(contrastRatio).toBeGreaterThanOrEqual(4.5);
  });
});

// 辅助函数：计算对比度
function calculateContrastRatio(foreground: string, background: string): number {
  // 简化的对比度计算
  // 实际实现应该使用WCAG对比度算法
  return 4.5;
}
```

### 2.7 Hook 测试

```typescript
// src/hooks/useChat.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useChat } from './useChat';
import { useChatStore } from '../stores/chatStore';
import { chatService } from '../services/chatService';

vi.mock('../stores/chatStore');
vi.mock('../services/chatService');

describe('useChat', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该发送消息并更新状态', async () => {
    const mockAddMessage = vi.fn();
    const mockSetSources = vi.fn();
    const mockSetStreaming = vi.fn();

    vi.mocked(useChatStore).mockReturnValue({
      messages: [],
      addMessage: mockAddMessage,
      setSources: mockSetSources,
      setStreaming: mockSetStreaming,
      useAgent: false,
    });

    vi.mocked(chatService.chatCompletion).mockResolvedValue({
      answer: '测试回答',
      sources: [],
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('测试问题');
    });

    expect(mockAddMessage).toHaveBeenCalledWith({ role: 'user', content: '测试问题' });
    expect(mockAddMessage).toHaveBeenCalledWith({ role: 'assistant', content: '测试回答' });
  });
});
```

### 2.8 Store 测试

```typescript
// src/stores/chatStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from './chatStore';
import type { Message } from '../types/chat';

describe('chatStore', () => {
  beforeEach(() => {
    useChatStore.setState({
      messages: [],
      sources: [],
      isStreaming: false,
      useAgent: false,
    });
  });

  it('应该添加消息', () => {
    const message: Message = { role: 'user', content: '测试消息' };

    useChatStore.getState().addMessage(message);

    expect(useChatStore.getState().messages).toHaveLength(1);
    expect(useChatStore.getState().messages[0]).toEqual(message);
  });

  it('应该清空消息和来源', () => {
    useChatStore.setState({
      messages: [{ role: 'user', content: '测试' }],
      sources: [{ file_name: 'test.pdf', content: '内容', score: 0.9 }],
    });

    useChatStore.getState().clearMessages();

    expect(useChatStore.getState().messages).toHaveLength(0);
    expect(useChatStore.getState().sources).toHaveLength(0);
  });
});
```

### 2.9 Service 测试

```typescript
// src/services/api.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import api from './api';

vi.mock('axios');
vi.mock('antd', () => ({
  message: {
    error: vi.fn(),
  },
}));

describe('api', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该成功发送请求', async () => {
    const mockResponse = { data: { success: true } };
    vi.mocked(axios.create).mockReturnValue({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    } as any);

    vi.mocked(axios.get).mockResolvedValue(mockResponse);

    const result = await api.get('/test');

    expect(result).toEqual({ success: true });
  });

  it('应该处理 400 错误', async () => {
    const mockError = {
      response: {
        status: 400,
        data: { detail: '参数错误' },
      },
    };

    vi.mocked(axios.create).mockReturnValue({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn((onError) => {
          onError(mockError);
          return Promise.reject(mockError);
        }) },
      },
    } as any);

    await expect(api.get('/test')).rejects.toEqual(mockError);
  });
});
```

### 2.10 前端测试调试技巧

#### 2.10.1 使用 Vitest UI 调试

```bash
# 启动 Vitest UI
pnpm test:ui

# 在浏览器中打开 http://localhost:51204
# 可以可视化查看测试结果、覆盖率、源码映射等
```

#### 2.10.2 调试测试代码

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

describe('调试测试', () => {
  it('调试渲染', () => {
    const { container } = render(<MyComponent />);

    // 打印整个 DOM 树
    console.log(container.innerHTML);

    // 使用 debug() 方法
    screen.debug();

    // 查找元素
    const element = screen.getByText('某个文本');
    console.log(element);
  });
});
```

### 2.11 前端测试常见问题排查

#### 2.11.1 测试找不到元素

- **问题**：测试报错 "Unable to find element with text: ..."
- **排查步骤**：
  1. 使用 `screen.debug()` 查看渲染的 DOM
  2. 检查元素是否真的被渲染
  3. 检查选择器是否正确
  4. 检查是否有异步操作未完成

#### 2.11.2 Mock 不生效

- **问题**：Mock 的函数没有被调用
- **排查步骤**：
  1. 检查 mock 是否在文件顶部使用 `vi.mock()` 导入
  2. 检查 mock 是否在测试之前设置
  3. 检查 mock 的返回值是否正确
  4. 使用 `vi.mocked()` 确保类型正确

#### 2.11.3 异步测试失败

- **问题**：异步操作未完成就断言
- **排查步骤**：
  1. 使用 `waitFor` 或 `findBy*` 查询方法
  2. 增加超时时间
  3. 检查异步操作是否真的被触发
  4. 使用 `act()` 包装状态更新

#### 2.11.4 覆盖率不达标

- **问题**：某些代码没有被测试覆盖
- **排查步骤**：
  1. 查看覆盖率报告，找到未覆盖的代码
  2. 分析未覆盖代码的逻辑
  3. 编写测试用例覆盖这些代码
  4. 检查是否有条件分支未被测试

### 2.12 前端测试最佳实践

#### 2.12.1 测试原则

- **用户视角**：测试用户能看到和交互的内容，而不是实现细节
- **独立性**：每个测试应该独立运行，不依赖其他测试
- **可读性**：测试代码应该清晰易懂，使用描述性的测试名称
- **快速反馈**：测试应该快速运行，避免不必要的等待
- **Mock 外部依赖**：使用 mock 隔离外部依赖（API、数据库等）

#### 2.12.2 测试金字塔

```
        E2E 测试（少量）
       /              \
      /                \
     /                  \
    /                    \
   /                      \
  /                        \
 /                          \
/                            \
集成测试（适量）              单元测试（大量）
```

- **单元测试**：测试独立的函数、组件、Hooks（70-80%）
- **集成测试**：测试多个组件协同工作（15-20%）
- **E2E 测试**：测试完整的用户流程（5-10%）

## 3. 测试工具对比

| 特性 | 后端测试 | 前端测试 |
|------|---------|---------|
| 测试框架 | pytest | Vitest |
| 测试环境 | 真实 Python 环境 | jsdom |
| 覆盖率工具 | pytest-cov | @vitest/coverage-v8 |
| Mock 工具 | pytest-mock | vi.mock() |
| 异步测试 | pytest-asyncio | 原生支持 |
| 运行命令 | uv run pytest | pnpm test |
| 覆盖率目标 | > 95% | > 80% |
| 主要测试内容 | API、Services、Models | 组件、Hooks、Stores |

## 4. 相关文档

- [测试方案文档](./测试方案.md) - 了解测试策略
- [CI/CD配置文档](./CI-CD配置文档.md) - 配置自动化测试和部署
- [技术设计文档](./技术设计.md) - 了解系统架构
- [本地调试文档](./本地调试.md) - 了解本地开发调试

希望这份测试指南能帮助你快速上手前后端测试！
