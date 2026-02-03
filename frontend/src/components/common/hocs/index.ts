/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：高阶组件统一导出模块
 * 内部逻辑：集中导出所有 HOC，方便使用
 * 设计模式：外观模式（Facade Pattern）
 */

// 导出错误边界 HOC
export {
  ErrorBoundary,
  withErrorBoundary,
  withAsyncErrorBoundary
} from './withErrorBoundary';
export type {
  ErrorBoundaryProps,
  WithErrorBoundaryOptions,
  AsyncErrorBoundaryProps
} from './withErrorBoundary';

// 导出加载状态 HOC
export {
  withLoading,
  withSuspenseLoading,
  withListLoading,
  createRetryableComponent
} from './withLoading';
export type {
  LoadingConfig,
  WithLoadingProps,
  ListData,
  WithListLoadingProps,
  RetryableLoadingProps,
  RetryableConfig
} from './withLoading';

// 导出权限控制 HOC
export {
  withPermission,
  withPermissions,
  PermissionGuard,
  usePermission,
  permissionManager,
  PermissionManager
} from './withPermission';
export type {
  Permission,
  PermissionChecker,
  PermissionConfig,
  UserContext,
  UsePermissionResult,
  PermissionGroup,
  PermissionGuardProps
} from './withPermission';

// 默认导出所有 HOC
export { default as withErrorBoundaryHOC } from './withErrorBoundary';
export { default as withLoadingHOC } from './withLoading';
export { default as withPermissionHOC } from './withPermission';
