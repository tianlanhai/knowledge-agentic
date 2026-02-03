/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：组件组合器模块
 * 内部逻辑：提供灵活的组件组合方式，支持条件渲染、动态组合
 * 设计模式：组合模式（Composite Pattern）+ 建造者模式
 * 设计原则：开闭原则、组合优于继承
 */

import React, { isValidElement, cloneElement } from 'react';
import type { ComponentType, ReactNode } from 'react';

/**
 * 可组合组件配置接口
 */
export interface ComposableComponent {
  /** 组件类型或 React 元素 */
  component: ComponentType<any> | ReactNode;
  /** 组件属性 */
  props?: Record<string, any>;
  /** 组件唯一标识（用于 key） */
  key?: string;
  /** 渲染条件函数 */
  condition?: (context: any) => boolean;
  /** 是否延迟加载（用于代码分割） */
  lazy?: boolean;
  /** 加载中占位组件 */
  fallback?: ReactNode;
  /** 错误回退组件 */
  errorFallback?: ReactNode;
}

/**
 * 组合器配置接口
 */
export interface ComposerConfig {
  /** 组件列表 */
  components: ComposableComponent[];
  /** 共享上下文 */
  context?: any;
  /** 布局方向 */
  direction?: 'vertical' | 'horizontal';
  /** 间距 */
  spacing?: number | string;
  /** 对齐方式 */
  align?: 'start' | 'center' | 'end' | 'stretch';
  /** 容器样式 */
  containerStyle?: React.CSSProperties;
  /** 容器类名 */
  containerClassName?: string;
  /** 全局回退组件 */
  fallback?: ReactNode;
}

/**
 * 组件：ComponentComposer
 * 内部逻辑：动态组合多个组件，支持条件渲染和延迟加载
 * 设计模式：组合模式（Composite Pattern）
 */
export const ComponentComposer: React.FC<ComposerConfig> = ({
  components,
  context,
  direction = 'vertical',
  spacing = 0,
  align = 'stretch',
  containerStyle,
  containerClassName,
  fallback
}) => {
  /**
   * 函数级注释：渲染单个组件
   * 参数：
   *   config - 组件配置
   *   index - 索引
   * 返回值：React 节点或 null
   */
  const renderComponent = (config: ComposableComponent, index: number): ReactNode | null => {
    // 内部逻辑：检查条件
    if (config.condition && !config.condition(context)) {
      return null;
    }

    // 内部逻辑：处理直接传入的 React 元素
    if (isValidElement(config.component)) {
      // 内部逻辑：合并 props
      return cloneElement(config.component as any, {
        key: config.key || `composer-${index}`,
        ...config.props
      });
    }

    // 内部逻辑：处理组件类型
    const Component = config.component as ComponentType<any>;

    try {
      // 内部逻辑：延迟加载处理
      if (config.lazy) {
        const LazyComponent = React.lazy(() =>
          Promise.resolve({ default: Component })
        );

        return (
          <React.Suspense
            key={config.key || `composer-${index}`}
            fallback={config.fallback || <div>Loading...</div>}
          >
            <LazyComponent {...config.props} />
          </React.Suspense>
        );
      }

      return (
        <Component
          key={config.key || `composer-${index}`}
          {...config.props}
        />
      );
    } catch (error) {
      console.error('[ComponentComposer] 组件渲染错误:', error);
      return config.errorFallback || null;
    }
  };

  /**
   * 函数级注释：计算容器样式
   * 返回值：CSS 样式对象
   */
  const getContainerStyle = (): React.CSSProperties => {
    const baseStyle: React.CSSProperties = {
      display: 'flex',
      flexDirection: direction === 'vertical' ? 'column' : 'row',
      gap: typeof spacing === 'number' ? `${spacing}px` : spacing,
      alignItems: align,
      ...containerStyle
    };

    return baseStyle;
  };

  // 内部逻辑：过滤和渲染组件
  const renderedComponents = components
    .map((config, index) => renderComponent(config, index))
    .filter((node): node is ReactNode => node !== null);

  // 内部逻辑：没有可渲染的组件
  if (renderedComponents.length === 0 && fallback) {
    return <>{fallback}</>;
  }

  return (
    <div className={containerClassName} style={getContainerStyle()}>
      {renderedComponents}
    </div>
  );
};

/**
 * 类：ComponentComposerBuilder
 * 内部逻辑：使用建造者模式构建组件组合
 * 设计模式：建造者模式（Builder Pattern）
 */
export class ComponentComposerBuilder {
  /** 内部变量：组件列表 */
  private components: ComposableComponent[] = [];

  /** 内部变量：组合器配置 */
  private config: Omit<ComposerConfig, 'components'> = {
    direction: 'vertical',
    spacing: 0,
    align: 'stretch'
  };

  /**
   * 函数级注释：添加组件
   * 参数：
   *   component - 组件或 React 元素
   *   props - 组件属性
   * 返回值：自身（支持链式调用）
   */
  addComponent(
    component: ComponentType<any> | ReactNode,
    props?: Record<string, any>
  ): this {
    this.components.push({ component, props });
    return this;
  }

  /**
   * 函数级注释：添加条件组件
   * 参数：
   *   component - 组件或 React 元素
   *   condition - 条件函数
   *   props - 组件属性
   * 返回值：自身（支持链式调用）
   */
  addConditionalComponent(
    component: ComponentType<any> | ReactNode,
    condition: (context: any) => boolean,
    props?: Record<string, any>
  ): this {
    this.components.push({ component, condition, props });
    return this;
  }

  /**
   * 函数级注释：添加延迟加载组件
   * 参数：
   *   component - 组件
   *   props - 组件属性
   *   fallback - 加载中占位
   * 返回值：自身（支持链式调用）
   */
  addLazyComponent(
    component: ComponentType<any>,
    props?: Record<string, any>,
    fallback?: ReactNode
  ): this {
    this.components.push({ component, props, lazy: true, fallback });
    return this;
  }

  /**
   * 函数级注释：设置布局方向
   * 参数：
   *   direction - 方向
   * 返回值：自身（支持链式调用）
   */
  setDirection(direction: 'vertical' | 'horizontal'): this {
    this.config.direction = direction;
    return this;
  }

  /**
   * 函数级注释：设置间距
   * 参数：
   *   spacing - 间距
   * 返回值：自身（支持链式调用）
   */
  setSpacing(spacing: number | string): this {
    this.config.spacing = spacing;
    return this;
  }

  /**
   * 函数级注释：设置对齐方式
   * 参数：
   *   align - 对齐方式
   * 返回值：自身（支持链式调用）
   */
  setAlign(align: 'start' | 'center' | 'end' | 'stretch'): this {
    this.config.align = align;
    return this;
  }

  /**
   * 函数级注释：设置共享上下文
   * 参数：
   *   context - 上下文数据
   * 返回值：自身（支持链式调用）
   */
  setContext(context: any): this {
    this.config.context = context;
    return this;
  }

  /**
   * 函数级注释：设置容器样式
   * 参数：
   *   style - 样式对象
   * 返回值：自身（支持链式调用）
   */
  setStyle(style: React.CSSProperties): this {
    this.config.containerStyle = style;
    return this;
  }

  /**
   * 函数级注释：设置容器类名
   * 参数：
   *   className - 类名
   * 返回值：自身（支持链式调用）
   */
  setClassName(className: string): this {
    this.config.containerClassName = className;
    return this;
  }

  /**
   * 函数级注释：设置回退组件
   * 参数：
   *   fallback - 回退组件
   * 返回值：自身（支持链式调用）
   */
  setFallback(fallback: ReactNode): this {
    this.config.fallback = fallback;
    return this;
  }

  /**
   * 函数级注释：清除所有组件
   * 返回值：自身（支持链式调用）
   */
  clear(): this {
    this.components = [];
    return this;
  }

  /**
   * 函数级注释：构建组合器
   * 返回值：组合器组件
   */
  build(): React.FC {
    const composerConfig = { ...this.config, components: [...this.components] };

    return () => <ComponentComposer {...composerConfig} />;
  }

  /**
   * 函数级注释：构建并渲染
   * 返回值：React 元素
   */
  render(): React.ReactElement {
    const composerConfig = { ...this.config, components: [...this.components] };
    return <ComponentComposer {...composerConfig} />;
  }
}

/**
 * Hook：useComponentComposer
 * 内部逻辑：提供组件组合的 Hook
 * 设计模式：Hook 模式
 */
export function useComponentComposer(initialConfig?: ComposerConfig) {
  // 内部变量：组件列表
  const [components, setComponents] = React.useState<ComposableComponent[]>(
    initialConfig?.components || []
  );

  // 内部变量：配置
  const [config, setConfig] = React.useState<Omit<ComposerConfig, 'components'>>({
    direction: initialConfig?.direction || 'vertical',
    spacing: initialConfig?.spacing || 0,
    align: initialConfig?.align || 'stretch',
    containerStyle: initialConfig?.containerStyle,
    containerClassName: initialConfig?.containerClassName,
    fallback: initialConfig?.fallback,
    context: initialConfig?.context
  });

  /**
   * 函数级注释：添加组件
   */
  const addComponent = (
    component: ComponentType<any> | ReactNode,
    props?: Record<string, any>,
    key?: string
  ) => {
    setComponents((prev) => [...prev, { component, props, key }]);
  };

  /**
   * 函数级注释：移除组件
   */
  const removeComponent = (key: string) => {
    setComponents((prev) => prev.filter((c) => c.key !== key));
  };

  /**
   * 函数级注释：更新配置
   */
  const updateConfig = (updates: Partial<Omit<ComposerConfig, 'components'>>) => {
    setConfig((prev) => ({ ...prev, ...updates }));
  };

  /**
   * 函数级注释：清空所有组件
   */
  const clear = () => {
    setComponents([]);
  };

  /**
   * 函数级注释：渲染组合器
   */
  const render = () => (
    <ComponentComposer components={components} {...config} />
  );

  return {
    components,
    config,
    addComponent,
    removeComponent,
    updateConfig,
    clear,
    render
  };
}

/**
 * 组件：ConditionalComposer
 * 内部逻辑：基于条件选择渲染组件
 * 设计模式：策略模式 + 组件模式
 */
export interface ConditionalComposerConfig {
  /** 条件-组件映射 */
  cases: Array<{
    condition: (context: any) => boolean;
    component: ComponentType<any> | ReactNode;
    props?: Record<string, any>;
  }>;
  /** 默认组件 */
  default?: ComponentType<any> | ReactNode;
  /** 共享上下文 */
  context?: any;
}

export const ConditionalComposer: React.FC<ConditionalComposerConfig> = ({
  cases,
  default: defaultComponent,
  context
}) => {
  // 内部逻辑：查找第一个匹配的条件
  const matchedCase = cases.find((c) => c.condition(context));

  if (matchedCase) {
    const { component, props } = matchedCase;

    if (isValidElement(component)) {
      return cloneElement(component as any, props);
    }

    const Component = component as ComponentType<any>;
    return <Component {...props} />;
  }

  // 内部逻辑：渲染默认组件
  if (defaultComponent) {
    if (isValidElement(defaultComponent)) {
      return defaultComponent;
    }

    const DefaultComponent = defaultComponent as ComponentType<any>;
    return <DefaultComponent />;
  }

  return null;
};

/**
 * 组件：SwitchComposer
 * 内部逻辑：类似 switch-case 的组件选择器
 */
export interface SwitchCase {
  /** 匹配值 */
  value: any;
  /** 对应的组件 */
  component: ComponentType<any> | ReactNode;
  /** 组件属性 */
  props?: Record<string, any>;
}

export interface SwitchComposerProps {
  /** 要匹配的值 */
  value: any;
  /** case 列表 */
  cases: SwitchCase[];
  /** 默认组件 */
  default?: ComponentType<any> | ReactNode;
}

export const SwitchComposer: React.FC<SwitchComposerProps> = ({
  value,
  cases,
  default: defaultComponent
}) => {
  // 内部逻辑：查找匹配的 case
  const matchedCase = cases.find((c) => c.value === value);

  if (matchedCase) {
    const { component, props } = matchedCase;

    if (isValidElement(component)) {
      return cloneElement(component as any, props);
    }

    const Component = component as ComponentType<any>;
    return <Component {...props} />;
  }

  // 内部逻辑：渲染默认组件
  if (defaultComponent) {
    if (isValidElement(defaultComponent)) {
      return defaultComponent;
    }

    const DefaultComponent = defaultComponent as ComponentType<any>;
    return <DefaultComponent />;
  }

  return null;
};

// 导出所有公共接口
export default ComponentComposer;
