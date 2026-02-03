/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：泛型状态机实现模块
 * 内部逻辑：提供类型安全的状态机基础实现，支持状态转换、守卫和副作用
 * 设计模式：状态模式（State Pattern）
 * 设计原则：开闭原则、单一职责原则
 */

/**
 * 类级注释：状态转换定义接口
 * 属性：目标状态、守卫条件、转换时的副作用
 */
export interface Transition<TState extends string> {
  /** 内部属性：目标状态 */
  to: TState;
  /** 内部属性：守卫条件函数，返回 true 允许转换 */
  guard?: () => boolean;
  /** 内部属性：转换前执行的副作用 */
  onTransition?: () => void | Promise<void>;
}

/**
 * 类级注释：状态配置接口
 * 属性：状态名称、入口/出口动作、允许的转换
 */
export interface StateConfig<TState extends string> {
  /** 内部属性：状态名称 */
  name: TState;
  /** 内部属性：进入状态时执行的动作 */
  onEnter?: () => void | Promise<void>;
  /** 内部属性：离开状态时执行的动作 */
  onExit?: () => void | Promise<void>;
  /** 内部属性：从当前状态允许的转换映射 */
  transitions: Record<string, Transition<TState>>;
}

/**
 * 类级注释：状态变更事件数据
 * 属性：前一状态、新状态、触发的事件
 */
export interface StateChangeEvent<TState extends string> {
  /** 内部属性：前一状态 */
  from: TState;
  /** 内部属性：新状态 */
  to: TState;
  /** 内部属性：触发转换的事件名称 */
  event: string;
}

/**
 * 类级注释：泛型状态机类
 * 内部逻辑：管理状态和转换，提供类型安全的状态转换 API
 * 设计模式：状态模式（State Pattern）
 *
 * @template TState - 状态类型，必须是字符串字面量类型
 *
 * @example
 * ```typescript
 * type AppState = 'idle' | 'loading' | 'success' | 'error';
 * const sm = new StateMachine<AppState>({
 *   initial: 'idle',
 *   states: {
 *     idle: {
 *       name: 'idle',
 *       onEnter: () => console.log('进入空闲状态'),
 *       transitions: {
 *         fetch: { to: 'loading' }
 *       }
 *     },
 *     loading: {
 *       name: 'loading',
 *       transitions: {
 *         success: { to: 'success' },
 *         error: { to: 'error' }
 *       }
 *     }
 *   }
 * });
 * ```
 */
export class StateMachine<TState extends string> {
  /** 内部变量：当前状态 */
  private _currentState: TState;

  /** 内部变量：状态配置映射 */
  private _states: Map<TState, StateConfig<TState>>;

  /** 内部变量：状态变更监听器 */
  private _listeners: Set<(event: StateChangeEvent<TState>) => void>;

  /** 内部变量：是否正在转换中（防止并发转换） */
  private _isTransitioning: boolean;

  /** 内部变量：状态机转换历史（用于调试和撤销） */
  private _history: StateChangeEvent<TState>[];

  /** 内部变量：最大历史记录数 */
  private readonly _maxHistorySize: number;

  /**
   * 函数级注释：构造函数
   * 参数：
   *   config - 状态机配置
   * 返回值：状态机实例
   */
  constructor(config: {
    /** 初始状态 */
    initial: TState;
    /** 状态配置映射 */
    states: Record<TState, StateConfig<TState>>;
    /** 最大历史记录数（默认 50） */
    maxHistorySize?: number;
  }) {
    // 内部逻辑：初始化状态
    this._currentState = config.initial;
    this._states = new Map(Object.entries(config.states) as [TState, StateConfig<TState>][]);
    this._listeners = new Set();
    this._isTransitioning = false;
    this._history = [];
    this._maxHistorySize = config.maxHistorySize ?? 50;

    // 内部逻辑：执行初始状态的 onEnter
    const initialState = this._states.get(this._currentState);
    initialState?.onEnter?.();
  }

  /**
   * 函数级注释：获取当前状态
   * 返回值：当前状态值
   */
  get currentState(): TState {
    return this._currentState;
  }

  /**
   * 函数级注释：获取状态机历史
   * 返回值：状态转换历史记录（按时间倒序）
   */
  get history(): readonly StateChangeEvent<TState>[] {
    return [...this._history].reverse();
  }

  /**
   * 函数级注释：检查是否正在转换中
   * 返回值：是否转换中
   */
  get isTransitioning(): boolean {
    return this._isTransitioning;
  }

  /**
   * 函数级注释：检查是否可以转换到指定状态
   * 参数：
   *   event - 触发转换的事件名称
   * 返回值：是否可以转换
   */
  can(event: string): boolean {
    // 内部逻辑：获取当前状态配置
    const currentConfig = this._states.get(this._currentState);
    if (!currentConfig) return false;

    // 内部逻辑：检查是否有对应的转换
    const transition = currentConfig.transitions[event];
    if (!transition) return false;

    // 内部逻辑：检查守卫条件
    if (transition.guard && !transition.guard()) {
      return false;
    }

    return true;
  }

  /**
   * 函数级注释：执行状态转换
   * 参数：
   *   event - 触发转换的事件名称
   * 返回值：转换是否成功
   * 异常：Error - 转换被守卫阻止或目标状态不存在时抛出
   */
  async transition(event: string): Promise<boolean> {
    // 内部逻辑：防止并发转换
    if (this._isTransitioning) {
      console.warn(`[StateMachine] 转换正在进行中，忽略事件: ${event}`);
      return false;
    }

    // 内部逻辑：获取当前状态配置
    const currentConfig = this._states.get(this._currentState);
    if (!currentConfig) {
      throw new Error(`[StateMachine] 当前状态 ${this._currentState} 的配置不存在`);
    }

    // 内部逻辑：获取转换配置
    const transition = currentConfig.transitions[event];
    if (!transition) {
      console.warn(`[StateMachine] 从状态 ${this._currentState} 没有事件 ${event} 的转换`);
      return false;
    }

    // 内部逻辑：检查守卫条件
    if (transition.guard && !transition.guard()) {
      console.warn(`[StateMachine] 转换被守卫阻止: ${event}`);
      return false;
    }

    // 内部逻辑：获取目标状态配置
    const targetConfig = this._states.get(transition.to);
    if (!targetConfig) {
      throw new Error(`[StateMachine] 目标状态 ${transition.to} 的配置不存在`);
    }

    // 内部逻辑：开始转换
    this._isTransitioning = true;
    const previousState = this._currentState;

    try {
      // 内部逻辑：执行当前状态的 onExit
      await currentConfig.onExit?.();

      // 内部逻辑：执行转换时的副作用
      await transition.onTransition?.();

      // 内部逻辑：更新状态
      this._currentState = transition.to;

      // 内部逻辑：执行目标状态的 onEnter
      await targetConfig.onEnter?.();

      // 内部逻辑：记录历史
      const changeEvent: StateChangeEvent<TState> = {
        from: previousState,
        to: this._currentState,
        event
      };
      this._addToHistory(changeEvent);

      // 内部逻辑：通知监听器
      this._notifyListeners(changeEvent);

      return true;
    } catch (error) {
      // 内部逻辑：转换失败，恢复原状态
      this._currentState = previousState;
      console.error(`[StateMachine] 转换失败:`, error);
      throw error;
    } finally {
      this._isTransitioning = false;
    }
  }

  /**
   * 函数级注释：重置到指定状态
   * 参数：
   *   state - 目标状态
   * 返回值：void
   */
  reset(state: TState): void {
    const previousState = this._currentState;
    this._currentState = state;

    // 内部逻辑：执行目标状态的 onEnter
    const targetConfig = this._states.get(state);
    targetConfig?.onEnter?.();

    // 内部逻辑：记录重置事件
    const changeEvent: StateChangeEvent<TState> = {
      from: previousState,
      to: state,
      event: 'reset'
    };
    this._addToHistory(changeEvent);
    this._notifyListeners(changeEvent);
  }

  /**
   * 函数级注释：监听状态变更
   * 参数：
   *   listener - 状态变更监听函数
   * 返回值：取消监听的函数
   */
  subscribe(listener: (event: StateChangeEvent<TState>) => void): () => void {
    this._listeners.add(listener);

    // 内部逻辑：返回取消订阅函数
    return () => {
      this._listeners.delete(listener);
    };
  }

  /**
   * 函数级注释：获取所有可能的状态
   * 返回值：状态列表
   */
  getStates(): TState[] {
    return Array.from(this._states.keys());
  }

  /**
   * 函数级注释：获取从当前状态允许的转换
   * 返回值：转换事件列表
   */
  getAvailableTransitions(): string[] {
    const currentConfig = this._states.get(this._currentState);
    if (!currentConfig) return [];

    return Object.keys(currentConfig.transitions);
  }

  /**
   * 函数级注释：添加历史记录（内部方法）
   * 参数：
   *   event - 状态变更事件
   * 返回值：void
   */
  private _addToHistory(event: StateChangeEvent<TState>): void {
    this._history.push(event);

    // 内部逻辑：限制历史记录大小
    if (this._history.length > this._maxHistorySize) {
      this._history.shift();
    }
  }

  /**
   * 函数级注释：通知所有监听器（内部方法）
   * 参数：
   *   event - 状态变更事件
   * 返回值：void
   */
  private _notifyListeners(event: StateChangeEvent<TState>): void {
    this._listeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('[StateMachine] 监听器执行失败:', error);
      }
    });
  }

  /**
   * 函数级注释：清空历史记录
   * 返回值：void
   */
  clearHistory(): void {
    this._history = [];
  }

  /**
   * 函数级注释：销毁状态机，清理所有监听器
   * 返回值：void
   */
  destroy(): void {
    this._listeners.clear();
    this._history = [];
  }
}

/**
 * 类级注释：状态机工具类
 * 内部逻辑：提供状态机创建和操作的辅助方法
 */
export class StateMachineHelper {
  /**
   * 函数级注释：创建简单状态机（只有状态，没有转换）
   * 参数：
   *   states - 状态列表
   *   initial - 初始状态
   * 返回值：状态机实例
   */
  static createSimple<TState extends string>(
    states: TState[],
    initial: TState
  ): StateMachine<TState> {
    const stateConfigs: Record<TState, StateConfig<TState>> = {} as any;

    // 内部逻辑：为每个状态创建配置，允许转换到任意状态
    for (const state of states) {
      const transitions: Record<string, Transition<TState>> = {};
      for (const target of states) {
        if (target !== state) {
          transitions[`to_${target}`] = { to: target };
        }
      }
      stateConfigs[state] = {
        name: state,
        transitions
      };
    }

    return new StateMachine({
      initial,
      states: stateConfigs
    });
  }

  /**
   * 函数级注释：创建状态机可视化字符串
   * 参数：
   *   stateMachine - 状态机实例
   * 返回值：Mermaid 格式的状态图字符串
   */
  static visualize<TState extends string>(
    stateMachine: StateMachine<TState>
  ): string {
    const states = stateMachine.getStates();
    const lines: string[] = ['stateDiagram-v2'];

    // 内部逻辑：输出所有状态
    for (const state of states) {
      lines.push(`  [*] --> ${state === stateMachine.currentState ? state : states[0]}`);
    }

    // 内部逻辑：输出当前状态标记
    lines.push(`  state ${stateMachine.currentState} {
    [*] --> active
  }`);

    return lines.join('\n');
  }
}
