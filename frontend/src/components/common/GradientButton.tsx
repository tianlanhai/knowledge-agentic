/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：渐变按钮组件
 * 内部逻辑：提供美观的渐变按钮，支持多种样式变体、加载状态、图标等
 * 外部变量：children - 按钮内容，variant - 样式变体，size - 尺寸，loading - 加载中，icon - 图标，onClick - 点击事件，disabled - 禁用
 * 内部变量：rippleRef - 波纹效果引用，isRippling - 波纹动画状态
 * 返回值：JSX.Element
 */

import React, { useState, useRef } from 'react';
import type { ReactNode, MouseEvent, CSSProperties } from 'react';

/**
 * 函数级注释：按钮样式变体类型
 */
export type ButtonVariant = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'ghost';

/**
 * 函数级注释：按钮尺寸类型
 */
export type ButtonSize = 'sm' | 'md' | 'lg' | 'xl';

/**
 * 函数级注释：渐变按钮属性接口
 * 属性说明：children - 子元素，variant - 样式变体，size - 尺寸，loading - 加载状态，icon - 图标，onClick - 点击，disabled - 禁用，type - 按钮类型，style - 内联样式，className - 类名，block - 块级按钮，gradient - 自定义渐变，shine - 光泽动画
 */
export interface GradientButtonProps {
  /** 子元素 */
  children: ReactNode;
  /** 样式变体 */
  variant?: ButtonVariant;
  /** 尺寸 */
  size?: ButtonSize;
  /** 加载状态 */
  loading?: boolean;
  /** 图标 */
  icon?: ReactNode;
  /** 点击事件 */
  onClick?: (e: MouseEvent<HTMLButtonElement>) => void;
  /** 禁用状态 */
  disabled?: boolean;
  /** 按钮类型 */
  type?: 'button' | 'submit' | 'reset';
  /** 内联样式 */
  style?: CSSProperties;
  /** 类名 */
  className?: string;
  /** 块级按钮 */
  block?: boolean;
  /** 自定义渐变 */
  gradient?: string;
  /** 光泽动画 */
  shine?: boolean;
  /** 圆角 */
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'full';
}

/**
 * 函数级注释：获取尺寸对应的CSS类
 * 参数说明：size - 尺寸类型
 * 返回值：CSS类名
 */
const getSizeClass = (size: ButtonSize): string => {
  const sizeMap: Record<ButtonSize, string> = {
    sm: 'btn-sm',
    md: 'btn-md',
    lg: 'btn-lg',
    xl: 'btn-xl',
  };
  return sizeMap[size];
};

/**
 * 函数级注释：获取圆角对应的CSS类
 * 参数说明：rounded - 圆角类型
 * 返回值：CSS类名
 */
const getRoundedClass = (rounded?: string): string => {
  const roundedMap: Record<string, string> = {
    none: '',
    sm: 'btn-rounded-sm',
    md: 'btn-rounded-md',
    lg: 'btn-rounded-lg',
    full: 'btn-rounded-full',
  };
  return rounded ? roundedMap[rounded] : 'btn-rounded-md';
};

/**
 * 函数级注释：获取变体对应的样式
 * 参数说明：variant - 变体类型
 * 返回值：样式对象（背景色、文本色、边框色、光晕色）
 */
const getVariantStyles = (variant: ButtonVariant) => {
  const variantMap: Record<ButtonVariant, {
    background: string;
    color: string;
    border: string;
    glow: string;
  }> = {
    primary: {
      background: 'var(--color-gradient)',
      color: '#ffffff',
      border: 'var(--color-gradient)',
      glow: 'var(--glow-primary)',
    },
    secondary: {
      background: 'var(--glass-bg)',
      color: 'var(--text-primary)',
      border: 'var(--glass-border)',
      glow: 'var(--glass-shadow)',
    },
    success: {
      background: 'var(--color-success)',
      color: '#ffffff',
      border: 'var(--color-success)',
      glow: 'var(--glow-success)',
    },
    warning: {
      background: 'var(--color-warning)',
      color: '#ffffff',
      border: 'var(--color-warning)',
      glow: 'var(--glow-warning)',
    },
    error: {
      background: 'var(--color-error)',
      color: '#ffffff',
      border: 'var(--color-error)',
      glow: 'var(--glow-error)',
    },
    ghost: {
      background: 'transparent',
      color: 'var(--color-primary-500)',
      border: 'var(--glass-border)',
      glow: 'transparent',
    },
  };
  return variantMap[variant];
};

/**
 * 函数级注释：渐变按钮组件
 * 内部变量：rippleRef - 波纹引用，isRippling - 波纹状态，shineRef - 光泽引用，shinePosition - 光泽位置，isHovering - 悬停状态
 * 内部逻辑：处理点击波纹效果、光泽动画、悬停效果
 * 返回值：JSX.Element
 */
export const GradientButton: React.FC<GradientButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  onClick,
  disabled = false,
  type = 'button',
  style = {},
  className = '',
  block = false,
  gradient,
  shine = false,
  rounded = 'md',
}) => {
  // 内部变量：波纹引用
  const rippleRef = useRef<HTMLButtonElement>(null);
  // 内部变量：波纹状态
  const [isRippling, setIsRippling] = useState(false);
  // 内部变量：光泽引用
  const shineRef = useRef<HTMLDivElement>(null);
  // 内部变量：光泽位置
  const [shinePosition, setShinePosition] = useState({ left: '-100%', top: '0%' });
  // 内部变量：悬停状态
  const [isHovering, setIsHovering] = useState(false);

  /**
   * 函数级注释：获取变体样式
   * 内部逻辑：返回对应变体的样式对象
   * 返回值：样式对象
   */
  const variantStyles = getVariantStyles(variant);

  /**
   * 函数级注释：移动光泽动画位置
   * 内部逻辑：随机更新位置，创造闪烁效果
   * 返回值：void
   */
  const moveShine = () => {
    if (!shine) return;
    const randomLeft = Math.random() * 200 - 100;
    const randomTop = Math.random() * 200 - 100;
    setShinePosition({ left: `${randomLeft}%`, top: `${randomTop}%` });
  };

  /**
   * 函数级注释：定期移动光泽
   * 内部逻辑：每3秒移动一次
   * 返回值：无（useEffect处理）
   */
  React.useEffect(() => {
    if (shine) {
      const interval = setInterval(moveShine, 3000);
      return () => clearInterval(interval);
    }
  }, [shine]);

  /**
   * 函数级注释：处理按钮点击
   * 内部逻辑：触发波纹动画和点击回调
   * 返回值：void
   */
  const handleClick = (e: MouseEvent<HTMLButtonElement>) => {
    if (disabled || loading || isRippling) return;

    setIsRippling(true);

    // 创建波纹元素
    const button = rippleRef.current;
    if (!button) return;

    const rect = button.getBoundingClientRect();
    const ripple = document.createElement('span');
    const size = Math.max(rect.width, rect.height);
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.position = 'absolute';
    ripple.style.left = `${rect.width / 2 - size / 2}px`;
    ripple.style.top = `${rect.height / 2 - size / 2}px`;
    ripple.style.borderRadius = '50%';
    ripple.style.background = 'rgba(255, 255, 255, 0.4)';
    ripple.style.transform = 'scale(0)';
    ripple.style.pointerEvents = 'none';
    ripple.style.animation = 'rippleEffect 0.6s ease-out';
    ripple.style.zIndex = '0';

    button.appendChild(ripple);
    button.style.position = 'relative';
    button.style.overflow = 'hidden';

    // 清理波纹元素
    setTimeout(() => {
      ripple.style.transform = 'scale(4)';
      ripple.style.opacity = '0';
    }, 10);

    setTimeout(() => {
      ripple.remove();
      setIsRippling(false);
    }, 600);

    onClick?.(e);
  };

  /**
   * 函数级注释：处理鼠标进入
   * 内部逻辑：更新悬停状态
   * 返回值：void
   */
  const handleMouseEnter = () => {
    setIsHovering(true);
  };

  /**
   * 函数级注释：处理鼠标离开
   * 内部逻辑：清除悬停状态
   * 返回值：void
   */
  const handleMouseLeave = () => {
    setIsHovering(false);
  };

  /**
   * 函数级注释：构造按钮类名
   * 内部逻辑：组合各种状态类名
   * 返回值：类名字符串
   */
  const buttonClasses = [
    'gradient-btn',
    `gradient-btn-${variant}`,
    getSizeClass(size),
    getRoundedClass(rounded),
    block && 'gradient-btn-block',
    disabled && 'gradient-btn-disabled',
    loading && 'gradient-btn-loading',
    isRippling && 'gradient-btn-rippling',
    isHovering && 'gradient-btn-hover',
    shine && 'gradient-btn-shine',
    className,
  ].filter(Boolean).join(' ');

  /**
   * 函数级注释：构造按钮样式
   * 内部逻辑：应用渐变、光晕、圆角等样式
   * 返回值：CSSProperties
   */
  const buttonStyle: CSSProperties = {
    ...style,
    '--btn-gradient': gradient || variantStyles.background,
    '--btn-color': variantStyles.color,
    '--btn-border': variantStyles.border,
    '--btn-glow': variantStyles.glow,
  } as CSSProperties & Record<string, string>;

  /**
   * 函数级注释：渲染图标
   * 内部逻辑：根据加载状态显示不同的图标
   * 返回值：ReactNode
   */
  const renderIcon = () => {
    if (loading) {
      return (
        <span className="gradient-btn-icon gradient-btn-loading-icon">
          <span className="gradient-btn-spinner" />
        </span>
      );
    }

    return icon ? (
      <span className="gradient-btn-icon">{icon}</span>
    ) : null;
  };

  return (
    <button
      ref={rippleRef}
      type={type}
      className={buttonClasses}
      style={buttonStyle}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      disabled={disabled || loading}
    >
      {/* 光泽动画层 */}
      {shine && (
        <div
          ref={shineRef}
          className="gradient-btn-shimmer"
          style={{
            '--shine-left': shinePosition.left,
            '--shine-top': shinePosition.top,
          } as React.CSSProperties & Record<string, string>}
        />
      )}

      {/* 波纹动画层 */}
      <span className="gradient-btn-ripple-layer" />

      {/* 内容 */}
      <span className="gradient-btn-content">
        {renderIcon()}
        {children}
      </span>
    </button>
  );
};

/**
 * 默认导出
 */
export default GradientButton;
