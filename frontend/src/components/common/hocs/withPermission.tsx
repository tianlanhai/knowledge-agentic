/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：权限控制高阶组件模块
 * 内部逻辑：为组件添加权限检查能力，控制组件的渲染和交互
 * 设计模式：高阶组件模式（HOC Pattern）+ 代理模式
 * 设计原则：最小权限原则、关注点分离原则
 */

import React, { useState, useEffect, useCallback } from 'react';
import type { ComponentType, ReactNode } from 'react';
import { Result, Button } from 'antd';

/**
 * 权限类型定义
 */
export type Permission = string | number | symbol;

/**
 * 权限检查函数类型
 */
export type PermissionChecker = (
  userPermissions: Permission[],
  requiredPermissions: Permission[]
) => boolean;

/**
 * 权限配置接口
 */
export interface PermissionConfig {
  /** 需要的权限列表（满足任一即可） */
  anyOf?: Permission[];
  /** 需要的权限列表（必须全部满足） */
  allOf?: Permission[];
  /** 自定义权限检查函数 */
  checker?: PermissionChecker;
  /** 无权限时显示的组件 */
  fallback?: ReactNode | ComponentType<{ onRetry?: () => void }>;
  /** 无权限时的提示标题 */
  noAccessTitle?: string;
  /** 无权限时的提示描述 */
  noAccessDescription?: string;
  /** 是否显示重试按钮 */
  showRetry?: boolean;
  /** 权限检查模式 */
  mode?: 'any' | 'all';
  /** 是否在无权限时渲染组件但禁用交互 */
  disableOnNoAccess?: boolean;
}

/**
 * 用户上下文接口
 */
export interface UserContext {
  /** 用户权限列表 */
  permissions: Permission[];
  /** 用户 ID */
  userId?: string | number;
  /** 用户角色 */
  roles?: string[];
}

/**
 * 默认权限检查函数
 * 内部逻辑：检查用户是否拥有所需的所有权限
 */
export const defaultPermissionChecker: PermissionChecker = (
  userPermissions: Permission[],
  requiredPermissions: Permission[]
): boolean => {
  return requiredPermissions.every((permission) =>
    userPermissions.includes(permission)
  );
};

/**
 * 任意权限匹配检查函数
 * 内部逻辑：检查用户是否拥有所需权限中的至少一个
 */
export const anyPermissionChecker: PermissionChecker = (
  userPermissions: Permission[],
  requiredPermissions: Permission[]
): boolean => {
  return requiredPermissions.some((permission) =>
    userPermissions.includes(permission)
  );
};

/**
 * 类：权限管理器
 * 内部逻辑：管理用户权限的获取和验证
 * 设计模式：单例模式
 */
export class PermissionManager {
  /** 内部变量：单例实例 */
  private static instance: PermissionManager;

  /** 内部变量：当前用户权限上下文 */
  private userContext: UserContext | null = null;

  /** 内部变量：权限监听器 */
  private listeners: Array<(context: UserContext | null) => void> = [];

  /**
   * 私有构造函数
   */
  private constructor() {}

  /**
   * 函数级注释：获取单例实例
   * 返回值：PermissionManager 实例
   */
  static getInstance(): PermissionManager {
    if (!PermissionManager.instance) {
      PermissionManager.instance = new PermissionManager();
    }
    return PermissionManager.instance;
  }

  /**
   * 函数级注释：设置用户上下文
   * 参数：
   *   context - 用户上下文
   */
  setUserContext(context: UserContext | null): void {
    this.userContext = context;
    // 内部逻辑：通知所有监听器
    this.listeners.forEach((listener) => listener(context));
  }

  /**
   * 函数级注释：获取用户上下文
   * 返回值：用户上下文或 null
   */
  getUserContext(): UserContext | null {
    return this.userContext;
  }

  /**
   * 函数级注释：检查权限
   * 参数：
   *   config - 权限配置
   *   checker - 权限检查函数
   * 返回值：是否有权限
   */
  hasPermission(
    config: PermissionConfig,
    checker: PermissionChecker = defaultPermissionChecker
  ): boolean {
    // 内部逻辑：无用户上下文视为无权限
    if (!this.userContext) {
      return false;
    }

    const { anyOf, allOf, mode } = config;

    // 内部逻辑：确定所需的权限列表
    const requiredPermissions =
      mode === 'all' || (!mode && allOf)
        ? allOf || []
        : anyOf || [];

    // 内部逻辑：没有权限要求则视为有权限
    if (requiredPermissions.length === 0) {
      return true;
    }

    // 内部逻辑：使用自定义检查函数或默认函数
    const checkerFn = config.checker || (mode === 'any' ? anyPermissionChecker : checker);

    return checkerFn(this.userContext.permissions, requiredPermissions);
  }

  /**
   * 函数级注释：订阅权限变化
   * 参数：
   *   listener - 监听函数
   * 返回值：取消订阅函数
   */
  subscribe(listener: (context: UserContext | null) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  /**
   * 函数级注释：清除用户上下文
   */
  clear(): void {
    this.userContext = null;
    this.listeners.forEach((listener) => listener(null));
  }
}

/**
 * 内部变量：全局权限管理器实例
 */
export const permissionManager = PermissionManager.getInstance();

/**
 * 默认无权限组件
 */
const DefaultNoAccess: React.FC<{
  title?: string;
  description?: string;
  onRetry?: () => void;
}> = ({ title = '无访问权限', description = '您没有访问此资源的权限', onRetry }) => (
  <Result
    status="403"
    title={title}
    subTitle={description}
    extra={
      onRetry ? (
        <Button type="primary" onClick={onRetry}>
          重新检查
        </Button>
      ) : null
    }
  />
);

/**
 * 高阶组件：withPermission
 * 内部逻辑：包装组件，添加权限检查能力
 * 设计模式：高阶组件模式（HOC）+ 代理模式
 * 泛型参数：
 *   P - 原组件的属性类型
 * 参数：
 *   WrappedComponent - 要包装的组件
 *   config - 权限配置
 * 返回值：增强后的组件
 *
 * @example
 * // 基本使用
 * const AdminPanel = withPermission(AdminComponent, {
 *   anyOf: ['admin', 'super_admin']
 * });
 *
 * // 多个权限（全部满足）
 * const SecureComponent = withPermission(Component, {
 *   allOf: ['read', 'write']
 * });
 */
export function withPermission<P extends object>(
  WrappedComponent: ComponentType<P>,
  config: PermissionConfig
): ComponentType<P> {
  const {
    fallback,
    noAccessTitle,
    noAccessDescription,
    showRetry = false,
    disableOnNoAccess = false,
    mode = 'all'
  } = config;

  const componentName =
    WrappedComponent.displayName || WrappedComponent.name || 'Component';

  /**
   * 增强后的组件
   */
  const ComponentWithPermission: React.FC<P> = (props) => {
    // 内部变量：当前权限状态
    const [hasPermission, setHasPermission] = useState<boolean>(() =>
      permissionManager.hasPermission(config)
    );

    // 内部变量：用户上下文
    const [userContext, setUserContext] = useState<UserContext | null>(
      permissionManager.getUserContext()
    );

    /**
     * 函数级注释：重新检查权限
     */
    const recheckPermission = useCallback(() => {
      const result = permissionManager.hasPermission(config);
      setHasPermission(result);
    }, [config]);

    /**
     * 函数级注释：处理权限变化
     */
    useEffect(() => {
      const unsubscribe = permissionManager.subscribe((context) => {
        setUserContext(context);
        setHasPermission(permissionManager.hasPermission(config));
      });

      return unsubscribe;
    }, [config]);

    // 内部逻辑：有权限或禁用模式，渲染组件
    if (hasPermission || disableOnNoAccess) {
      // 内部逻辑：无权限但禁用模式，添加禁用样式
      if (!hasPermission && disableOnNoAccess) {
        return (
          <div
            style={{
              opacity: 0.5,
              pointerEvents: 'none',
              filter: 'grayscale(100%)'
            }}
          >
            <WrappedComponent {...props} />
          </div>
        );
      }

      return <WrappedComponent {...props} />;
    }

    // 内部逻辑：无权限，使用自定义回退组件
    if (fallback) {
      if (React.isValidElement(fallback)) {
        return <>{fallback}</>;
      }
      const FallbackComponent = fallback as ComponentType<{ onRetry?: () => void }>;
      return <FallbackComponent onRetry={showRetry ? recheckPermission : undefined} />;
    }

    // 内部逻辑：使用默认无权限组件
    return (
      <DefaultNoAccess
        title={noAccessTitle}
        description={noAccessDescription}
        onRetry={showRetry ? recheckPermission : undefined}
      />
    );
  };

  // 内部逻辑：设置显示名称
  ComponentWithPermission.displayName = `withPermission(${componentName})`;

  return ComponentWithPermission;
}

/**
 * Hook：usePermission
 * 内部逻辑：提供权限检查的 Hook
 * 设计模式：Hook 模式
 */
export interface UsePermissionResult {
  /** 是否有权限 */
  hasPermission: boolean;
  /** 重新检查权限 */
  recheck: () => void;
  /** 用户上下文 */
  userContext: UserContext | null;
}

export function usePermission(config: PermissionConfig): UsePermissionResult {
  // 内部变量：权限状态
  const [hasPermission, setHasPermission] = useState<boolean>(() =>
    permissionManager.hasPermission(config)
  );

  // 内部变量：用户上下文
  const [userContext, setUserContext] = useState<UserContext | null>(
    permissionManager.getUserContext()
  );

  /**
   * 函数级注释：重新检查权限
   */
  const recheck = useCallback(() => {
    setHasPermission(permissionManager.hasPermission(config));
  }, [config]);

  /**
   * 函数级注释：订阅权限变化
   */
  useEffect(() => {
    const unsubscribe = permissionManager.subscribe((context) => {
      setUserContext(context);
      setHasPermission(permissionManager.hasPermission(config));
    });

    return unsubscribe;
  }, [config]);

  return { hasPermission, recheck, userContext };
}

/**
 * 组件：PermissionGuard
 * 内部逻辑：条件渲染子组件的权限守卫组件
 * 设计模式：组件模式
 */
export interface PermissionGuardProps extends PermissionConfig {
  /** 子组件 */
  children: ReactNode;
  /** 无权限时是否隐藏（不渲染） */
  hideOnNoAccess?: boolean;
}

export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  children,
  hideOnNoAccess = false,
  ...config
}) => {
  const { hasPermission } = usePermission(config);

  // 内部逻辑：无权限时隐藏
  if (hideOnNoAccess && !hasPermission) {
    return null;
  }

  // 内部逻辑：有权限显示子组件
  if (hasPermission) {
    return <>{children}</>;
  }

  // 内部逻辑：无权限显示回退组件
  if (config.fallback) {
    if (React.isValidElement(config.fallback)) {
      return <>{config.fallback}</>;
    }
    const FallbackComponent = config.fallback as ComponentType;
    return <FallbackComponent />;
  }

  // 内部逻辑：默认无权限组件
  return (
    <DefaultNoAccess
      title={config.noAccessTitle}
      description={config.noAccessDescription}
    />
  );
};

/**
 * 高阶组件：withPermissions
 * 内部逻辑：支持多组权限配置的 HOC
 * 设计模式：高阶组件模式
 */
export interface PermissionGroup {
  /** 权限配置 */
  config: PermissionConfig;
  /** 对应的属性键 */
  propKey: string;
}

export function withPermissions<P extends object>(
  WrappedComponent: ComponentType<P>,
  groups: PermissionGroup[]
): ComponentType<P> {
  /**
   * 增强后的组件
   */
  const ComponentWithPermissions: React.FC<P> = (props) => {
    // 内部逻辑：收集权限检查结果
    const permissionResults: Record<string, boolean> = {};

    groups.forEach((group) => {
      // eslint-disable-next-line react-hooks/rules-of-hooks
      const { hasPermission } = usePermission(group.config);
      permissionResults[group.propKey] = hasPermission;
    });

    // 内部逻辑：将权限结果作为额外 props 传递
    return <WrappedComponent {...props} {...(permissionResults as any)} />;
  };

  ComponentWithPermissions.displayName = `withPermissions(${
    WrappedComponent.displayName || WrappedComponent.name || 'Component'
  })`;

  return ComponentWithPermissions;
}

// 导出所有公共接口
export default withPermission;
