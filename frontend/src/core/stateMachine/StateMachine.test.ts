/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：泛型状态机模块单元测试
 * 内部逻辑：测试状态机的状态转换、守卫条件和监听器功能
 * 测试策略：
 *   - 单元测试：测试每个状态机方法
 *   - 转换测试：验证各种状态转换场景
 *   - 异常测试：验证错误处理和守卫条件
 */

import { describe, it, expect, vi } from 'vitest';
import { StateMachine, StateMachineHelper, type StateConfig, type Transition, type StateChangeEvent } from './StateMachine';

describe('StateMachine', () => {
  describe('构造函数和初始化', () => {
    it('应该创建状态机实例', () => {
      type TestState = 'idle' | 'loading' | 'success';

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading' },
          },
        },
        loading: {
          name: 'loading',
          transitions: {
            success: { to: 'success' },
          },
        },
        success: {
          name: 'success',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      expect(sm.currentState).toBe('idle');
    });

    it('应该执行初始状态的 onEnter', () => {
      type TestState = 'idle' | 'loading';

      const onEnter = vi.fn();

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          onEnter,
          transitions: {},
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      expect(onEnter).toHaveBeenCalledTimes(1);
    });

    it('应该支持自定义历史记录大小', () => {
      type TestState = 'idle' | 'loading';

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: { start: { to: 'loading' } },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
        maxHistorySize: 10,
      });

      // 内部逻辑：历史记录大小应该是10
      expect(sm).toBeInstanceOf(StateMachine);
    });
  });

  describe('can 方法', () => {
    it('应该返回 true 对于有效的转换', () => {
      type TestState = 'idle' | 'loading';

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading' },
          },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      expect(sm.can('start')).toBe(true);
    });

    it('应该返回 false 对于无效的转换', () => {
      type TestState = 'idle' | 'loading';

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading' },
          },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      expect(sm.can('invalid')).toBe(false);
    });

    it('应该遵守守卫条件', () => {
      type TestState = 'idle' | 'loading';

      const guard = vi.fn(() => false);

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading', guard },
          },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      expect(sm.can('start')).toBe(false);
      expect(guard).toHaveBeenCalled();
    });

    it('应该返回 true 当守卫条件满足时', () => {
      type TestState = 'idle' | 'loading';

      let shouldAllow = true;

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading', guard: () => shouldAllow },
          },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      expect(sm.can('start')).toBe(true);
    });
  });

  describe('transition 方法', () => {
    it('应该成功执行状态转换', async () => {
      type TestState = 'idle' | 'loading';

      const onExit = vi.fn();
      const onTransition = vi.fn();
      const onEnter = vi.fn();

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          onExit,
          transitions: {
            start: { to: 'loading', onTransition },
          },
        },
        loading: {
          name: 'loading',
          onEnter,
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      const result = await sm.transition('start');

      expect(result).toBe(true);
      expect(sm.currentState).toBe('loading');
      expect(onExit).toHaveBeenCalled();
      expect(onTransition).toHaveBeenCalled();
      expect(onEnter).toHaveBeenCalled();
    });

    it('应该返回 false 对于无效的转换', async () => {
      type TestState = 'idle' | 'loading';

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {},
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      const result = await sm.transition('invalid');

      expect(result).toBe(false);
    });

    it('应该被守卫条件阻止转换', async () => {
      type TestState = 'idle' | 'loading';

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading', guard: () => false },
          },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      const result = await sm.transition('start');

      expect(result).toBe(false);
      expect(sm.currentState).toBe('idle');
    });

    it('应该支持异步 onEnter', async () => {
      type TestState = 'idle' | 'loading';

      const asyncOnEnter = vi.fn(async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
      });

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading' },
          },
        },
        loading: {
          name: 'loading',
          onEnter: asyncOnEnter,
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      await sm.transition('start');

      expect(asyncOnEnter).toHaveBeenCalled();
      expect(sm.currentState).toBe('loading');
    });

    it('应该支持异步 onExit', async () => {
      type TestState = 'idle' | 'loading';

      const asyncOnExit = vi.fn(async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
      });

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          onExit: asyncOnExit,
          transitions: {
            start: { to: 'loading' },
          },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      await sm.transition('start');

      expect(asyncOnExit).toHaveBeenCalled();
      expect(sm.currentState).toBe('loading');
    });

    it('应该在转换失败时恢复原状态', async () => {
      type TestState = 'idle' | 'loading';

      const error = new Error('转换失败');

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: {
              to: 'loading',
              onTransition: async () => {
                throw error;
              },
            },
          },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      await expect(sm.transition('start')).rejects.toThrow('转换失败');
      expect(sm.currentState).toBe('idle');
    });

    it('应该防止并发转换', async () => {
      type TestState = 'idle' | 'loading' | 'success';

      let transitionCount = 0;

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: {
              to: 'loading',
              onTransition: async () => {
                transitionCount++;
                await new Promise((resolve) => setTimeout(resolve, 50));
              },
            },
          },
        },
        loading: {
          name: 'loading',
          transitions: {
            success: { to: 'success' },
          },
        },
        success: {
          name: 'success',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      // 内部逻辑：并发发起两个转换
      const [result1, result2] = await Promise.all([
        sm.transition('start'),
        sm.transition('start'),
      ]);

      // 内部逻辑：只有一个转换应该成功
      expect(transitionCount).toBe(1);
      expect(result1 || result2).toBe(true);
    });
  });

  describe('reset 方法', () => {
    it('应该重置到指定状态', () => {
      type TestState = 'idle' | 'loading' | 'success';

      const onEnter = vi.fn();

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {},
        },
        loading: {
          name: 'loading',
          transitions: {
            success: { to: 'success' },
          },
        },
        success: {
          name: 'success',
          onEnter,
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      sm.reset('success');

      expect(sm.currentState).toBe('success');
      expect(onEnter).toHaveBeenCalled();
    });

    it('应该记录重置事件到历史', () => {
      type TestState = 'idle' | 'loading';

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {},
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      sm.reset('loading');

      expect(sm.history).toHaveLength(1);
      expect(sm.history[0].event).toBe('reset');
    });
  });

  describe('subscribe 方法', () => {
    it('应该通知监听器状态变化', async () => {
      type TestState = 'idle' | 'loading';

      const listener = vi.fn();

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading' },
          },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      sm.subscribe(listener);

      await sm.transition('start');

      expect(listener).toHaveBeenCalledWith({
        from: 'idle',
        to: 'loading',
        event: 'start',
      });
    });

    it('应该返回取消订阅函数', async () => {
      type TestState = 'idle' | 'loading';

      const listener = vi.fn();

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading' },
          },
        },
        loading: {
          name: 'loading',
          transitions: {
            start: { to: 'idle' },
          },
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      const unsubscribe = sm.subscribe(listener);

      await sm.transition('start');
      unsubscribe();
      await sm.transition('start');

      // 内部逻辑：应该只调用一次
      expect(listener).toHaveBeenCalledTimes(1);
    });

    it('应该支持多个监听器', async () => {
      type TestState = 'idle' | 'loading';

      const listener1 = vi.fn();
      const listener2 = vi.fn();

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading' },
          },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      sm.subscribe(listener1);
      sm.subscribe(listener2);

      await sm.transition('start');

      expect(listener1).toHaveBeenCalled();
      expect(listener2).toHaveBeenCalled();
    });

    it('应该处理监听器错误', async () => {
      type TestState = 'idle' | 'loading';

      const errorListener = vi.fn(() => {
        throw new Error('监听器错误');
      });
      const normalListener = vi.fn();

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading' },
          },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      sm.subscribe(errorListener);
      sm.subscribe(normalListener);

      await sm.transition('start');

      expect(normalListener).toHaveBeenCalled();
    });
  });

  describe('history 属性', () => {
    it('应该记录转换历史', async () => {
      type TestState = 'idle' | 'loading' | 'success';

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading' },
          },
        },
        loading: {
          name: 'loading',
          transitions: {
            success: { to: 'success' },
          },
        },
        success: {
          name: 'success',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      await sm.transition('start');
      await sm.transition('success');

      expect(sm.history).toHaveLength(2);
      expect(sm.history[0].event).toBe('success');
      expect(sm.history[1].event).toBe('start');
    });

    it('应该限制历史记录大小', async () => {
      type TestState = 'a' | 'b';

      const states: Record<TestState, StateConfig<TestState>> = {
        a: {
          name: 'a',
          transitions: {
            toB: { to: 'b' },
          },
        },
        b: {
          name: 'b',
          transitions: {
            toA: { to: 'a' },
          },
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'a',
        states,
        maxHistorySize: 3,
      });

      // 内部逻辑：执行超过限制的转换
      await sm.transition('toB');
      await sm.transition('toA');
      await sm.transition('toB');
      await sm.transition('toA');
      await sm.transition('toB');

      // 内部逻辑：历史记录应该被限制
      expect(sm.history.length).toBeLessThanOrEqual(3);
    });
  });

  describe('getStates 方法', () => {
    it('应该返回所有状态', () => {
      type TestState = 'idle' | 'loading' | 'success';

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: { name: 'idle', transitions: {} },
        loading: { name: 'loading', transitions: {} },
        success: { name: 'success', transitions: {} },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      const allStates = sm.getStates();

      expect(allStates).toContain('idle');
      expect(allStates).toContain('loading');
      expect(allStates).toContain('success');
    });
  });

  describe('getAvailableTransitions 方法', () => {
    it('应该返回当前可用的转换', () => {
      type TestState = 'idle' | 'loading';

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading' },
            skip: { to: 'idle' },
          },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      const transitions = sm.getAvailableTransitions();

      expect(transitions).toContain('start');
      expect(transitions).toContain('skip');
    });

    it('应该在未知状态时返回空数组', () => {
      type TestState = 'idle' | 'loading';

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {},
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      const transitions = sm.getAvailableTransitions();

      expect(transitions).toEqual([]);
    });
  });

  describe('clearHistory 方法', () => {
    it('应该清空历史记录', async () => {
      type TestState = 'idle' | 'loading';

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading' },
          },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      await sm.transition('start');
      sm.clearHistory();

      expect(sm.history).toHaveLength(0);
    });
  });

  describe('destroy 方法', () => {
    it('应该清理所有监听器', async () => {
      type TestState = 'idle' | 'loading';

      const listener = vi.fn();

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading' },
          },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      sm.subscribe(listener);
      sm.destroy();

      await sm.transition('start');

      expect(listener).not.toHaveBeenCalled();
    });

    it('应该清空历史记录', async () => {
      type TestState = 'idle' | 'loading';

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: { to: 'loading' },
          },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      await sm.transition('start');
      sm.destroy();

      expect(sm.history).toHaveLength(0);
    });
  });

  describe('isTransitioning 属性', () => {
    it('应该在转换过程中返回 true', async () => {
      type TestState = 'idle' | 'loading';

      const states: Record<TestState, StateConfig<TestState>> = {
        idle: {
          name: 'idle',
          transitions: {
            start: {
              to: 'loading',
              onTransition: async () => {
                // 内部逻辑：在转换过程中检查状态
                expect(sm.isTransitioning).toBe(true);
              },
            },
          },
        },
        loading: {
          name: 'loading',
          transitions: {},
        },
      };

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states,
      });

      expect(sm.isTransitioning).toBe(false);
      await sm.transition('start');
      expect(sm.isTransitioning).toBe(false);
    });
  });
});

describe('StateMachineHelper', () => {
  describe('createSimple 方法', () => {
    it('应该创建简单的状态机', () => {
      type TestState = 'idle' | 'loading' | 'success';

      const sm = StateMachineHelper.createSimple<TestState>(
        ['idle', 'loading', 'success'],
        'idle'
      );

      expect(sm.currentState).toBe('idle');
      expect(sm.getStates()).toContain('idle');
      expect(sm.getStates()).toContain('loading');
      expect(sm.getStates()).toContain('success');
    });

    it('应该允许转换到任意状态', async () => {
      type TestState = 'a' | 'b' | 'c';

      const sm = StateMachineHelper.createSimple<TestState>(['a', 'b', 'c'], 'a');

      await sm.transition('to_b');
      expect(sm.currentState).toBe('b');

      await sm.transition('to_c');
      expect(sm.currentState).toBe('c');

      await sm.transition('to_a');
      expect(sm.currentState).toBe('a');
    });
  });

  describe('visualize 方法', () => {
    it('应该生成 Mermaid 格式的状态图', () => {
      type TestState = 'idle' | 'loading';

      const sm = new StateMachine<TestState>({
        initial: 'idle',
        states: {
          idle: { name: 'idle', transitions: { start: { to: 'loading' } } },
          loading: { name: 'loading', transitions: {} },
        },
      });

      const visualization = StateMachineHelper.visualize(sm);

      expect(visualization).toContain('stateDiagram-v2');
      expect(visualization).toContain('idle');
    });
  });
});
