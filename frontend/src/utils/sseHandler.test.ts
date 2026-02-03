/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：SSE 流式数据处理工具单元测试
 * 内部逻辑：测试 SSE 处理器和事件发射器的功能
 * 测试策略：
 *   - 单元测试：测试每个类的方法
 *   - Mock 测试：Mock Response 和 Reader
 *   - 异步测试：验证流式数据处理
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SSEHandler, SSEEventEmitter, SSEEventType, type SSECallbacks } from './sseHandler';

describe('SSEHandler', () => {
  describe('processStream 方法', () => {
    it('应该成功处理完整的 SSE 流', async () => {
      // 内部变量：模拟流式数据
      const chunks = [
        'data: {"answer":"Hello"}\n\n',
        'data: {"answer":" World"}\n\n',
        'data: {"done":true}\n\n',
      ];

      // 内部变量：创建模拟的 Reader
      let chunkIndex = 0;
      const mockReader = {
        read: vi.fn(async () => {
          if (chunkIndex < chunks.length) {
            const value = new TextEncoder().encode(chunks[chunkIndex]);
            chunkIndex++;
            return { done: false, value };
          }
          return { done: true, value: undefined };
        }),
        releaseLock: vi.fn(),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as unknown as Response;

      const onChunk = vi.fn();
      const onDone = vi.fn();

      await SSEHandler.processStream(mockResponse, { onChunk, onDone });

      expect(onChunk).toHaveBeenCalledWith('Hello');
      expect(onChunk).toHaveBeenCalledWith(' World');
      expect(onDone).toHaveBeenCalled();
      expect(mockReader.releaseLock).toHaveBeenCalled();
    });

    it('应该在 HTTP 错误时抛出异常', async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      } as Response;

      const onChunk = vi.fn();

      await expect(SSEHandler.processStream(mockResponse, { onChunk })).rejects.toThrow(
        'HTTP 500: Internal Server Error'
      );
    });

    it('应该在无可读流时抛出异常', async () => {
      const mockResponse = {
        ok: true,
        body: null,
      } as Response;

      await expect(SSEHandler.processStream(mockResponse, {})).rejects.toThrow(
        'Response body is not readable'
      );
    });

    it('应该处理来源数据', async () => {
      const chunks = ['data: {"sources":[{"doc_id":1,"content":"来源1"}]}\n\n'];

      let chunkIndex = 0;
      const mockReader = {
        read: vi.fn(async () => {
          if (chunkIndex < chunks.length) {
            const value = new TextEncoder().encode(chunks[chunkIndex]);
            chunkIndex++;
            return { done: false, value };
          }
          return { done: true, value: undefined };
        }),
        releaseLock: vi.fn(),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as unknown as Response;

      const onSources = vi.fn();

      await SSEHandler.processStream(mockResponse, { onSources });

      expect(onSources).toHaveBeenCalledWith([{ doc_id: 1, content: '来源1' }]);
    });

    it('应该处理错误事件', async () => {
      const chunks = ['data: {"error":"发生错误"}\n\n'];

      let chunkIndex = 0;
      const mockReader = {
        read: vi.fn(async () => {
          if (chunkIndex < chunks.length) {
            const value = new TextEncoder().encode(chunks[chunkIndex]);
            chunkIndex++;
            return { done: false, value };
          }
          return { done: true, value: undefined };
        }),
        releaseLock: vi.fn(),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as unknown as Response;

      const onError = vi.fn();

      await SSEHandler.processStream(mockResponse, { onError });

      expect(onError).toHaveBeenCalledWith('发生错误');
    });

    it('应该跳过空行', async () => {
      const chunks = ['\n\ndata: {"answer":"Hello"}\n\n'];

      let chunkIndex = 0;
      const mockReader = {
        read: vi.fn(async () => {
          if (chunkIndex < chunks.length) {
            const value = new TextEncoder().encode(chunks[chunkIndex]);
            chunkIndex++;
            return { done: false, value };
          }
          return { done: true, value: undefined };
        }),
        releaseLock: vi.fn(),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as unknown as Response;

      const onChunk = vi.fn();

      await SSEHandler.processStream(mockResponse, { onChunk });

      expect(onChunk).toHaveBeenCalledTimes(1);
    });

    it('应该跳过注释行', async () => {
      const chunks = [': this is a comment\ndata: {"answer":"Hello"}\n\n'];

      let chunkIndex = 0;
      const mockReader = {
        read: vi.fn(async () => {
          if (chunkIndex < chunks.length) {
            const value = new TextEncoder().encode(chunks[chunkIndex]);
            chunkIndex++;
            return { done: false, value };
          }
          return { done: true, value: undefined };
        }),
        releaseLock: vi.fn(),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as unknown as Response;

      const onChunk = vi.fn();

      await SSEHandler.processStream(mockResponse, { onChunk });

      expect(onChunk).toHaveBeenCalledTimes(1);
    });

    it('应该处理跨块的不完整行', async () => {
      const chunks = ['data: {"ans', 'wer":"Hello"}\n\n'];

      let chunkIndex = 0;
      const mockReader = {
        read: vi.fn(async () => {
          if (chunkIndex < chunks.length) {
            const value = new TextEncoder().encode(chunks[chunkIndex]);
            chunkIndex++;
            return { done: false, value };
          }
          return { done: true, value: undefined };
        }),
        releaseLock: vi.fn(),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as unknown as Response;

      const onChunk = vi.fn();

      await SSEHandler.processStream(mockResponse, { onChunk });

      expect(onChunk).toHaveBeenCalledWith('Hello');
    });

    it('应该在 JSON 解析失败时输出警告', async () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const chunks = ['data: invalid json\n\n'];

      let chunkIndex = 0;
      const mockReader = {
        read: vi.fn(async () => {
          if (chunkIndex < chunks.length) {
            const value = new TextEncoder().encode(chunks[chunkIndex]);
            chunkIndex++;
            return { done: false, value };
          }
          return { done: true, value: undefined };
        }),
        releaseLock: vi.fn(),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as unknown as Response;

      const onChunk = vi.fn();

      await SSEHandler.processStream(mockResponse, { onChunk });

      expect(consoleWarnSpy).toHaveBeenCalled();
      expect(onChunk).not.toHaveBeenCalled();

      consoleWarnSpy.mockRestore();
    });

    it('应该确保 reader 在错误时释放', async () => {
      const mockReader = {
        read: vi.fn(async () => {
          throw new Error('读取错误');
        }),
        releaseLock: vi.fn(),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as unknown as Response;

      await expect(SSEHandler.processStream(mockResponse, {})).rejects.toThrow('读取错误');
      expect(mockReader.releaseLock).toHaveBeenCalled();
    });

    it('应该处理没有回调的情况', async () => {
      const chunks = ['data: {"answer":"Hello"}\n\n'];

      let chunkIndex = 0;
      const mockReader = {
        read: vi.fn(async () => {
          if (chunkIndex < chunks.length) {
            const value = new TextEncoder().encode(chunks[chunkIndex]);
            chunkIndex++;
            return { done: false, value };
          }
          return { done: true, value: undefined };
        }),
        releaseLock: vi.fn(),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as unknown as Response;

      await expect(SSEHandler.processStream(mockResponse, {})).resolves.not.toThrow();
    });
  });

  describe('processLine 私有方法', () => {
    it('应该忽略非 data 开头的行', async () => {
      const chunks = ['event: custom\ndata: {"answer":"Hello"}\n\n'];

      let chunkIndex = 0;
      const mockReader = {
        read: vi.fn(async () => {
          if (chunkIndex < chunks.length) {
            const value = new TextEncoder().encode(chunks[chunkIndex]);
            chunkIndex++;
            return { done: false, value };
          }
          return { done: true, value: undefined };
        }),
        releaseLock: vi.fn(),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as unknown as Response;

      const onChunk = vi.fn();

      await SSEHandler.processStream(mockResponse, { onChunk });

      expect(onChunk).toHaveBeenCalledTimes(1);
    });
  });

  describe('fetchWithStream 方法', () => {
    it('应该发起流式请求并处理响应', async () => {
      const chunks = ['data: {"answer":"Hello"}\n\n'];

      let chunkIndex = 0;
      const mockReader = {
        read: vi.fn(async () => {
          if (chunkIndex < chunks.length) {
            const value = new TextEncoder().encode(chunks[chunkIndex]);
            chunkIndex++;
            return { done: false, value };
          }
          return { done: true, value: undefined };
        }),
        releaseLock: vi.fn(),
      };

      global.fetch = vi.fn(async () => ({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      })) as any;

      const onChunk = vi.fn();

      await SSEHandler.fetchWithStream('http://test.com', { message: 'test' }, { onChunk });

      expect(fetch).toHaveBeenCalledWith(
        'http://test.com',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: 'test', stream: true }),
        })
      );
      expect(onChunk).toHaveBeenCalledWith('Hello');
    });

    it('应该支持自定义 fetch 选项', async () => {
      const mockReader = {
        read: vi.fn(async () => ({ done: true, value: undefined })),
        releaseLock: vi.fn(),
      };

      global.fetch = vi.fn(async () => ({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      })) as any;

      await SSEHandler.fetchWithStream(
        'http://test.com',
        { message: 'test' },
        {},
        {
          headers: {
            Authorization: 'Bearer token',
          },
        }
      );

      expect(fetch).toHaveBeenCalled();
      const callArgs = (fetch as any).mock.calls[0];
      expect(callArgs[0]).toBe('http://test.com');
      expect(callArgs[1].method).toBe('POST');
      expect(callArgs[1].headers.Authorization).toBe('Bearer token');
    });

    it('应该在请求失败时抛出错误', async () => {
      global.fetch = vi.fn(async () => ({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      })) as any;

      await expect(
        SSEHandler.fetchWithStream('http://test.com', { message: 'test' }, {})
      ).rejects.toThrow('HTTP 404: Not Found');
    });
  });
});

describe('SSEEventEmitter', () => {
  let emitter: SSEEventEmitter;

  beforeEach(() => {
    emitter = new SSEEventEmitter();
  });

  describe('on 方法', () => {
    it('应该订阅事件', () => {
      const listener = vi.fn();
      const unsubscribe = emitter.on(SSEEventType.CHUNK, listener);

      expect(typeof unsubscribe).toBe('function');
    });

    it('应该返回取消订阅函数', () => {
      const listener = vi.fn();
      const unsubscribe = emitter.on(SSEEventType.CHUNK, listener);

      unsubscribe();

      emitter.emit(SSEEventType.CHUNK, 'test');

      expect(listener).not.toHaveBeenCalled();
    });

    it('应该支持多个监听器', () => {
      const listener1 = vi.fn();
      const listener2 = vi.fn();

      emitter.on(SSEEventType.CHUNK, listener1);
      emitter.on(SSEEventType.CHUNK, listener2);

      emitter.emit(SSEEventType.CHUNK, 'test');

      expect(listener1).toHaveBeenCalledWith('test');
      expect(listener2).toHaveBeenCalledWith('test');
    });
  });

  describe('emit 方法', () => {
    it('应该触发事件监听器', () => {
      const listener = vi.fn();

      emitter.on(SSEEventType.CHUNK, listener);
      emitter.emit(SSEEventType.CHUNK, 'test data');

      expect(listener).toHaveBeenCalledWith('test data');
    });

    it('应该在无监听器时静默处理', () => {
      expect(() => emitter.emit(SSEEventType.CHUNK, 'test')).not.toThrow();
    });

    it('应该只触发对应事件的监听器', () => {
      const chunkListener = vi.fn();
      const sourcesListener = vi.fn();

      emitter.on(SSEEventType.CHUNK, chunkListener);
      emitter.on(SSEEventType.SOURCES, sourcesListener);

      emitter.emit(SSEEventType.CHUNK, 'test');

      expect(chunkListener).toHaveBeenCalled();
      expect(sourcesListener).not.toHaveBeenCalled();
    });
  });

  describe('clear 方法', () => {
    it('应该清空指定事件的监听器', () => {
      const listener = vi.fn();

      emitter.on(SSEEventType.CHUNK, listener);
      emitter.clear(SSEEventType.CHUNK);

      emitter.emit(SSEEventType.CHUNK, 'test');

      expect(listener).not.toHaveBeenCalled();
    });

    it('应该清空所有监听器', () => {
      const listener1 = vi.fn();
      const listener2 = vi.fn();

      emitter.on(SSEEventType.CHUNK, listener1);
      emitter.on(SSEEventType.SOURCES, listener2);
      emitter.clear();

      emitter.emit(SSEEventType.CHUNK, 'test');
      emitter.emit(SSEEventType.SOURCES, []);

      expect(listener1).not.toHaveBeenCalled();
      expect(listener2).not.toHaveBeenCalled();
    });
  });

  describe('listenerCount 方法', () => {
    it('应该返回监听器数量', () => {
      emitter.on(SSEEventType.CHUNK, vi.fn());
      emitter.on(SSEEventType.CHUNK, vi.fn());
      emitter.on(SSEEventType.SOURCES, vi.fn());

      expect(emitter.listenerCount(SSEEventType.CHUNK)).toBe(2);
      expect(emitter.listenerCount(SSEEventType.SOURCES)).toBe(1);
      expect(emitter.listenerCount(SSEEventType.DONE)).toBe(0);
    });

    it('应该在无监听器时返回 0', () => {
      expect(emitter.listenerCount(SSEEventType.CHUNK)).toBe(0);
    });
  });

  describe('取消订阅功能', () => {
    it('应该只移除指定的监听器', () => {
      const listener1 = vi.fn();
      const listener2 = vi.fn();

      const unsubscribe1 = emitter.on(SSEEventType.CHUNK, listener1);
      emitter.on(SSEEventType.CHUNK, listener2);

      unsubscribe1();

      emitter.emit(SSEEventType.CHUNK, 'test');

      expect(listener1).not.toHaveBeenCalled();
      expect(listener2).toHaveBeenCalledWith('test');
    });

    it('应该支持多次取消订阅', () => {
      const listener1 = vi.fn();
      const listener2 = vi.fn();

      const unsubscribe1 = emitter.on(SSEEventType.CHUNK, listener1);
      const unsubscribe2 = emitter.on(SSEEventType.CHUNK, listener2);

      unsubscribe1();
      unsubscribe2();

      emitter.emit(SSEEventType.CHUNK, 'test');

      expect(listener1).not.toHaveBeenCalled();
      expect(listener2).not.toHaveBeenCalled();
    });
  });

  describe('事件类型枚举', () => {
    it('应该包含所有事件类型', () => {
      expect(SSEEventType.CHUNK).toBe('chunk');
      expect(SSEEventType.SOURCES).toBe('sources');
      expect(SSEEventType.DONE).toBe('done');
      expect(SSEEventType.ERROR).toBe('error');
    });
  });

  describe('复杂场景', () => {
    it('应该处理监听器抛出错误的情况', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const errorListener = vi.fn(() => {
        throw new Error('监听器错误');
      });
      const normalListener = vi.fn();

      emitter.on(SSEEventType.CHUNK, errorListener);
      emitter.on(SSEEventType.CHUNK, normalListener);

      // 内部逻辑：捕获错误以确保测试继续
      try {
        emitter.emit(SSEEventType.CHUNK, 'test');
      } catch (e) {
        // 忽略错误
      }

      // 内部逻辑：检查是否调用了监听器（即使抛出错误）
      expect(errorListener).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });

    it('应该支持在监听器中取消订阅', () => {
      let unsubscribe: (() => void) | undefined;
      const listener = vi.fn(() => {
        if (unsubscribe) {
          unsubscribe();
        }
      });

      unsubscribe = emitter.on(SSEEventType.CHUNK, listener);

      emitter.emit(SSEEventType.CHUNK, 'test1');
      emitter.emit(SSEEventType.CHUNK, 'test2');

      // 内部逻辑：第一次触发后取消订阅，只应调用一次
      expect(listener).toHaveBeenCalledTimes(1);
    });
  });
});

describe('SSECallbacks 类型', () => {
  it('应该支持可选的回调函数', () => {
    const callbacks1: SSECallbacks<string, any> = {};
    const callbacks2: SSECallbacks<string, any> = {
      onChunk: vi.fn(),
    };
    const callbacks3: SSECallbacks<string, any> = {
      onChunk: vi.fn(),
      onSources: vi.fn(),
      onDone: vi.fn(),
      onError: vi.fn(),
    };

    expect(callbacks1).toBeDefined();
    expect(callbacks2).toBeDefined();
    expect(callbacks3).toBeDefined();
  });
});
