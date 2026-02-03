/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：玻璃拟态卡片组件
 * 内部逻辑：提供玻璃拟态效果的卡片容器，支持渐变边框、光晕效果等增强视觉
 * 外部变量：className - 额外的CSS类名，children - 子元素，onClick - 点击回调，hover - 是否悬停
 * 内部变量：showShine - 控制光泽动画状态
 * 返回值：JSX.Element
 */

import React, { useState, useEffect, useRef } from 'react';
import type { ReactNode, CSSProperties } from 'react';

/**
 * 函数级注释：玻璃拟态卡片属性接口
 * 属性说明：children - 子元素，className - 类名，style - 内联样式，onClick - 点击事件，gradientBorder - 渐变边框，shine - 光泽动画
 */
export interface GlassCardProps {
  /** 子元素 */
  children: ReactNode;
  /** 额外的CSS类名 */
  className?: string;
  /** 内联样式 */
  style?: CSSProperties;
  /** 点击事件 */
  onClick?: () => void;
  /** 启用渐变边框 */
  gradientBorder?: boolean;
  /** 启用光泽动画 */
  shine?: boolean;
  /** 禁用动画 */
  noAnimation?: boolean;
  /** 卡片内边距 */
  padding?: string;
  /** 卡片内边距水平 */
  paddingX?: string;
  /** 卡片内边距垂直 */
  paddingY?: string;
  /** 圆角大小 */
  rounded?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  /** 悬停时提升效果 */
  hoverLift?: boolean;
}

/**
 * 函数级注释：获取圆角对应的CSS变量
 * 参数说明：rounded - 圆角大小标识
 * 返回值：CSS变量值
 */
const getRoundedClass = (rounded?: string): string => {
  const roundedMap: Record<string, string> = {
    sm: 'var(--radius-sm)',
    md: 'var(--radius-md)',
    lg: 'var(--radius-lg)',
    xl: 'var(--radius-xl)',
    '2xl': 'var(--radius-2xl)',
    full: 'var(--radius-full)',
  };
  return rounded ? roundedMap[rounded] : 'var(--radius-lg)';
};

/**
 * 函数级注释：玻璃拟态卡片组件
 * 内部变量：shineRef - 光泽动画引用，shimmerPosition - 光泽位置，isHovering - 悬停状态
 * 内部逻辑：处理光泽动画、悬停效果、渐变边框
 * 返回值：JSX.Element
 */
export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className = '',
  style = {},
  onClick,
  gradientBorder = false,
  shine = false,
  noAnimation = false,
  padding,
  paddingX,
  paddingY,
  rounded = 'lg',
  hoverLift = true,
}) => {
  // 内部变量：光泽动画引用
  const shineRef = useRef<HTMLDivElement>(null);
  // 内部变量：光泽位置状态
  const [shimmerPosition, setShimmerPosition] = useState({ left: '-100%', top: '0%' });

  /**
   * 函数级注释：移动光泽动画位置
   * 内部逻辑：随机更新光泽位置，创造闪烁效果
   * 返回值：void
   */
  const moveShine = () => {
    if (!shine || noAnimation) return;

    // 内部变量：随机位置
    const randomLeft = Math.random() * 200 - 100;
    const randomTop = Math.random() * 200 - 100;
    setShimmerPosition({ left: `${randomLeft}%`, top: `${randomTop}%` });
  };

  /**
   * 函数级注释：定期移动光泽
   * 内部逻辑：每3秒移动一次光泽位置
   * 返回值：NodeJS.Timeout
   */
  useEffect(() => {
    if (shine && !noAnimation) {
      const interval = setInterval(moveShine, 3000);
      return () => clearInterval(interval);
    }
  }, [shine, noAnimation]);

  /**
   * 函数级注释：处理鼠标进入
   * 内部逻辑：播放移动光泽动画
   * 返回值：void
   */
  const handleMouseEnter = () => {
    if (shine && !noAnimation) {
      moveShine();
    }
  };

  /**
   * 函数级注释：处理鼠标离开
   * 内部逻辑：空函数，保留接口一致性
   * 返回值：void
   */
  const handleMouseLeave = () => {
    // 保留接口一致性，暂无操作
  };

  /**
   * 函数级注释：计算内边距样式
   * 内部逻辑：根据props计算padding值
   * 返回值：CSSProperties
   */
  const getPaddingStyle = (): CSSProperties => {
    const paddingStyle: CSSProperties = {};
    if (padding) paddingStyle.padding = padding;
    if (paddingX) {
      paddingStyle.paddingLeft = paddingX;
      paddingStyle.paddingRight = paddingX;
    }
    if (paddingY) {
      paddingStyle.paddingTop = paddingY;
      paddingStyle.paddingBottom = paddingY;
    }
    return paddingStyle;
  };

  /**
   * 函数级注释：构造基础类名
   * 内部逻辑：根据props组合类名
   * 返回值：字符串
   */
  const getBaseClasses = (): string => {
    const classes = [
      'glass-card',
      gradientBorder ? 'glass-card-gradient' : '',
      hoverLift ? 'glass-card-lift' : '',
      noAnimation ? 'glass-card-no-animation' : '',
      className,
    ].filter(Boolean).join(' ');
    return classes;
  };

  /**
   * 函数级注释：构造容器样式
   * 内部逻辑：应用玻璃拟态、渐变、圆角、内边距等样式
   * 返回值：CSSProperties
   */
  const getContainerStyle = (): CSSProperties => ({
    ...style,
    '--card-padding': padding || (paddingX || paddingY) ? 'auto' : 'var(--spacing-lg)',
    '--card-padding-x': paddingX || 'auto',
    '--card-padding-y': paddingY || 'auto',
    '--card-radius': getRoundedClass(rounded),
    '--shimmer-left': shimmerPosition.left,
    '--shimmer-top': shimmerPosition.top,
    ...getPaddingStyle(),
  }) as CSSProperties & Record<string, string>;

  return (
    <div
      ref={shineRef}
      className={getBaseClasses()}
      style={getContainerStyle()}
      onClick={onClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {/* 光泽动画层 */}
      {shine && !noAnimation && (
        <div className="glass-card-shimmer" />
      )}

      {/* 内容层 */}
      <div className="glass-card-content">
        {children}
      </div>

      {/* 渐变边框层 */}
      {gradientBorder && <div className="glass-card-gradient-border" />}
    </div>
  );
};

/**
 * 默认导出
 */
export default GlassCard;
