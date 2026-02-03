/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：光泽动画组合式模块
 * 内部逻辑：统一管理光泽动画效果，消除代码重复
 * 设计模式：组合模式（Composite Pattern）+ 共享模式
 * 设计原则：DRY原则（Don't Repeat Yourself）
 *
 * 实现说明：
 *   - 创建共享的光泽动画逻辑
 *   - 支持多个组件复用
 *   - 提供配置选项
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { CSSProperties } from 'react';

/**
 * 接口：光泽动画配置
 */
export interface GlossAnimationConfig {
  /** 是否启用动画 */
  enabled?: boolean;
  /** 动画持续时间（毫秒） */
  duration?: number;
  /** 动画间隔（毫秒） */
  interval?: number;
  /** 光泽颜色 */
  glossColor?: string;
  /** 光泽角度 */
  angle?: number;
  /** 光泽大小 */
  size?: number;
  /** 光泽透明度 */
  opacity?: number;
}

/**
 * 接口：光泽位置
 */
export interface GlossPosition {
  left: string;
  top: string;
}

/**
 * Hook: 使用光泽动画
 * 内部逻辑：提供统一的光泽动画逻辑
 * 设计模式：组合模式
 * 参数：
 *   config - 动画配置
 * 返回值：
 *   elementRef - 元素引用
 *   position - 光泽位置
 *   isActive - 是否激活
 *   trigger - 触发动画
 *   pause - 暂停动画
 *   resume - 恢复动画
 *   getStyle - 获取光泽样式
 */
export const useGlossAnimation = (config: GlossAnimationConfig = {}) => {
  /**
   * 内部变量：动画配置（使用默认值）
   */
  const animationConfig: Required<GlossAnimationConfig> = {
    enabled: config.enabled ?? true,
    duration: config.duration ?? 1500,
    interval: config.interval ?? 3000,
    glossColor: config.glossColor ?? 'rgba(255, 255, 255, 0.3)',
    angle: config.angle ?? 45,
    size: config.size ?? 100,
    opacity: config.opacity ?? 0.3,
  };

  /**
   * 内部变量：元素引用
   */
  const elementRef = useRef<HTMLDivElement>(null);

  /**
   * 内部变量：光泽位置
   */
  const [position, setPosition] = useState<GlossPosition>({ left: '-100%', top: '0%' });

  /**
   * 内部变量：是否激活
   */
  const [isActive, setIsActive] = useState(false);

  /**
   * 内部变量：定时器引用
   */
  const timerRef = useRef<number>();

  /**
   * 函数级注释：触发光泽动画
   * 内部逻辑：随机更新位置
   */
  const trigger = useCallback(() => {
    if (!animationConfig.enabled || !isActive) {
      return;
    }

    const randomLeft = Math.random() * 200 - 100;
    const randomTop = Math.random() * 200 - 100;
    setPosition({ left: `${randomLeft}%`, top: `${randomTop}%` });
  }, [animationConfig.enabled, isActive]);

  /**
   * 函数级注释：暂停动画
   */
  const pause = useCallback(() => {
    setIsActive(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
  }, []);

  /**
   * 函数级注释：恢复动画
   */
  const resume = useCallback(() => {
    setIsActive(true);
  }, []);

  /**
   * 函数级注释：获取光泽样式
   * 返回值：CSS样式对象
   */
  const getStyle = useCallback((): CSSProperties => {
    return {
      position: 'absolute',
      width: `${animationConfig.size}%`,
      height: `${animationConfig.size}%`,
      background: `linear-gradient(${animationConfig.angle}deg,
        transparent 40%,
        ${animationConfig.glossColor} 50%,
        transparent 60%)`,
      backgroundSize: '200% 200%',
      opacity: animationConfig.opacity,
      pointerEvents: 'none',
      left: position.left,
      top: position.top,
      transform: 'translate(-50%, -50%)',
      borderRadius: '50%',
    };
  }, [animationConfig, position]);

  /**
   * 内部逻辑：设置动画循环
   */
  useEffect(() => {
    if (animationConfig.enabled && isActive) {
      trigger();
      timerRef.current = setInterval(trigger, animationConfig.interval);
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [animationConfig.enabled, animationConfig.interval, isActive, trigger]);

  /**
   * 内部逻辑：组件卸载时清理定时器
   */
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  return {
    /** 元素引用 */
    elementRef,
    /** 当前光泽位置 */
    position,
    /** 是否激活 */
    isActive,
    /** 触发动画 */
    trigger,
    /** 暂停动画 */
    pause,
    /** 恢复动画 */
    resume,
    /** 获取光泽样式 */
    getStyle,
  };
};

/**
 * 类：光泽动画管理器（单例）
 * 设计模式：单例模式 + 共享模式
 * 职责：全局管理光泽动画实例
 */
class GlossAnimationManager {
  /**
   * 内部变量：单例实例
   */
  private static instance: GlossAnimationManager;

  /**
   * 内部变量：动画池
   */
  private animations: Map<string, number> = new Map();

  /**
   * 函数级注释：获取单例实例
   */
  static getInstance(): GlossAnimationManager {
    if (!GlossAnimationManager.instance) {
      GlossAnimationManager.instance = new GlossAnimationManager();
    }
    return GlossAnimationManager.instance;
  }

  /**
   * 函数级注释：注册动画
   * 参数：
   *   key - 动画键
   *   callback - 动画回调
   *   interval - 间隔时间
   */
  register(key: string, callback: () => void, interval: number): void {
    // 内部逻辑：清除已有动画
    this.unregister(key);

    // 内部逻辑：创建新动画
    const timer = setInterval(callback, interval);
    this.animations.set(key, timer);
  }

  /**
   * 函数级注释：注销动画
   * 参数：
   *   key - 动画键
   */
  unregister(key: string): void {
    const timer = this.animations.get(key);
    if (timer) {
      clearInterval(timer);
      this.animations.delete(key);
    }
  }

  /**
   * 函数级注释：清空所有动画
   */
  clear(): void {
    this.animations.forEach(timer => clearInterval(timer));
    this.animations.clear();
  }
}

/**
 * 变量：全局光泽动画管理器实例
 */
export const glossAnimationManager = GlossAnimationManager.getInstance();

/**
 * 组件：光泽效果层
 * 设计模式：组合模式 - 可复用组件
 * 职责：渲染光泽动画效果
 */
interface GlossEffectProps {
  /** 动画配置 */
  config?: GlossAnimationConfig;
  /** 是否激活 */
  active?: boolean;
  /** 自定义类名 */
  className?: string;
}

/**
 * 函数级注释：光泽效果组件
 * 内部逻辑：独立的光泽效果层，可嵌入任何组件
 */
export const GlossEffect: React.FC<GlossEffectProps> = ({
  config = {},
  active = true,
  className = ''
}) => {
  const { elementRef, getStyle } = useGlossAnimation({ ...config, enabled: active });

  return (
    <div
      ref={elementRef}
      className={`gloss-effect ${className}`}
      style={getStyle()}
    />
  );
};

/**
 * 默认导出
 */
export default useGlossAnimation;
