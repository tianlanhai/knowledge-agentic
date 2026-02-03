/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：统一的API响应拦截器处理
 * 内部逻辑：处理后端返回的统一响应格式 {success, data/error, message}，提供不同超时级别的API实例
 * 内部变量：api - 默认API实例，apiShort - 短超时API实例，apiLong - 长超时API实例
 */

import axios from 'axios';
import type { AxiosInstance } from 'axios';
import { message } from 'antd';

/**
 * 函数级注释：配置API实例的拦截器
 * 内部逻辑：设置请求和响应拦截器，统一处理错误
 * 参数：instance - 需要配置的API实例
 */
const setupInterceptors = (instance: AxiosInstance) => {
  // 内部逻辑：请求拦截器
  instance.interceptors.request.use(
    (config) => {
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // 内部逻辑：响应拦截器
  instance.interceptors.response.use(
    (response) => {
      /**
       * 成功响应处理
       * 后端现在返回统一格式：{success: true, data: {...}, message: "..."}
       * 前端直接提取data使用
       */
      const { success, data, message: msg } = response.data;

      // 内部逻辑：验证响应格式
      if (success === false) {
        // 内部逻辑：如果success为false，视为错误
        return Promise.reject(new Error(msg || '操作失败'));
      }

      // 内部逻辑：返回实际数据
      return data;
    },
    (error) => {
      /**
       * 错误响应处理
       * 处理HTTP错误和网络错误
       */
      /**
       * 函数级注释：提取错误信息字符串
       * 内部逻辑：处理错误对象可能是字符串或对象的情况
       */
      const extractErrorMessage = (detail: any): string => {
        if (typeof detail === 'string') {
          return detail;
        }
        if (typeof detail === 'object' && detail !== null) {
          // 内部逻辑：处理空对象
          if (Object.keys(detail).length === 0) {
            return '请求失败';
          }
          // 内部逻辑：处理 Pydantic 验证错误格式
          if (Array.isArray(detail)) {
            return detail.map((err: any) => err?.msg || JSON.stringify(err)).join(', ');
          }
          // 内部逻辑：处理带有 msg 字段的错误对象
          if (detail.msg) {
            return detail.msg;
          }
          // 内部逻辑：处理带有 message 字段的错误对象
          if (detail.message) {
            return detail.message;
          }
          // 内部逻辑：其他对象转为字符串
          return JSON.stringify(detail);
        }
        return '请求失败';
      };

      if (error.response) {
        const { status, data } = error.response;

        // 内部变量：提取错误信息
        const errorMsg = extractErrorMessage(data.detail || data.message || data);

        // 内部逻辑：根据HTTP状态码显示不同的错误提示
        switch (status) {
          case 400:
          case 422:
            // 内部逻辑：参数错误或验证错误
            message.error(errorMsg || '请求参数错误');
            break;
          case 401:
            // 内部逻辑：未授权
            message.warning('未授权，请登录');
            break;
          case 403:
            // 内部逻辑：无权限
            message.warning('您没有权限执行此操作');
            break;
          case 404:
            // 内部逻辑：资源不存在
            message.error('资源不存在');
            break;
          case 429:
            // 内部逻辑：请求过于频繁
            message.warning('请求过于频繁，请稍后重试');
            break;
          case 500:
            // 内部逻辑：服务器内部错误
            message.error('服务器内部错误，请稍后重试');
            break;
          case 503:
            // 内部逻辑：服务不可用
            message.error('服务暂时不可用，请稍后重试');
            break;
          default:
            // 内部逻辑：其他错误
            message.error(errorMsg || '请求失败');
        }
      } else if (error.request) {
        // 内部逻辑：网络错误或超时
        if (error.code === 'ECONNABORTED') {
          message.error('请求超时，请检查网络连接或稍后重试');
        } else {
          message.error('网络错误，请检查网络连接');
        }
      } else {
        // 内部逻辑：请求配置错误
        message.error('请求配置错误');
      }

      // 内部逻辑：返回统一的错误对象
      return Promise.reject(error);
    }
  );
};

/**
 * 内部变量：默认API实例配置
 * 说明：用于常规API请求，30秒超时
 */
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 内部变量：短超时API实例配置
 * 说明：用于健康检查等快速请求，5秒超时
 */
const apiShort: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 内部变量：长超时API实例配置
 * 说明：用于文件上传等耗时操作，60秒超时
 */
const apiLong: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 内部逻辑：为所有API实例配置拦截器
setupInterceptors(api);
setupInterceptors(apiShort);
setupInterceptors(apiLong);

// 内部逻辑：导出所有API实例
// 说明：默认导出标准API实例，命名导出用于特殊场景
export default api;
export { apiShort, apiLong };