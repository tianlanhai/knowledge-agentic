/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：错误边界高阶组件模块
 * 内部逻辑：为组件添加错误边界处理能力，捕获渲染错误并显示友好提示
 * 设计模式：高阶组件模式（HOC Pattern）+ 装饰器模式
 * 设计原则：关注点分离原则、开闭原则
 */

import React, { Component } from 'react';
import type { ComponentType, ReactNode } from 'react';

/**
 * 错误边界属性接口
 */
export interface ErrorBoundaryProps {
  /** 子组件 */
  children?: ReactNode;
  /** 发生错误时显示的回退组件 */
  fallback?: ReactNode | ComponentType<{ error: Error; retry: () => void }>;
  /** 错误回调函数 */
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  /** 组件名称（用于日志） */
  componentName?: string;
}

/**
 * 错误边界状态接口
 */
interface ErrorBoundaryState {
  /** 是否发生错误 */
  hasError: boolean;
  /** 错误对象 */
  error: Error | null;
}

/**
 * 默认错误回退组件
 */
const DefaultFallback: ComponentType<{ error: Error; retry: () => void }> = ({
  error,
  retry
}) => (
  <div
    style={{
      padding: '20px',
      backgroundColor: 'rgba(255, 77, 79, 0.1)',
      border: '1px solid rgba(255, 77, 79, 0.3)',
      borderRadius: '8px',
      textAlign: 'center'
    }}
  >
    <h3 style={{ color: '#ff4d4f', margin: '0 0 10px 0' }}>
      出错了
    </h3>
    <p style={{ color: '#ff4d4f', margin: '0 0 15px 0', fontSize: '14px' }}>
      {error.message}
    </p>
    <button
      onClick={retry}
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
  </div>
);

/**
 * 类：错误边界组件
 * 内部逻辑：捕获子组件树中的 JavaScript 错误，记录错误日志并显示备用 UI
 * 设计模式：组件模式 + 错误处理模式
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  /**
   * 函数级注释：初始化状态
   */
  state: ErrorBoundaryState = {
    hasError: false,
    error: null
  };

  /**
   * 函数级注释：捕获子组件抛出的错误
   * 内部逻辑：更新状态 -> 记录错误
   * 参数：
   *   error - 错误对象
   *   errorInfo - 错误信息
   * 返回值：新的状态对象
   */
  static getDerivedStateFromError(
    error: Error
  ): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }

  /**
   * 函数级注释：捕获错误信息后的副作用
   * 内部逻辑：调用错误回调 -> 记录日志
   * 参数：
   *   error - 错误对象
   *   errorInfo - 错误信息
   */
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    const { onError, componentName } = this.props;

    // 内部逻辑：记录错误日志
    console.error(
      `[ErrorBoundary${componentName ? `: ${componentName}` : ''}]`,
      error,
      errorInfo
    );

    // 内部逻辑：调用错误回调
    if (onError) {
      onError(error, errorInfo);
    }
  }

  /**
   * 函数级注释：重试恢复
   * 内部逻辑：重置错误状态
   */
  handleRetry = (): void => {
    this.setState({
      hasError: false,
      error: null
    });
  };

  /**
   * 函数级注释：渲染方法
   * 内部逻辑：有错误显示回退组件 -> 无错误显示子组件
   */
  render(): ReactNode {
    const { hasError, error } = this.state;
    const { children, fallback } = this.props;

    if (hasError && error) {
      // 内部逻辑：使用自定义回退组件或默认组件
      if (React.isValidElement(fallback)) {
        return fallback;
      }

      if (typeof fallback === 'function') {
        const FallbackComponent = fallback as ComponentType<{
          error: Error;
          retry: () => void;
        }>;
        return <FallbackComponent error={error} retry={this.handleRetry} />;
      }

      return <DefaultFallback error={error} retry={this.handleRetry} />;
    }

    return children;
  }
}

/**
 * 高阶组件：withErrorBoundary
 * 内部逻辑：包装组件，添加错误边界处理能力
 * 设计模式：高阶组件模式（HOC）
 * 泛型参数：
 *   P - 原组件的属性类型
 * 参数：
 *   options - 配置选项
 * 返回值：增强后的组件
 *
 * @example
 * // 基本使用
 * const MyComponentWithErrorBoundary = withErrorBoundary(MyComponent);
 *
 * // 自定义配置
 * const EnhancedComponent = withErrorBoundary(MyComponent, {
 *   fallback: <CustomError />,
 *   onError: (error) => logError(error),
 *   componentName: 'MyComponent'
 * });
 */
export interface WithErrorBoundaryOptions {
  /** 错误回退组件 */
  fallback?: ReactNode | ComponentType<{ error: Error; retry: () => void }>;
  /** 错误回调 */
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  /** 组件名称 */
  componentName?: string;
}

export function withErrorBoundary<
  P extends object
>(
  WrappedComponent: ComponentType<P>,
  options: WithErrorBoundaryOptions = {}
): ComponentType<P> {
  const {
    fallback,
    onError,
    componentName = WrappedComponent.displayName || WrappedComponent.name || 'Component'
  } = options;

  /**
   * 增强后的组件
   */
  const ComponentWithErrorBoundary: React.FC<P> = (props) => {
    return (
      <ErrorBoundary
        fallback={fallback}
        onError={onError}
        componentName={componentName}
      >
        <WrappedComponent {...props} />
      </ErrorBoundary>
    );
  };

  // 内部逻辑：设置显示名称以便调试
  ComponentWithErrorBoundary.displayName = `withErrorBoundary(${componentName})`;

  return ComponentWithErrorBoundary;
}

/**
 * 高阶组件：withAsyncErrorBoundary
 * 内部逻辑：处理异步错误的高阶组件
 * 设计模式：高阶组件模式（HOC）
 * 说明：除了捕获渲染错误，还能处理异步操作中的错误
 */
export interface AsyncErrorBoundaryProps {
  /** 异步错误 */
  asyncError?: Error | null;
  /** 清除异步错误 */
  clearAsyncError?: () => void;
}

export function withAsyncErrorBoundary<
  P extends object
>(
  WrappedComponent: ComponentType<P>,
  options: WithErrorBoundaryOptions = {}
): ComponentType<Omit<P, 'asyncError' | 'clearAsyncError'> & AsyncErrorBoundaryProps> {
  const {
    fallback,
    onError,
    componentName = WrappedComponent.displayName || WrappedComponent.name || 'Component'
  } = options;

  /**
   * 增后的组件
   */
  const ComponentWithAsyncErrorBoundary: React.FC<P & AsyncErrorBoundaryProps> = ({
    asyncError,
    clearAsyncError,
    ...props
  }) => {
    // 内部逻辑：如果有异步错误，显示错误界面
    if (asyncError) {
      const handleRetry = () => {
        if (clearAsyncError) {
          clearAsyncError();
        }
      };

      if (React.isValidElement(fallback)) {
        return fallback;
      }

      if (typeof fallback === 'function') {
        const FallbackComponent = fallback as ComponentType<{
          error: Error;
          retry: () => void;
        }>;
        return <FallbackComponent error={asyncError} retry={handleRetry} />;
      }

      return <DefaultFallback error={asyncError} retry={handleRetry} />;
    }

    return (
      <ErrorBoundary
        fallback={fallback}
        onError={onError}
        componentName={componentName}
      >
        <WrappedComponent {...(props as P)} />
      </ErrorBoundary>
    );
  };

  ComponentWithAsyncErrorBoundary.displayName = `withAsyncErrorBoundary(${componentName})`;

  return ComponentWithAsyncErrorBoundary as any;
}

// 导出所有公共接口
export { ErrorBoundary };
export default ErrorBoundary;
