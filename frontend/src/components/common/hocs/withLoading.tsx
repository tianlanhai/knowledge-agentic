/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：加载状态高阶组件模块
 * 内部逻辑：为组件添加加载状态处理能力，统一加载中的 UI 表现
 * 设计模式：高阶组件模式（HOC Pattern）
 * 设计原则：关注点分离原则、DRY 原则
 */

import React from 'react';
import type { ComponentType, ReactNode, ComponentClass } from 'react';
import { Spin, Empty } from 'antd';

/**
 * 加载状态配置接口
 */
export interface LoadingConfig {
  /** 是否正在加载 */
  loading?: boolean;
  /** 加载中的提示文字 */
  loadingTip?: string;
  /** 加载中的大小 */
  size?: 'small' | 'default' | 'large';
  /** 是否延迟显示加载状态（避免闪烁） */
  delay?: number;
  /** 数据是否为空 */
  isEmpty?: boolean;
  /** 空状态的描述 */
  emptyDescription?: string;
  /** 是否显示加载状态 */
  showLoading?: boolean;
}

/**
 * 默认空状态组件
 */
const DefaultEmpty: React.FC<{ description?: string }> = ({ description }) => (
  <Empty
    description={description || '暂无数据'}
    style={{ padding: '40px 0' }}
  />
);

/**
 * 默认加载组件
 */
const DefaultLoading: React.FC<{
  tip?: string;
  size?: 'small' | 'default' | 'large';
}> = ({ tip, size = 'default' }) => (
  <div
    style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '200px',
      width: '100%'
    }}
  >
    <Spin size={size} tip={tip} />
  </div>
);

/**
 * 类型：增强后的组件属性
 * 内部逻辑：包含原组件属性 + 加载配置
 */
export type WithLoadingProps<P> = P & {
  /** 是否正在加载 */
  loading?: boolean;
  /** 加载提示文字 */
  loadingTip?: string;
  /** 数据是否为空 */
  isEmpty?: boolean;
  /** 空状态描述 */
  emptyDescription?: string;
  /** 自定义加载组件 */
  loadingComponent?: ReactNode;
  /** 自定义空状态组件 */
  emptyComponent?: ReactNode;
  /** 是否忽略空状态检查 */
  ignoreEmpty?: boolean;
};

/**
 * 高阶组件：withLoading
 * 内部逻辑：包装组件，添加加载状态和空状态处理
 * 设计模式：高阶组件模式（HOC）
 * 泛型参数：
 *   P - 原组件的属性类型
 * 参数：
 *   WrappedComponent - 要包装的组件
 * 返回值：增强后的组件
 *
 * @example
 * // 基本使用
 * const MyComponentWithLoading = withLoading(MyComponent);
 * <MyComponentWithLoading loading={true} />
 *
 * // 完整配置
 * <MyComponentWithLoading
 *   loading={isLoading}
 *   loadingTip="加载中..."
 *   isEmpty={data.length === 0}
 *   emptyDescription="暂无数据"
 * />
 */
export function withLoading<P extends object>(
  WrappedComponent: ComponentType<P>,
  options: {
    /** 默认加载提示 */
    defaultLoadingTip?: string;
    /** 默认空状态描述 */
    defaultEmptyDescription?: string;
    /** 加载组件大小 */
    size?: 'small' | 'default' | 'large';
    /** 组件名称（用于调试） */
    componentName?: string;
  } = {}
): ComponentType<WithLoadingProps<P>> {
  const {
    defaultLoadingTip = '加载中...',
    defaultEmptyDescription = '暂无数据',
    size = 'default',
    componentName = WrappedComponent.displayName || WrappedComponent.name || 'Component'
  } = options;

  /**
   * 增强后的组件
   */
  const ComponentWithLoading: React.FC<WithLoadingProps<P>> = ({
    loading = false,
    loadingTip,
    isEmpty = false,
    emptyDescription,
    loadingComponent,
    emptyComponent,
    ignoreEmpty = false,
    ...props
  }) => {
    // 内部逻辑：处理加载状态
    if (loading) {
      // 内部逻辑：使用自定义加载组件
      if (loadingComponent) {
        return <>{loadingComponent}</>;
      }

      // 内部逻辑：使用默认加载组件
      return <DefaultLoading tip={loadingTip || defaultLoadingTip} size={size} />;
    }

    // 内部逻辑：处理空状态
    if (isEmpty && !ignoreEmpty) {
      // 内部逻辑：使用自定义空状态组件
      if (emptyComponent) {
        return <>{emptyComponent}</>;
      }

      // 内部逻辑：使用默认空状态组件
      return <DefaultEmpty description={emptyDescription || defaultEmptyDescription} />;
    }

    // 内部逻辑：正常渲染原组件
    return <WrappedComponent {...(props as P)} />;
  };

  // 内部逻辑：设置显示名称
  ComponentWithLoading.displayName = `withLoading(${componentName})`;

  return ComponentWithLoading;
}

/**
 * 高阶组件：withSuspenseLoading
 * 内部逻辑：配合 React Suspense 使用的高阶组件
 * 设计模式：高阶组件模式（HOC）
 * 说明：用于 React.lazy 和 Suspense 场景
 */
export interface SuspenseLoadingConfig {
  /** 加载提示 */
  fallback?: ReactNode;
  /** 延迟显示时间（毫秒） */
  delay?: number;
}

export function withSuspenseLoading<P extends object>(
  WrappedComponent: ComponentType<P>,
  config: SuspenseLoadingConfig = {}
): ComponentType<P> {
  const { fallback, delay = 200 } = config;

  /**
   * 增强后的组件
   */
  const ComponentWithSuspense: React.FC<P> = (props) => {
    // 内部逻辑：延迟显示加载状态（避免闪烁）
    const [showLoading, setShowLoading] = React.useState(false);

    React.useEffect(() => {
      const timer = setTimeout(() => {
        setShowLoading(true);
      }, delay);

      return () => clearTimeout(timer);
    }, []);

    if (showLoading && fallback) {
      return <>{fallback}</>;
    }

    return <WrappedComponent {...props} />;
  };

  ComponentWithSuspense.displayName = `withSuspenseLoading(${
    WrappedComponent.displayName || WrappedComponent.name || 'Component'
  })`;

  return ComponentWithSuspense;
}

/**
 * 高阶组件：withListLoading
 * 内部逻辑：专门处理列表数据的加载和空状态
 * 设计模式：高阶组件模式（HOC）
 */
export interface ListData<T = any> {
  /** 列表数据 */
  items?: T[];
  /** 总数 */
  total?: number;
  /** 是否有更多 */
  hasMore?: boolean;
}

export interface WithListLoadingProps<P> extends WithLoadingProps<P> {
  /** 列表数据 */
  data?: any[];
  /** 数据提取函数（从 props 中提取列表数据） */
  dataSelector?: (props: P) => any[];
}

export function withListLoading<P extends object>(
  WrappedComponent: ComponentType<P>,
  options: {
    /** 数据选择器（函数） */
    dataSelector?: (props: P) => any[];
    /** 默认空状态描述 */
    defaultEmptyDescription?: string;
    /** 组件名称 */
    componentName?: string;
  } = {}
): ComponentType<WithListLoadingProps<P>> {
  const {
    dataSelector,
    defaultEmptyDescription = '暂无数据',
    componentName = WrappedComponent.displayName || WrappedComponent.name || 'Component'
  } = options;

  /**
   * 增强后的组件
   */
  const ComponentWithListLoading: React.FC<WithListLoadingProps<P>> = (props) => {
    const { loading, data, loadingTip, emptyDescription, ignoreEmpty, ...restProps } =
      props as any;

    // 内部逻辑：提取列表数据
    let listData: any[] = [];

    if (Array.isArray(data)) {
      listData = data;
    } else if (dataSelector) {
      listData = dataSelector(props as P);
    }

    // 内部逻辑：检查是否为空
    const isEmpty = !loading && listData.length === 0 && !ignoreEmpty;

    // 内部逻辑：处理加载状态
    if (loading) {
      return <DefaultLoading tip={loadingTip} />;
    }

    // 内部逻辑：处理空状态
    if (isEmpty) {
      return <DefaultEmpty description={emptyDescription || defaultEmptyDescription} />;
    }

    // 内部逻辑：正常渲染
    return <WrappedComponent {...(restProps as P)} />;
  };

  ComponentWithListLoading.displayName = `withListLoading(${componentName})`;

  return ComponentWithListLoading;
}

/**
 * 类型：可重试的加载组件属性
 */
export interface RetryableLoadingProps {
  /** 是否正在加载 */
  loading?: boolean;
  /** 是否加载失败 */
  error?: Error | null;
  /** 重试函数 */
  onRetry?: () => void;
  /** 错误提示 */
  errorTitle?: string;
  /** 错误描述 */
  errorDescription?: string;
}

/**
 * 组件：可重试的加载状态组件
 * 内部逻辑：结合加载、错误、空状态的统一处理
 * 设计模式：状态模式 + 组件模式
 */
export interface RetryableConfig {
  /** 加载提示 */
  loadingTip?: string;
  /** 错误标题 */
  errorTitle?: string;
  /** 空状态描述 */
  emptyDescription?: string;
  /** 自定义渲染函数 */
  renderLoading?: () => ReactNode;
  /** 自定义渲染函数 */
  renderError?: (error: Error, onRetry: () => void) => ReactNode;
  /** 自定义渲染函数 */
  renderEmpty?: () => ReactNode;
}

export function createRetryableComponent(config: RetryableConfig = {}) {
  const {
    loadingTip = '加载中...',
    errorTitle = '加载失败',
    emptyDescription = '暂无数据',
    renderLoading,
    renderError,
    renderEmpty
  } = config;

  /**
   * 可重试状态组件
   */
  const RetryableComponent: React.FC<
    RetryableLoadingProps & {
      children?: ReactNode;
      isEmpty?: boolean;
    }
  > = ({
    loading,
    error,
    onRetry,
    isEmpty,
    children
  }) => {
    // 内部逻辑：加载状态
    if (loading) {
      return <>{renderLoading ? renderLoading() : <DefaultLoading tip={loadingTip} />}</>;
    }

    // 内部逻辑：错误状态
    if (error) {
      return (
        <>
          {renderError ? (
            renderError(error, onRetry || (() => {}))
          ) : (
            <div
              style={{
                padding: '20px',
                textAlign: 'center',
                backgroundColor: 'rgba(255, 77, 79, 0.1)',
                borderRadius: '8px'
              }}
            >
              <h3 style={{ color: '#ff4d4f', margin: '0 0 10px 0' }}>{errorTitle}</h3>
              <p style={{ color: '#ff4d4f', margin: '0 0 15px 0' }}>{error.message}</p>
              {onRetry && (
                <button
                  onClick={onRetry}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#1890ff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  重试
                </button>
              )}
            </div>
          )}
        </>
      );
    }

    // 内部逻辑：空状态
    if (isEmpty) {
      return <>{renderEmpty ? renderEmpty() : <DefaultEmpty description={emptyDescription} />}</>;
    }

    // 内部逻辑：正常渲染子组件
    return <>{children}</>;
  };

  return RetryableComponent;
}

// 导出所有公共接口
export default withLoading;
