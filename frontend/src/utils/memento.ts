/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：备忘录模式工具模块
 * 内部逻辑：实现状态快照和撤销/恢复功能
 * 设计模式：备忘录模式（Memento Pattern）
 * 设计原则：SOLID - 单一职责原则
 */

/**
 * 内部类型：状态快照接口
 */
export interface Memento<T> {
  /**
   * 属性级注释：快照保存的状态数据
   */
  state: T;

  /**
   * 属性级注释：快照创建时间戳
   */
  timestamp: number;

  /**
   * 属性级注释：快照描述（可选）
   */
  description?: string;
}

/**
 * 内部类型：状态快照元数据
 */
interface SnapshotMetadata {
  /**
   * 属性级注释：快照索引
   */
  index: number;

  /**
   * 属性级注释：快照描述
   */
  description?: string;

  /**
   * 属性级注释：快照创建时间
   */
  timestamp: number;
}

/**
 * 类级注释：备忘录管理器
 * 设计模式：备忘录模式（Memento Pattern）- 负责人（Caretaker）
 * 职责：
 *   1. 管理状态快照历史
 *   2. 提供撤销/恢复功能
 *   3. 控制历史记录大小
 *
 * 泛型参数：
 *   T - 状态数据类型
 *
 * 设计优势：
 *   - 支持操作撤销和恢复
 *   - 不破坏原发器对象的封装
 *   - 可配置历史记录大小限制
 */
export class Caretaker<T> {
  /**
   * 内部变量：历史快照列表
   */
  private history: Memento<T>[] = [];

  /**
   * 内部变量：当前快照索引
   */
  private currentIndex: number = -1;

  /**
   * 内部变量：最大历史记录数
   */
  private maxHistory: number;

  /**
   * 内部变量：快照元数据列表
   */
  private metadata: SnapshotMetadata[] = [];

  /**
   * 函数级注释：构造函数
   *
   * @param maxHistory - 最大历史记录数（默认50）
   */
  constructor(maxHistory: number = 50) {
    this.maxHistory = maxHistory;
  }

  /**
   * 函数级注释：保存状态快照
   * 内部逻辑：创建快照 -> 添加到历史 -> 更新索引 -> 清理过期记录
   *
   * @param state - 要保存的状态
   * @param description - 快照描述（可选）
   * @returns 快照索引
   */
  save(state: T, description?: string): number {
    // 内部逻辑：创建快照
    const snapshot: Memento<T> = {
      // 内部逻辑：深拷贝状态，避免引用问题
      state: JSON.parse(JSON.stringify(state)),
      timestamp: Date.now(),
      description
    };

    // 内部逻辑：如果在中间位置保存，清除后续历史
    if (this.currentIndex < this.history.length - 1) {
      this.history = this.history.slice(0, this.currentIndex + 1);
      this.metadata = this.metadata.slice(0, this.currentIndex + 1);
    }

    // 内部逻辑：添加到历史
    this.history.push(snapshot);
    this.currentIndex = this.history.length - 1;

    // 内部逻辑：添加元数据
    this.metadata.push({
      index: this.currentIndex,
      description,
      timestamp: snapshot.timestamp
    });

    // 内部逻辑：清理过期记录
    this._pruneHistory();

    return this.currentIndex;
  }

  /**
   * 函数级注释：撤销到上一个状态
   * 内部逻辑：检查可撤销 -> 减少索引 -> 返回快照
   *
   * @returns 上一个状态或null（如果无法撤销）
   */
  undo(): T | null {
    // Guard Clauses：无法撤销
    if (!this.canUndo()) {
      return null;
    }

    // 内部逻辑：移动到上一个状态
    this.currentIndex--;
    return this.getCurrentState();
  }

  /**
   * 函数级注释：恢复到下一个状态
   * 内部逻辑：检查可恢复 -> 增加索引 -> 返回快照
   *
   * @returns 下一个状态或null（如果无法恢复）
   */
  redo(): T | null {
    // Guard Clauses：无法恢复
    if (!this.canRedo()) {
      return null;
    }

    // 内部逻辑：移动到下一个状态
    this.currentIndex++;
    return this.getCurrentState();
  }

  /**
   * 函数级注释：跳转到指定索引的状态
   *
   * @param index - 目标索引
   * @returns 目标状态或null（如果索引无效）
   */
  goTo(index: number): T | null {
    // Guard Clauses：索引无效
    if (index < 0 || index >= this.history.length) {
      return null;
    }

    this.currentIndex = index;
    return this.getCurrentState();
  }

  /**
   * 函数级注释：获取当前状态
   *
   * @returns 当前状态或null
   */
  getCurrentState(): T | null {
    if (this.currentIndex < 0 || this.currentIndex >= this.history.length) {
      return null;
    }

    // 内部逻辑：返回深拷贝，避免外部修改
    return JSON.parse(JSON.stringify(this.history[this.currentIndex].state));
  }

  /**
   * 函数级注释：检查是否可以撤销
   *
   * @returns 是否可以撤销
   */
  canUndo(): boolean {
    return this.currentIndex > 0;
  }

  /**
   * 函数级注释：检查是否可以恢复
   *
   * @returns 是否可以恢复
   */
  canRedo(): boolean {
    return this.currentIndex < this.history.length - 1;
  }

  /**
   * 函数级注释：获取历史记录元数据
   *
   * @returns 元数据列表
   */
  getHistoryMetadata(): SnapshotMetadata[] {
    return [...this.metadata];
  }

  /**
   * 函数级注释：获取历史记录数量
   *
   * @returns 历史记录数量
   */
  getHistorySize(): number {
    return this.history.length;
  }

  /**
   * 函数级注释：清除所有历史记录
   */
  clear(): void {
    this.history = [];
    this.metadata = [];
    this.currentIndex = -1;
  }

  /**
   * 函数级注释：设置最大历史记录数
   *
   * @param maxHistory - 最大历史记录数
   */
  setMaxHistory(maxHistory: number): void {
    this.maxHistory = maxHistory;
    this._pruneHistory();
  }

  /**
   * 私有函数级注释：清理过期历史记录
   * 内部逻辑：如果历史记录超过最大值，删除最早的记录
   */
  private _pruneHistory(): void {
    while (this.history.length > this.maxHistory) {
      this.history.shift();
      this.metadata.shift();
      this.currentIndex--;
    }

    // 内部逻辑：确保索引不小于-1
    if (this.currentIndex < -1) {
      this.currentIndex = -1;
    }
  }

  /**
   * 函数级注释：获取当前索引
   *
   * @returns 当前索引
   */
  getCurrentIndex(): number {
    return this.currentIndex;
  }
}

/**
 * 类级注释：带自动保存的状态管理器
 * 设计模式：备忘录模式 + 观察者模式
 * 职责：
 *   1. 包装状态对象
 *   2. 状态变化时自动创建快照
 *   3. 提供撤销/恢复接口
 */
export class HistoryState<T extends object> {
  /**
   * 内部变量：当前状态
   */
  private _state: T;

  /**
   * 内部变量：备忘录管理器
   */
  private caretaker: Caretaker<T>;

  /**
   * 内部变量：是否启用自动保存
   */
  private autoSave: boolean;

  /**
   * 内部变量：状态变化监听器
   */
  private listeners: Set<(state: T) => void> = new Set();

  /**
   * 函数级注释：构造函数
   *
   * @param initialState - 初始状态
   * @param maxHistory - 最大历史记录数
   * @param autoSave - 是否自动保存（默认true）
   */
  constructor(
    initialState: T,
    maxHistory: number = 50,
    autoSave: boolean = true
  ) {
    this._state = initialState;
    this.caretaker = new Caretaker<T>(maxHistory);
    this.autoSave = autoSave;

    // 内部逻辑：保存初始状态
    if (autoSave) {
      this.caretaker.save(this._state, '初始状态');
    }
  }

  /**
   * 函数级注释：获取当前状态
   */
  get state(): T {
    return this._state;
  }

  /**
   * 函数级注释：设置状态
   * 内部逻辑：更新状态 -> 自动保存 -> 通知监听器
   */
  set state(value: T) {
    this._state = value;

    if (this.autoSave) {
      this.caretaker.save(value);
    }

    this._notifyListeners();
  }

  /**
   * 函数级注释：更新状态的部分属性
   * 内部逻辑：合并属性 -> 自动保存 -> 通知监听器
   *
   * @param partial - 部分状态更新
   * @param description - 快照描述（可选）
   */
  update(partial: Partial<T>, description?: string): void {
    this._state = { ...this._state, ...partial } as T;

    if (this.autoSave) {
      this.caretaker.save(this._state, description);
    }

    this._notifyListeners();
  }

  /**
   * 函数级注释：撤销到上一个状态
   */
  undo(): boolean {
    const prevState = this.caretaker.undo();
    if (prevState !== null) {
      this._state = prevState;
      this._notifyListeners();
      return true;
    }
    return false;
  }

  /**
   * 函数级注释：恢复到下一个状态
   */
  redo(): boolean {
    const nextState = this.caretaker.redo();
    if (nextState !== null) {
      this._state = nextState;
      this._notifyListeners();
      return true;
    }
    return false;
  }

  /**
   * 函数级注释：检查是否可以撤销
   */
  canUndo(): boolean {
    return this.caretaker.canUndo();
  }

  /**
   * 函数级注释：检查是否可以恢复
   */
  canRedo(): boolean {
    return this.caretaker.canRedo();
  }

  /**
   * 函数级注释：手动创建快照
   */
  snapshot(description?: string): void {
    this.caretaker.save(this._state, description);
  }

  /**
   * 函数级注释：获取历史记录元数据
   */
  getHistory() {
    return this.caretaker.getHistoryMetadata();
  }

  /**
   * 函数级注释：添加状态变化监听器
   */
  listen(listener: (state: T) => void): () => void {
    this.listeners.add(listener);

    // 内部逻辑：返回取消监听函数
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * 私有函数级注释：通知所有监听器
   */
  private _notifyListeners(): void {
    for (const listener of this.listeners) {
      listener(this._state);
    }
  }
}

/**
 * 导出类型
 */
export type { SnapshotMetadata };
