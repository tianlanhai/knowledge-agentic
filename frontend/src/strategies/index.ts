/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：策略模块入口
 * 内部逻辑：导出所有策略相关功能
 */

export type { ButtonVariantStrategy } from './buttonVariantStrategies';
export type { ButtonVariant } from './buttonVariantStrategies';
export {
  getVariantStyles,
  applyVariantStyles,
} from './buttonVariantStrategies';
export { default as ButtonVariantStrategyFactory } from './buttonVariantStrategies';
