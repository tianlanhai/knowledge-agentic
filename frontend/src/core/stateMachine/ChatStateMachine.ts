/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：聊天状态机专用实现模块
 * 内部逻辑：为聊天功能定义专门的状态机，包含聊天会话的所有可能状态和转换
 * 设计模式：状态模式（State Pattern）
 * 设计原则：开闭原则、单一职责原则
 */

import { StateMachine, StateConfig, Transition } from './StateMachine';

/**
 * 类级注释：聊天状态枚举
 * 属性：聊天会话的所有可能状态
 */
export type ChatState =
  /** 空闲状态 - 等待用户输入 */
  | 'idle'
  /** 发送消息中 - 正在发送用户消息 */
  | 'sending'
  /** 接收响应中 - 正在接收 AI 响应 */
  | 'receiving'
  /** 流式响应中 - 正在接收流式响应 */
  | 'streaming'
  /** 成功状态 - 消息处理完成 */
  | 'success'
  /** 错误状态 - 发生错误 */
  | 'error'
  /** 重试中 - 正在重试 */
  | 'retrying';

/**
 * 类级注释：聊天事件枚举
 * 属性：触发状态转换的所有可能事件
 */
export type ChatEvent =
  /** 发送消息 */
  | 'send'
  /** 开始接收响应 */
  | 'receive_start'
  /** 接收流式数据 */
  | 'stream_chunk'
  /** 流式接收完成 */
  | 'stream_end'
  /** 操作成功 */
  | 'success'
  /** 发生错误 */
  | 'error'
  /** 重试 */
  | 'retry'
  /** 取消 */
  | 'cancel'
  /** 重置 */
  | 'reset';

/**
 * 类级注释：聊天状态上下文
 * 属性：状态转换时携带的额外信息
 */
export interface ChatStateContext {
  /** 内部属性：当前错误信息 */
  error?: Error;
  /** 内部属性：重试次数 */
  retryCount?: number;
  /** 内部属性：最大重试次数 */
  maxRetries?: number;
  /** 内部属性：是否正在取消 */
  isCancelling?: boolean;
}

/**
 * 类级注释：聊天状态机类
 * 内部逻辑：管理聊天会话状态，提供状态转换和监听 API
 * 设计模式：状态模式（State Pattern）
 *
 * @example
 * ```typescript
 * const chatSM = new ChatStateMachine();
 * chatSM.subscribe(({ from, to, event }) => {
 *   console.log(`状态: ${from} -> ${to}, 事件: ${event}`);
 * });
 * await chatSM.send();
 * ```
 */
export class ChatStateMachine {
  /** 内部变量：底层状态机实例 */
  private _stateMachine: StateMachine<ChatState>;

  /** 内部变量：状态上下文 */
  private _context: ChatStateContext;

  /** 内部变量：取消控制器 */
  private _abortController: AbortController | null;

  /**
   * 函数级注释：构造函数
   * 返回值：聊天状态机实例
   */
  constructor() {
    // 内部逻辑：初始化上下文
    this._context = {
      retryCount: 0,
      maxRetries: 3
    };
    this._abortController = null;

    // 内部逻辑：创建状态机配置
    const states = this._createStateConfigs();

    // 内部逻辑：初始化底层状态机
    this._stateMachine = new StateMachine<ChatState>({
      initial: 'idle',
      states,
      maxHistorySize: 100
    });
  }

  /**
   * 函数级注释：获取当前状态
   * 返回值：当前聊天状态
   */
  get currentState(): ChatState {
    return this._stateMachine.currentState;
  }

  /**
   * 函数级注释：获取状态上下文
   * 返回值：状态上下文对象
   */
  get context(): Readonly<ChatStateContext> {
    return { ...this._context };
  }

  /**
   * 函数级注释：获取是否在流式响应状态
   * 返回值：是否正在流式响应
   */
  get isStreaming(): boolean {
    return this._stateMachine.currentState === 'streaming';
  }

  /**
   * 函数级注释：获取是否在加载状态
   * 返回值：是否正在加载
   */
  get isLoading(): boolean {
    return ['sending', 'receiving', 'streaming', 'retrying'].includes(
      this._stateMachine.currentState
    );
  }

  /**
   * 函数级注释：获取是否有错误
   * 返回值：是否处于错误状态
   */
  get hasError(): boolean {
    return this._stateMachine.currentState === 'error';
  }

  /**
   * 函数级注释：获取取消控制器
   * 返回值：AbortController 实例
   */
  get abortController(): AbortController | null {
    return this._abortController;
  }

  /**
   * 函数级注释：发送消息事件
   * 返回值：转换是否成功
   */
  async send(): Promise<boolean> {
    return await this._stateMachine.transition('send');
  }

  /**
   * 函数级注释：接收响应开始事件
   * 返回值：转换是否成功
   */
  async receiveStart(): Promise<boolean> {
    return await this._stateMachine.transition('receive_start');
  }

  /**
   * 函数级注释：接收流式数据块事件
   * 返回值：转换是否成功
   */
  async streamChunk(): Promise<boolean> {
    return await this._stateMachine.transition('stream_chunk');
  }

  /**
   * 函数级注释：流式接收结束事件
   * 返回值：转换是否成功
   */
  async streamEnd(): Promise<boolean> {
    return await this._stateMachine.transition('stream_end');
  }

  /**
   * 函数级注释：成功事件
   * 返回值：转换是否成功
   */
  async success(): Promise<boolean> {
    // 内部逻辑：重置重试计数
    this._context.retryCount = 0;
    return await this._stateMachine.transition('success');
  }

  /**
   * 函数级注释：错误事件
   * 参数：
   *   error - 错误对象
   * 返回值：转换是否成功
   */
  async error(error: Error): Promise<boolean> {
    this._context.error = error;
    return await this._stateMachine.transition('error');
  }

  /**
   * 函数级注释：重试事件
   * 返回值：转换是否成功
   */
  async retry(): Promise<boolean> {
    const maxRetries = this._context.maxRetries ?? 3;

    // 内部逻辑：检查是否超过最大重试次数
    if (this._context.retryCount! >= maxRetries) {
      return await this._stateMachine.transition('error');
    }

    this._context.retryCount = (this._context.retryCount ?? 0) + 1;
    return await this._stateMachine.transition('retry');
  }

  /**
   * 函数级注释：取消事件
   * 返回值：转换是否成功
   */
  async cancel(): Promise<boolean> {
    // 内部逻辑：取消当前请求
    this._abortController?.abort();
    this._abortController = null;

    return await this._stateMachine.transition('cancel');
  }

  /**
   * 函数级注释：重置事件
   * 返回值：void
   */
  reset(): void {
    this._context = {
      retryCount: 0,
      maxRetries: 3
    };
    this._abortController = null;
    this._stateMachine.reset('idle');
  }

  /**
   * 函数级注释：监听状态变更
   * 参数：
   *   listener - 状态变更监听函数
   * 返回值：取消监听的函数
   */
  subscribe(
    listener: (event: {
      from: ChatState;
      to: ChatState;
      event: ChatEvent;
    }) => void
  ): () => void {
    return this._stateMachine.subscribe(listener);
  }

  /**
   * 函数级注释：触发状态转换
   * 参数：
   *   event - 事件名称
   * 返回值：转换是否成功
   */
  async transition(event: ChatEvent): Promise<boolean> {
    return await this._stateMachine.transition(event);
  }

  /**
   * 函数级注释：检查是否可以执行指定事件
   * 参数：
   *   event - 事件名称
   * 返回值：是否可以执行
   */
  can(event: ChatEvent): boolean {
    return this._stateMachine.can(event);
  }

  /**
   * 函数级注释：获取可用的转换事件
   * 返回值：可用事件列表
   */
  getAvailableEvents(): ChatEvent[] {
    const transitions = this._stateMachine.getAvailableTransitions();
    return transitions as ChatEvent[];
  }

  /**
   * 函数级注释：创建新的 AbortController
   * 返回值：AbortController 实例
   */
  createAbortController(): AbortController {
    this._abortController = new AbortController();
    return this._abortController;
  }

  /**
   * 函数级注释：获取状态机历史
   * 返回值：状态转换历史
   */
  getHistory() {
    return this._stateMachine.history;
  }

  /**
   * 函数级注释：创建状态配置（内部方法）
   * 返回值：状态配置映射
   */
  private _createStateConfigs(): Record<ChatState, StateConfig<ChatState>> {
    return {
      idle: {
        name: 'idle',
        onEnter: () => {
          // 内部逻辑：进入空闲状态时清理
          this._abortController = null;
        },
        transitions: {
          send: {
            to: 'sending',
            onTransition: () => {
              // 内部逻辑：准备发送消息
              this.createAbortController();
            }
          }
        }
      },

      sending: {
        name: 'sending',
        onEnter: () => {
          // 内部逻辑：开始发送
        },
        transitions: {
          receive_start: {
            to: 'receiving'
          },
          error: {
            to: 'error'
          },
          cancel: {
            to: 'idle',
            guard: () => !this._context.isCancelling
          }
        }
      },

      receiving: {
        name: 'receiving',
        onEnter: () => {
          // 内部逻辑：开始接收响应
        },
        transitions: {
          stream_chunk: {
            to: 'streaming'
          },
          success: {
            to: 'success'
          },
          error: {
            to: 'error'
          },
          cancel: {
            to: 'idle'
          }
        }
      },

      streaming: {
        name: 'streaming',
        onEnter: () => {
          // 内部逻辑：开始流式接收
        },
        transitions: {
          stream_chunk: {
            to: 'streaming', // 自转换，继续流式接收
            onTransition: () => {
              // 内部逻辑：处理新的数据块
            }
          },
          stream_end: {
            to: 'success'
          },
          error: {
            to: 'error'
          },
          cancel: {
            to: 'idle'
          }
        }
      },

      success: {
        name: 'success',
        onEnter: () => {
          // 内部逻辑：处理成功，短暂延迟后返回空闲
        },
        transitions: {
          send: {
            to: 'sending'
          },
          reset: {
            to: 'idle'
          }
        }
      },

      error: {
        name: 'error',
        onEnter: () => {
          // 内部逻辑：处理错误
        },
        transitions: {
          retry: {
            to: 'retrying',
            guard: () => {
              const maxRetries = this._context.maxRetries ?? 3;
              return (this._context.retryCount ?? 0) < maxRetries;
            }
          },
          reset: {
            to: 'idle'
          },
          send: {
            to: 'sending'
          }
        }
      },

      retrying: {
        name: 'retrying',
        onEnter: () => {
          // 内部逻辑：准备重试，创建新的 AbortController
          this.createAbortController();
        },
        transitions: {
          receive_start: {
            to: 'receiving'
          },
          error: {
            to: 'error'
          }
        }
      }
    };
  }

  /**
   * 函数级注释：销毁状态机
   * 返回值：void
   */
  destroy(): void {
    this._abortController?.abort();
    this._stateMachine.destroy();
  }
}

/**
 * 类级注释：聊天状态机工厂类
 * 内部逻辑：提供创建聊天状态机的静态方法
 */
export class ChatStateMachineFactory {
  /**
   * 函数级注释：创建新的聊天状态机实例
   * 返回值：聊天状态机实例
   */
  static create(): ChatStateMachine {
    return new ChatStateMachine();
  }

  /**
   * 函数级注释：创建带有自定义配置的聊天状态机
   * 参数：
   *   config - 自定义配置
   * 返回值：聊天状态机实例
   */
  static createWithConfig(config: {
    maxRetries?: number;
    initial?: ChatState;
  }): ChatStateMachine {
    const sm = new ChatStateMachine();
    if (config.maxRetries) {
      sm['_context'].maxRetries = config.maxRetries;
    }
    if (config.initial && config.initial !== 'idle') {
      sm.reset();
      sm['_stateMachine'].reset(config.initial);
    }
    return sm;
  }
}

/**
 * 类级注释：聊天状态机钩子辅助类
 * 内部逻辑：为 React Hook 提供状态机管理
 */
export class ChatStateMachineHookHelper {
  /**
   * 函数级注释：将状态机转换为 React 可用的状态
   * 参数：
   *   sm - 聊天状态机实例
   * 返回值：状态快照
   */
  static toSnapshot(sm: ChatStateMachine) {
    return {
      currentState: sm.currentState,
      isStreaming: sm.isStreaming,
      isLoading: sm.isLoading,
      hasError: sm.hasError,
      context: sm.context,
      can: (event: ChatEvent) => sm.can(event),
      availableEvents: sm.getAvailableEvents()
    };
  }
}
