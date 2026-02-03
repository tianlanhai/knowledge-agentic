/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：前端依赖注入容器模块
 * 内部逻辑：提供 React 环境下的依赖注入实现
 * 设计模式：单例模式 + 依赖注入模式
 * 设计原则：依赖倒置原则（DIP）、开闭原则（OCP）
 */

import { createContext, useContext, ReactNode, useMemo, useRef, useCallback } from 'react';

/**
 * 类级注释：服务生命周期枚举
 * 属性：服务的生命周期类型
 */
export enum ServiceLifetime {
  /** 瞬态 - 每次请求创建新实例 */
  Transient = 'transient',
  /** 作用域 - 同一 Provider 作用域内共享 */
  Scoped = 'scoped',
  /** 单例 - 全局唯一实例 */
  Singleton = 'singleton',
}

/**
 * 类级注释：服务描述符接口
 * 属性：工厂函数、生命周期、依赖
 */
export interface ServiceDescriptor<T = any> {
  /** 内部属性：服务工厂函数 */
  factory: () => T;
  /** 内部属性：服务生命周期 */
  lifetime: ServiceLifetime;
  /** 内部属性：依赖的服务键数组 */
  dependencies?: string[];
}

/**
 * 类级注释：服务配置映射类型
 */
export type ServiceRegistry = Record<string, ServiceDescriptor>;

/**
 * 类级注释：服务容器上下文类型
 */
export interface ServiceContainerContextValue {
  /** 内部变量：服务注册表 */
  services: ServiceRegistry;
  /** 内部变量：服务实例缓存 */
  instances: Map<string, any>;
  /** 内部变量：父容器（用于作用域继承） */
  parent?: ServiceContainerContextValue;
  /** 内部变量：获取服务的方法 */
  getService: <T>(key: string) => T;
  /** 内部变量：注册服务的方法 */
  register: <T>(key: string, descriptor: ServiceDescriptor<T>) => void;
  /** 内部变量：检查服务是否已注册 */
  hasService: (key: string) => boolean;
}

/**
 * 变量：服务容器上下文
 * 内部逻辑：创建 React Context 用于传递容器
 */
const ServiceContainerContext = createContext<ServiceContainerContextValue | null>(null);

/**
 * 类级注释：全局服务容器（单例）
 * 内部逻辑：存储全局单例服务
 */
class GlobalServiceContainer {
  /** 内部变量：单例实例 */
  private static instance: GlobalServiceContainer;

  /** 内部变量：全局单例服务缓存 */
  private singletons = new Map<string, any>();

  /** 内部变量：全局服务注册表 */
  private registry = new Map<string, ServiceDescriptor>();

  /**
   * 函数级注释：获取全局容器实例
   * 返回值：全局容器实例
   */
  static getInstance(): GlobalServiceContainer {
    if (!GlobalServiceContainer.instance) {
      GlobalServiceContainer.instance = new GlobalServiceContainer();
    }
    return GlobalServiceContainer.instance;
  }

  /**
   * 函数级注释：注册全局服务
   * 参数：
   *   key - 服务键
   *   descriptor - 服务描述符
   */
  register(key: string, descriptor: ServiceDescriptor): void {
    this.registry.set(key, descriptor);
  }

  /**
   * 函数级注释：获取全局服务
   * 参数：
   *   key - 服务键
   * 返回值：服务实例
   */
  getService(key: string): any {
    const descriptor = this.registry.get(key);
    if (!descriptor) {
      throw new Error(`服务未注册: ${key}`);
    }

    // 内部逻辑：单例服务使用全局缓存
    if (descriptor.lifetime === ServiceLifetime.Singleton) {
      if (!this.singletons.has(key)) {
        this.singletons.set(key, descriptor.factory());
      }
      return this.singletons.get(key);
    }

    // 内部逻辑：其他服务每次创建新实例
    return descriptor.factory();
  }

  /**
   * 函数级注释：检查服务是否已注册
   * 参数：
   *   key - 服务键
   * 返回值：是否已注册
   */
  has(key: string): boolean {
    return this.registry.has(key);
  }

  /**
   * 函数级注释：清空全局容器
   * 返回值：void
   */
  clear(): void {
    this.singletons.clear();
    this.registry.clear();
  }
}

/**
 * 接口：DI Provider 属性
 */
export interface DIProviderProps {
  /** 内部属性：子组件 */
  children: ReactNode;
  /** 内部属性：服务配置 */
  services?: ServiceRegistry;
  /** 内部属性：是否继承父容器 */
  inheritParent?: boolean;
}

/**
 * 组件：依赖注入 Provider
 * 设计模式：Provider 模式 + 依赖注入模式
 * 内部逻辑：提供服务容器上下文
 *
 * @example
 * ```tsx
 * <DIProvider services={{
 *   'IChatService': {
 *     factory: () => new ChatService(),
 *     lifetime: ServiceLifetime.Scoped
 *   }
 * }}>
 *   <App />
 * </DIProvider>
 * ```
 */
export function DIProvider({ children, services = {}, inheritParent = true }: DIProviderProps) {
  // 内部变量：父容器上下文
  const parentContext = useContext(ServiceContainerContext);

  // 内部变量：当前容器实例缓存
  const instancesRef = useRef(new Map<string, any>());

  // 内部逻辑：合并全局服务注册表
  const globalContainer = GlobalServiceContainer.getInstance();

  // 内部逻辑：创建服务获取函数
  const getService = useCallback(<T,>(key: string): T => {
    // 内部逻辑：优先从当前作用域查找
    if (key in services) {
      const descriptor = services[key];

      // 内部逻辑：作用域服务使用当前缓存
      if (descriptor.lifetime === ServiceLifetime.Scoped) {
        if (!instancesRef.current.has(key)) {
          instancesRef.current.set(key, descriptor.factory());
        }
        return instancesRef.current.get(key);
      }

      // 内部逻辑：单例服务使用全局缓存
      if (descriptor.lifetime === ServiceLifetime.Singleton) {
        return globalContainer.getService(key);
      }

      // 内部逻辑：瞬态服务每次创建新实例
      return descriptor.factory();
    }

    // 内部逻辑：从父容器查找
    if (inheritParent && parentContext) {
      return parentContext.getService<T>(key);
    }

    // 内部逻辑：从全局容器查找
    if (globalContainer.has(key)) {
      return globalContainer.getService(key);
    }

    throw new Error(`服务未注册: ${key}`);
  }, [services, inheritParent, parentContext]);

  // 内部逻辑：创建注册函数
  const register = useCallback(<T,>(key: string, descriptor: ServiceDescriptor<T>) => {
    services[key] = descriptor;
    // 内部逻辑：如果是单例，同时注册到全局容器
    if (descriptor.lifetime === ServiceLifetime.Singleton) {
      globalContainer.register(key, descriptor);
    }
  }, [services]);

  // 内部逻辑：创建检查函数
  const hasService = useCallback((key: string): boolean => {
    if (key in services) return true;
    if (inheritParent && parentContext?.hasService(key)) return true;
    return globalContainer.has(key);
  }, [services, inheritParent, parentContext]);

  // 内部逻辑：创建上下文值
  const contextValue = useMemo<ServiceContainerContextValue>(() => ({
    services,
    instances: instancesRef.current,
    parent: parentContext ?? undefined,
    getService,
    register,
    hasService,
  }), [services, parentContext, getService, register, hasService]);

  return (
    <ServiceContainerContext.Provider value={contextValue}>
      {children}
    </ServiceContainerContext.Provider>
  );
}

/**
 * Hook: 使用服务容器
 * 内部逻辑：获取服务容器实例
 * 返回值：服务容器上下文
 *
 * @throws {Error} - 在 DIProvider 外部使用时抛出
 */
export function useServiceContainer(): ServiceContainerContextValue {
  const context = useContext(ServiceContainerContext);
  if (!context) {
    throw new Error('useServiceContainer 必须在 DIProvider 内部使用');
  }
  return context;
}

/**
 * Hook: 注入服务
 * 设计模式：依赖注入模式
 * 内部逻辑：根据服务键获取服务实例
 *
 * @param key - 服务键
 * @returns 服务实例
 *
 * @example
 * ```tsx
 * const chatService = useService<IChatService>('IChatService');
 * ```
 */
export function useService<T = any>(key: string): T {
  const { getService } = useServiceContainer();
  return getService<T>(key);
}

/**
 * Hook: 注入多个服务
 * 设计模式：依赖注入模式
 * 内部逻辑：批量获取服务实例
 *
 * @param keys - 服务键数组
 * @returns 服务实例数组
 *
 * @example
 * ```tsx
 * const [chatService, userService] = useServices(['IChatService', 'IUserService']);
 * ```
 */
export function useServices<T = any>(keys: string[]): T[] {
  const { getService } = useServiceContainer();
  return keys.map(key => getService<T>(key));
}

/**
 * Hook: 创建服务消费者组件
 * 设计模式：高阶组件模式 + 依赖注入模式
 *
 * @param serviceKeys - 需要注入的服务键
 * @returns 服务实例对象
 *
 * @example
 * ```tsx
 * const { chatService, userService } = useInjectedServices({
 *   chatService: 'IChatService',
 *   userService: 'IUserService'
 * });
 * ```
 */
export function useInjectedServices<T extends Record<string, string>>(
  serviceKeys: T
): Record<keyof T, any> {
  const { getService } = useServiceContainer();

  return useMemo(() => {
    const result = {} as Record<keyof T, any>;
    for (const [propName, serviceKey] of Object.entries(serviceKeys)) {
      result[propName as keyof T] = getService(serviceKey);
    }
    return result;
  }, [getService, serviceKeys]);
}

/**
 * 类级注释：全局服务注册器
 * 内部逻辑：提供全局服务的注册方法
 */
export class ServiceRegistry {
  /**
   * 函数级注释：注册单例服务
   * 参数：
   *   key - 服务键
   *   factory - 工厂函数
   * 返回值：void
   */
  static registerSingleton(key: string, factory: () => any): void {
    GlobalServiceContainer.getInstance().register(key, {
      factory,
      lifetime: ServiceLifetime.Singleton,
    });
  }

  /**
   * 函数级注释：批量注册服务
   * 参数：
   *   services - 服务配置映射
   * 返回值：void
   */
  static registerServices(services: Record<string, ServiceDescriptor>): void {
    const container = GlobalServiceContainer.getInstance();
    for (const [key, descriptor] of Object.entries(services)) {
      container.register(key, descriptor);
    }
  }

  /**
   * 函数级注释：获取全局服务
   * 参数：
   *   key - 服务键
   * 返回值：服务实例
   */
  static getGlobalService<T = any>(key: string): T {
    return GlobalServiceContainer.getInstance().getService(key);
  }

  /**
   * 函数级注释：清空全局服务
   * 返回值：void
   */
  static clear(): void {
    GlobalServiceContainer.getInstance().clear();
  }
}

/**
 * 类级注释：服务装饰器工厂（模拟）
 * 内部逻辑：为类添加服务元数据
 */
export function Injectable(lifetime: ServiceLifetime = ServiceLifetime.Transient) {
  return function <T extends { new (...args: any[]): {} }>(constructor: T) {
    // 内部逻辑：添加元数据
    (constructor as any).__injectable__ = true;
    (constructor as any).__lifetime__ = lifetime;
    return constructor;
  };
}

// 导出所有公共接口
export {
  ServiceContainerContext,
  GlobalServiceContainer,
};
