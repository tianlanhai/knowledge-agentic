/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：按钮变体策略模块
 * 内部逻辑：使用策略模式管理按钮变体样式，消除硬编码的映射
 * 设计模式：策略模式（Strategy Pattern）
 * 设计原则：开闭原则（OCP）、单一职责原则（SRP）
 *
 * 实现说明：
 *   - 定义按钮变体策略的统一接口
 *   - 每个变体对应一个具体的策略实现
 *   - 支持动态注册新的变体策略
 */

import type { CSSProperties } from 'react';

/**
 * 类型：按钮变体类型
 */
export type ButtonVariant = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'ghost';

/**
 * 接口：按钮变体样式策略
 * 内部逻辑：定义变体样式的统一接口
 * 设计模式：策略模式 - 抽象策略接口
 */
export interface ButtonVariantStrategy {
  /**
   * 函数级注释：获取背景色
   * 返回值：CSS背景色值
   */
  getBackground(): string;

  /**
   * 函数级注释：获取文本颜色
   * 返回值：CSS文本颜色值
   */
  getColor(): string;

  /**
   * 函数级注释：获取边框颜色
   * 返回值：CSS边框颜色值
   */
  getBorder(): string;

  /**
   * 函数级注释：获取光晕颜色
   * 返回值：CSS光晕颜色值
   */
  getGlow(): string;

  /**
   * 函数级注释：获取所有样式
   * 内部逻辑：返回完整的样式对象
   * 返回值：样式对象
   */
  getStyles(): {
    background: string;
    color: string;
    border: string;
    glow: string;
  };
}

/**
 * 类：基础按钮变体策略
 * 设计模式：策略模式 - 基础策略类
 * 职责：提供默认实现
 */
abstract class BaseButtonVariantStrategy implements ButtonVariantStrategy {
  /**
   * 函数级注释：获取所有样式
   * 返回值：样式对象
   */
  getStyles() {
    return {
      background: this.getBackground(),
      color: this.getColor(),
      border: this.getBorder(),
      glow: this.getGlow(),
    };
  }

  /**
   * 函数级注释：获取背景色（抽象方法）
   */
  abstract getBackground(): string;

  /**
   * 函数级注释：获取文本颜色（抽象方法）
   */
  abstract getColor(): string;

  /**
   * 函数级注释：获取边框颜色（抽象方法）
   */
  abstract getBorder(): string;

  /**
   * 函数级注释：获取光晕颜色（抽象方法）
   */
  abstract getGlow(): string;
}

/**
 * 类：主要按钮策略
 * 设计模式：策略模式 - 具体策略
 */
class PrimaryButtonStrategy extends BaseButtonVariantStrategy {
  getBackground(): string {
    return 'var(--color-gradient)';
  }

  getColor(): string {
    return '#ffffff';
  }

  getBorder(): string {
    return 'var(--color-gradient)';
  }

  getGlow(): string {
    return 'var(--glow-primary)';
  }
}

/**
 * 类：次要按钮策略
 * 设计模式：策略模式 - 具体策略
 */
class SecondaryButtonStrategy extends BaseButtonVariantStrategy {
  getBackground(): string {
    return 'var(--glass-bg)';
  }

  getColor(): string {
    return 'var(--text-primary)';
  }

  getBorder(): string {
    return 'var(--glass-border)';
  }

  getGlow(): string {
    return 'var(--glass-shadow)';
  }
}

/**
 * 类：成功按钮策略
 * 设计模式：策略模式 - 具体策略
 */
class SuccessButtonStrategy extends BaseButtonVariantStrategy {
  getBackground(): string {
    return 'var(--color-success)';
  }

  getColor(): string {
    return '#ffffff';
  }

  getBorder(): string {
    return 'var(--color-success)';
  }

  getGlow(): string {
    return 'var(--glow-success)';
  }
}

/**
 * 类：警告按钮策略
 * 设计模式：策略模式 - 具体策略
 */
class WarningButtonStrategy extends BaseButtonVariantStrategy {
  getBackground(): string {
    return 'var(--color-warning)';
  }

  getColor(): string {
    return '#ffffff';
  }

  getBorder(): string {
    return 'var(--color-warning)';
  }

  getGlow(): string {
    return 'var(--glow-warning)';
  }
}

/**
 * 类：错误按钮策略
 * 设计模式：策略模式 - 具体策略
 */
class ErrorButtonStrategy extends BaseButtonVariantStrategy {
  getBackground(): string {
    return 'var(--color-error)';
  }

  getColor(): string {
    return '#ffffff';
  }

  getBorder(): string {
    return 'var(--color-error)';
  }

  getGlow(): string {
    return 'var(--glow-error)';
  }
}

/**
 * 类：幽灵按钮策略
 * 设计模式：策略模式 - 具体策略
 */
class GhostButtonStrategy extends BaseButtonVariantStrategy {
  getBackground(): string {
    return 'transparent';
  }

  getColor(): string {
    return 'var(--color-primary-500)';
  }

  getBorder(): string {
    return 'var(--glass-border)';
  }

  getGlow(): string {
    return 'transparent';
  }
}

/**
 * 类：按钮变体策略工厂
 * 设计模式：工厂模式 + 策略模式
 * 职责：管理和创建按钮变体策略
 */
class ButtonVariantStrategyFactory {
  /**
   * 内部变量：策略注册表
   */
  private static strategies: Map<ButtonVariant, ButtonVariantStrategy> = new Map([
    ['primary', new PrimaryButtonStrategy()],
    ['secondary', new SecondaryButtonStrategy()],
    ['success', new SuccessButtonStrategy()],
    ['warning', new WarningButtonStrategy()],
    ['error', new ErrorButtonStrategy()],
    ['ghost', new GhostButtonStrategy()],
  ]);

  /**
   * 函数级注释：获取变体策略
   * 参数：
   *   variant - 按钮变体类型
   * 返回值：变体策略实例
   */
  static getStrategy(variant: ButtonVariant): ButtonVariantStrategy {
    const strategy = this.strategies.get(variant);
    if (!strategy) {
      // 内部逻辑：默认使用主要按钮策略
      return this.strategies.get('primary')!;
    }
    return strategy;
  }

  /**
   * 函数级注释：注册新的变体策略
   * 内部逻辑：支持动态扩展新的变体
   * 参数：
   *   variant - 变体名称
   *   strategy - 策略实例
   */
  static register(variant: string, strategy: ButtonVariantStrategy): void {
    this.strategies.set(variant as ButtonVariant, strategy);
  }

  /**
   * 函数级注释：获取变体样式（便捷方法）
   * 参数：
   *   variant - 按钮变体类型
   * 返回值：样式对象
   */
  static getVariantStyles(variant: ButtonVariant): ReturnType<ButtonVariantStrategy['getStyles']> {
    const strategy = this.getStrategy(variant);
    return strategy.getStyles();
  }
}

/**
 * 函数级注释：获取变体样式（对外API）
 * 参数：
 *   variant - 按钮变体类型
 * 返回值：样式对象
 */
export const getVariantStyles = (variant: ButtonVariant) => {
  return ButtonVariantStrategyFactory.getVariantStyles(variant);
};

/**
 * 函数级注释：应用变体样式到CSS变量
 * 参数：
 *   variant - 按钮变体类型
 *   customGradient - 自定义渐变（可选）
 * 返回值：CSS样式对象
 */
export const applyVariantStyles = (
  variant: ButtonVariant,
  customGradient?: string
): CSSProperties & Record<string, string> => {
  const styles = getVariantStyles(variant);
  return {
    '--btn-gradient': customGradient || styles.background,
    '--btn-color': styles.color,
    '--btn-border': styles.border,
    '--btn-glow': styles.glow,
  } as CSSProperties & Record<string, string>;
};

/**
 * 默认导出
 */
export default ButtonVariantStrategyFactory;
