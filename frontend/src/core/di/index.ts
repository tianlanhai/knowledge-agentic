/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：前端依赖注入模块导出文件
 * 内部逻辑：统一导出所有依赖注入相关的类型和函数
 */

// 导出核心组件和 Hook
export {
  DIProvider,
  useServiceContainer,
  useService,
  useServices,
  useInjectedServices,
  Injectable,
  ServiceContainerContext,
  GlobalServiceContainer,
} from './ServiceContainer';

// 导出类型定义（ServiceRegistry 是类型，已在下方导出）
export type {
  ServiceRegistry,
  ServiceDescriptor,
  ServiceContainerContextValue,
} from './ServiceContainer';

// 导出枚举
export { ServiceLifetime } from './ServiceContainer';
