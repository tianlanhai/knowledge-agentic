/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：chatService单元测试
 * 内部逻辑：测试对话服务层的API调用
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { chatService } from './chatService';
import type { ChatRequest, ChatResponse, SourceDetail } from '../types/chat';
import api from './api';

/**
 * 文件级注释：全局类型扩展
 * 内部逻辑：为测试环境扩展global类型
 */
declare global {
  var fetch: any;
}

/**
 * 内部变量：Mock数据
 */
const mockResponses = {
  chatCompletion: {
    answer: '测试回答',
    sources: [{ doc_id: 1, text_segment: '来源内容', score: 0.9 }],
    formatting_applied: true,
  } as ChatResponse,
  sources: [
    { doc_id: 1, file_name: 'test.txt', content: '来源内容1', score: 0.9 },
    { doc_id: 1, file_name: 'test.txt', content: '来源内容2', score: 0.8 },
  ] as SourceDetail[],
  summary: {
    summary: '文档总结内容',
    key_points: ['要点1', '要点2', '要点3'],
  },
  comparison: {
    comparison: '文档对比结果',
    differences: ['差异1', '差异2'],
  },
};

describe('chatService', () => {
  let postSpy: any;
  let getSpy: any;

  beforeEach(() => {
    // 内部逻辑：Mock全局fetch和spy on api模块
    global.fetch = vi.fn();
    postSpy = vi.spyOn(api, 'post').mockResolvedValue(mockResponses.chatCompletion);
    getSpy = vi.spyOn(api, 'get').mockResolvedValue(mockResponses.sources);
  });

  afterEach(() => {
    // 内部逻辑：恢复全局mock
    vi.restoreAllMocks();
  });

  /**
   * 测试chatCompletion功能
   */
  it('应该调用chatCompletions接口', async () => {
    const request: ChatRequest = {
      message: '测试问题',
      history: [],
      use_agent: false,
      stream: false,
    };

    const response = await chatService.chatCompletion(request);

    expect(response).toEqual(mockResponses.chatCompletion);
    expect(postSpy).toHaveBeenCalledWith('/chat/completions', request);
  });

  /**
   * 测试streamChatCompletion功能
   */
  it('应该调用streamChatCompletions接口', async () => {
    // 内部逻辑：创建模拟的ReadableStream用于测试流式响应
    const mockStream = new ReadableStream({
      async start(controller) {
        // 内部逻辑：发送SSE格式的数据
        const chunks = [
          'data: {"answer": "流"}\n\n',
          'data: {"answer": "式"}\n\n',
          'data: {"answer": "回"}\n\n',
          'data: {"answer": "答"}\n\n',
        ];
        for (const chunk of chunks) {
          controller.enqueue(new TextEncoder().encode(chunk));
          // 内部逻辑：短暂延迟模拟真实网络行为
          await new Promise(resolve => setTimeout(resolve, 10));
        }
        controller.close();
      },
    });

    const mockResponse = {
      ok: true,
      status: 200,
      statusText: 'OK',
      body: mockStream,
    } as Response;

    vi.mocked(global.fetch).mockResolvedValue(mockResponse);

    const request: ChatRequest = {
      message: '流式测试',
      history: [],
      use_agent: false,
      stream: true,
    };

    let receivedChunks: string[] = [];

    await chatService.streamChatCompletion(request, (chunk) => {
      receivedChunks.push(chunk);
    });

    expect(receivedChunks).toEqual(['流', '式', '回', '答']);
  });

  /**
   * 测试getSources功能
   */
  it('应该调用sources接口', async () => {
    const response = await chatService.getSources(1);

    expect(response).toEqual(mockResponses.sources);
    expect(getSpy).toHaveBeenCalledWith('/sources', { params: { doc_id: 1 } });
  });

  /**
   * 测试getSources不传docId
   */
  it('应该在不传docId时调用sources接口', async () => {
    const response = await chatService.getSources();

    expect(response).toEqual(mockResponses.sources);
    expect(getSpy).toHaveBeenCalledWith('/sources', { params: { doc_id: undefined } });
  });

  /**
   * 测试summarizeDocument功能
   */
  it('应该调用summary接口', async () => {
    postSpy.mockResolvedValueOnce(mockResponses.summary);

    const response = await chatService.summarizeDocument(1);

    expect(response).toEqual(mockResponses.summary);
    expect(postSpy).toHaveBeenCalledWith('/chat/summary', { doc_id: 1 });
  });

  /**
   * 测试compareDocuments功能
   */
  it('应该调用compare接口', async () => {
    postSpy.mockResolvedValueOnce(mockResponses.comparison);

    const docIds = [1, 2, 3];

    const response = await chatService.compareDocuments(docIds);

    expect(response).toEqual(mockResponses.comparison);
    expect(postSpy).toHaveBeenCalledWith('/chat/compare', { doc_ids: docIds });
  });

  /**
   * 测试单个文档对比
   */
  it('应该支持单个文档对比', async () => {
    postSpy.mockResolvedValueOnce(mockResponses.comparison);

    const response = await chatService.compareDocuments([1]);

    expect(response).toEqual(mockResponses.comparison);
    expect(postSpy).toHaveBeenCalledWith('/chat/compare', { doc_ids: [1] });
  });

  /**
   * 测试网络错误
   */
  it('应该处理HTTP错误', async () => {
    postSpy.mockRejectedValueOnce(new Error('Internal Server Error'));

    const request: ChatRequest = {
      message: '测试问题',
      history: [],
      use_agent: false,
      stream: false,
    };

    await expect(chatService.chatCompletion(request)).rejects.toThrow('Internal Server Error');
  });

  /**
   * 测试chatCompletion带历史记录
   */
  it('应该发送带历史记录的请求', async () => {
    const request: ChatRequest = {
      message: '新问题',
      history: [
        { role: 'user', content: '历史问题1' },
        { role: 'assistant', content: '历史回答1' },
      ],
      use_agent: true,
      stream: false,
    };

    await chatService.chatCompletion(request);

    expect(postSpy).toHaveBeenCalledWith('/chat/completions', request);
  });

  /**
   * 测试streamChatCompletion带智能体模式
   */
  it('应该在智能体模式下流式发送', async () => {
    // 内部逻辑：创建模拟的ReadableStream
    const mockStream = new ReadableStream({
      async start(controller) {
        // 内部逻辑：发送SSE格式的数据
        const sseData = 'data: {"answer": "智能体回答"}\n\n';
        controller.enqueue(new TextEncoder().encode(sseData));
        controller.close();
      },
    });

    const mockResponse = {
      ok: true,
      status: 200,
      statusText: 'OK',
      body: mockStream,
    } as Response;

    vi.mocked(global.fetch).mockResolvedValue(mockResponse);

    const request: ChatRequest = {
      message: '智能体问题',
      history: [],
      use_agent: true,
      stream: true,
    };

    await chatService.streamChatCompletion(request, vi.fn());

    expect(global.fetch).toHaveBeenCalledWith('/api/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...request, stream: true }),
    });
  });

  /**
   * 测试流式数据接收
   */
  it('应该正确处理流式数据', async () => {
    // 内部逻辑：创建模拟的ReadableStream，发送多个数据块
    const mockStream = new ReadableStream({
      async start(controller) {
        // 内部逻辑：发送多个SSE数据块
        const chunks = [
          'data: {"answer": "流"}\n\n',
          'data: {"answer": "式"}\n\n',
          'data: {"answer": "回"}\n\n',
          'data: {"answer": "答"}\n\n',
        ];
        for (const chunk of chunks) {
          controller.enqueue(new TextEncoder().encode(chunk));
        }
        controller.close();
      },
    });

    const mockResponse = {
      ok: true,
      status: 200,
      statusText: 'OK',
      body: mockStream,
    } as Response;

    vi.mocked(global.fetch).mockResolvedValue(mockResponse);

    const request: ChatRequest = {
      message: '流式测试',
      history: [],
      use_agent: false,
      stream: true,
    };

    const chunks: string[] = [];

    await chatService.streamChatCompletion(request, (chunk) => {
      chunks.push(chunk);
    });

    expect(chunks).toContain('流');
    expect(chunks).toContain('式');
  });

  /**
   * 测试流式响应带sources回调
   * 内部逻辑：验证onSources回调被正确调用
   */
  it('应该在流式响应中调用onSources回调', async () => {
    const mockStream = new ReadableStream({
      async start(controller) {
        // 内部逻辑：发送包含sources的SSE数据
        const chunks = [
          'data: {"answer": "回答"}\n\n',
          'data: {"sources": [{"doc_id": 1, "file_name": "test.pdf"}]}\n\n',
        ];
        for (const chunk of chunks) {
          controller.enqueue(new TextEncoder().encode(chunk));
        }
        controller.close();
      },
    });

    const mockResponse = {
      ok: true,
      status: 200,
      statusText: 'OK',
      body: mockStream,
    } as Response;

    vi.mocked(global.fetch).mockResolvedValue(mockResponse);

    const request: ChatRequest = {
      message: '测试',
      history: [],
      use_agent: false,
      stream: true,
    };

    const onSources = vi.fn();

    await chatService.streamChatCompletion(request, vi.fn(), onSources);

    expect(onSources).toHaveBeenCalledWith([{ doc_id: 1, file_name: 'test.pdf' }]);
  });

  /**
   * 测试流式响应带onDone回调
   * 内部逻辑：验证流完成时onDone回调被调用
   */
  it('应该在流完成时调用onDone回调', async () => {
    const mockStream = new ReadableStream({
      async start(controller) {
        const chunks = [
          'data: {"answer": "回答"}\n\n',
          'data: {"done": true}\n\n',
        ];
        for (const chunk of chunks) {
          controller.enqueue(new TextEncoder().encode(chunk));
        }
        controller.close();
      },
    });

    const mockResponse = {
      ok: true,
      status: 200,
      statusText: 'OK',
      body: mockStream,
    } as Response;

    vi.mocked(global.fetch).mockResolvedValue(mockResponse);

    const request: ChatRequest = {
      message: '测试',
      history: [],
      use_agent: false,
      stream: true,
    };

    const onDone = vi.fn();

    await chatService.streamChatCompletion(request, vi.fn(), undefined, onDone);

    expect(onDone).toHaveBeenCalled();
  });

  /**
   * 测试流式响应跳过空行和注释行
   * 内部逻辑：验证SSE格式的注释和空行被正确跳过
   */
  it('应该跳过SSE格式的空行和注释行', async () => {
    const mockStream = new ReadableStream({
      async start(controller) {
        // 内部逻辑：包含空行、注释行和有效数据
        const chunks = [
          '\n\n',
          ': this is a comment\n\n',
          'data: {"answer": "有效回答"}\n\n',
          '\n',
          'data: {"answer": "另一个回答"}\n\n',
        ];
        for (const chunk of chunks) {
          controller.enqueue(new TextEncoder().encode(chunk));
        }
        controller.close();
      },
    });

    const mockResponse = {
      ok: true,
      status: 200,
      statusText: 'OK',
      body: mockStream,
    } as Response;

    vi.mocked(global.fetch).mockResolvedValue(mockResponse);

    const request: ChatRequest = {
      message: '测试',
      history: [],
      use_agent: false,
      stream: true,
    };

    const chunks: string[] = [];

    await chatService.streamChatCompletion(request, (chunk) => {
      chunks.push(chunk);
    });

    expect(chunks).toEqual(['有效回答', '另一个回答']);
  });

  /**
   * 测试流式响应处理无效JSON
   * 内部逻辑：验证JSON解析失败时跳过该行并继续处理
   */
  it('应该在JSON解析失败时跳过该行', async () => {
    const mockStream = new ReadableStream({
      async start(controller) {
        // 内部逻辑：包含无效的JSON数据
        const chunks = [
          'data: {"answer": "有效回答"}\n\n',
          'data: {invalid json}\n\n',
          'data: {"answer": "另一个有效回答"}\n\n',
        ];
        for (const chunk of chunks) {
          controller.enqueue(new TextEncoder().encode(chunk));
        }
        controller.close();
      },
    });

    const mockResponse = {
      ok: true,
      status: 200,
      statusText: 'OK',
      body: mockStream,
    } as Response;

    vi.mocked(global.fetch).mockResolvedValue(mockResponse);

    const request: ChatRequest = {
      message: '测试',
      history: [],
      use_agent: false,
      stream: true,
    };

    const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const chunks: string[] = [];

    await chatService.streamChatCompletion(request, (chunk) => {
      chunks.push(chunk);
    });

    // 内部逻辑：验证有效的chunk被处理，无效的跳过
    expect(chunks).toEqual(['有效回答', '另一个有效回答']);
    expect(consoleWarnSpy).toHaveBeenCalled();

    consoleWarnSpy.mockRestore();
  });

  /**
   * 测试流式响应处理跨chunk的数据
   * 内部逻辑：验证数据跨chunk分割时能正确重组
   */
  it('应该正确处理跨chunk的SSE数据', async () => {
    const mockStream = new ReadableStream({
      async start(controller) {
        // 内部逻辑：故意分割SSE数据行
        const chunks = [
          new TextEncoder().encode('data: {"answer": '),
          new TextEncoder().encode('"跨chunk回答"}\n\n'),
        ];
        for (const chunk of chunks) {
          controller.enqueue(chunk);
        }
        controller.close();
      },
    });

    const mockResponse = {
      ok: true,
      status: 200,
      statusText: 'OK',
      body: mockStream,
    } as Response;

    vi.mocked(global.fetch).mockResolvedValue(mockResponse);

    const request: ChatRequest = {
      message: '测试',
      history: [],
      use_agent: false,
      stream: true,
    };

    const chunks: string[] = [];

    await chatService.streamChatCompletion(request, (chunk) => {
      chunks.push(chunk);
    });

    expect(chunks).toEqual(['跨chunk回答']);
  });

  /**
   * 测试流式响应HTTP错误
   * 内部逻辑：验证HTTP非200状态码时抛出错误
   */
  it('应该在HTTP错误时抛出异常', async () => {
    const mockResponse = {
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      body: null,
    } as Response;

    vi.mocked(global.fetch).mockResolvedValue(mockResponse);

    const request: ChatRequest = {
      message: '测试',
      history: [],
      use_agent: false,
      stream: true,
    };

    await expect(
      chatService.streamChatCompletion(request, vi.fn())
    ).rejects.toThrow('HTTP 500: Internal Server Error');
  });

  /**
   * 测试流式响应没有answer字段
   * 内部逻辑：验证数据中没有answer字段时不调用onChunk
   */
  it('应该处理没有answer字段的SSE数据', async () => {
    const mockStream = new ReadableStream({
      async start(controller) {
        // 内部逻辑：只有sources字段，没有answer
        const chunks = [
          'data: {"sources": []}\n\n',
          'data: {"done": true}\n\n',
        ];
        for (const chunk of chunks) {
          controller.enqueue(new TextEncoder().encode(chunk));
        }
        controller.close();
      },
    });

    const mockResponse = {
      ok: true,
      status: 200,
      statusText: 'OK',
      body: mockStream,
    } as Response;

    vi.mocked(global.fetch).mockResolvedValue(mockResponse);

    const request: ChatRequest = {
      message: '测试',
      history: [],
      use_agent: false,
      stream: true,
    };

    const onChunk = vi.fn();
    const onSources = vi.fn();
    const onDone = vi.fn();

    await chatService.streamChatCompletion(request, onChunk, onSources, onDone);

    expect(onChunk).not.toHaveBeenCalled();
    expect(onSources).toHaveBeenCalledWith([]);
    expect(onDone).toHaveBeenCalled();
  });

  /**
   * 测试流式响应处理非data开头的行
   * 内部逻辑：验证不以'data:'开头的行被跳过
   */
  it('应该跳过不以data:开头的行', async () => {
    const mockStream = new ReadableStream({
      async start(controller) {
        // 内部逻辑：包含不以data:开头的有效数据行
        const chunks = [
          'event: message\n\n',
          'data: {"answer": "回答"}\n\n',
          'id: 123\n\n',
          'data: {"done": true}\n\n',
        ];
        for (const chunk of chunks) {
          controller.enqueue(new TextEncoder().encode(chunk));
        }
        controller.close();
      },
    });

    const mockResponse = {
      ok: true,
      status: 200,
      statusText: 'OK',
      body: mockStream,
    } as Response;

    vi.mocked(global.fetch).mockResolvedValue(mockResponse);

    const request: ChatRequest = {
      message: '测试',
      history: [],
      use_agent: false,
      stream: true,
    };

    const onChunk = vi.fn();
    const onDone = vi.fn();

    await chatService.streamChatCompletion(request, onChunk, undefined, onDone);

    expect(onChunk).toHaveBeenCalledWith('回答');
    expect(onDone).toHaveBeenCalled();
  });
});
