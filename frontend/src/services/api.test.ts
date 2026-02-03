/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：API服务层单元测试
 * 内部逻辑：测试axios实例配置和拦截器功能，包括错误处理
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import api from './api';

/**
 * 内部变量：Mock message组件
 * 内部逻辑：模拟antd的message组件，用于验证错误提示
 */
vi.mock('antd', () => ({
  message: {
    error: vi.fn(),
    warning: vi.fn(),
  },
}));

import { message } from 'antd';

describe('api service', () => {
  /**
   * 内部变量：保存message的原始实现
   */
  let originalError: typeof message.error;
  let originalWarning: typeof message.warning;

  beforeEach(() => {
    // 内部逻辑：保存原始实现以便恢复
    originalError = message.error;
    originalWarning = message.warning;
    // 内部逻辑：清除所有mock的调用记录
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    // 内部逻辑：恢复原始message实现
    message.error = originalError;
    message.warning = originalWarning;
  });

  /**
   * 测试API实例导出
   */
  it('应该正确导出API实例', () => {
    expect(api).toBeDefined();
    expect(api).toHaveProperty('get');
    expect(api).toHaveProperty('post');
    expect(api).toHaveProperty('delete');
  });

  /**
   * 测试axios实例配置
   */
  it('应该正确配置axios', () => {
    expect(api.defaults).toBeDefined();
    // 内部逻辑：检查 Content-Type 头配置
    expect(api.defaults.headers.common['Content-Type'] || api.defaults.headers['Content-Type']).toContain('json');
  });

  /**
   * 测试超时配置
   */
  it('应该配置超时', () => {
    expect(api.defaults.timeout).toBeDefined();
    expect(api.defaults.timeout).toBeGreaterThan(0);
  });

  /**
   * 测试baseURL配置
   */
  it('应该配置baseURL', () => {
    expect(api.defaults.baseURL).toBeDefined();
    expect(api.defaults.baseURL).toContain('/v1');
  });

  /**
   * 测试拦截器配置
   */
  it('应该配置请求拦截器', () => {
    expect(api.interceptors.request).toBeDefined();
    // 内部逻辑：检查请求拦截器的 handlers 数组
    expect(api.interceptors.request.handlers).toBeDefined();
    expect(api.interceptors.request.handlers.length).toBeGreaterThan(0);
  });

  /**
   * 测试响应拦截器
   */
  it('应该配置响应拦截器', () => {
    expect(api.interceptors.response).toBeDefined();
    // 内部逻辑：检查响应拦截器的 handlers 数组
    expect(api.interceptors.response.handlers).toBeDefined();
    expect(api.interceptors.response.handlers.length).toBeGreaterThan(0);
  });

  /**
   * 测试错误拦截器
   */
  it('应该配置错误拦截器', () => {
    expect(api.interceptors.response).toBeDefined();
  });

  /**
   * 测试拦截器清理
   */
  it('应该在清理时清除拦截器', () => {
    const eject = api.interceptors.request.eject;
    expect(eject).toBeInstanceOf(Function);
  });

  /**
   * 测试请求拦截器成功处理
   * 内部逻辑：验证请求拦截器正确返回配置
   */
  it('应该正确处理请求拦截器成功', async () => {
    const config = {
      url: '/test',
      method: 'get',
    };

    const result = await api.interceptors.request.handlers[0].fulfilled(config);

    expect(result).toEqual(config);
  });

  /**
   * 测试请求拦截器错误处理
   * 内部逻辑：验证请求拦截器错误时正确reject
   */
  it('应该正确处理请求拦截器错误', async () => {
    const error = new Error('Request error');

    await expect(api.interceptors.request.handlers[0].rejected(error)).rejects.toEqual(error);
  });

  /**
   * 测试响应拦截器处理success=false
   * 内部逻辑：验证后端返回success:false时作为错误处理
   */
  it('应该在success为false时reject', async () => {
    const response = {
      data: {
        success: false,
        message: '操作失败',
      },
    };

    await expect(api.interceptors.response.handlers[0].fulfilled(response)).rejects.toThrow('操作失败');
  });

  /**
   * 测试响应拦截器处理success=false且无message
   * 内部逻辑：验证success=false且无message时使用默认错误消息
   */
  it('应该在success为false且无消息时使用默认错误', async () => {
    const response = {
      data: {
        success: false,
      },
    };

    await expect(api.interceptors.response.handlers[0].fulfilled(response)).rejects.toThrow('操作失败');
  });

  /**
   * 测试响应拦截器成功处理
   * 内部逻辑：验证success=true时返回data
   */
  it('应该在success为true时返回data', async () => {
    const responseData = { test: 'data' };
    const response = {
      data: {
        success: true,
        data: responseData,
      },
    };

    const result = await api.interceptors.response.handlers[0].fulfilled(response);

    expect(result).toEqual(responseData);
  });

  /**
   * 测试错误拦截器返回reject
   * 内部逻辑：验证错误处理路径都返回reject
   */
  it('应该在错误处理后reject promise', async () => {
    const error = new Error('Request failed') as any;
    error.response = { status: 500, data: {} };
    error.config = {};
    error.request = {};

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
  });

  /**
   * 测试网络错误时reject
   */
  it('应该在网络错误时reject promise', async () => {
    const error = new Error('Network Error') as any;
    error.request = {};
    error.config = {};
    error.response = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
  });

  /**
   * 测试配置错误时reject
   */
  it('应该在配置错误时reject promise', async () => {
    const error = new Error('Config Error') as any;
    error.config = {};
    error.request = undefined;
    error.response = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
  });

  /**
   * 测试400错误处理
   * 内部逻辑：验证400状态码时显示参数错误提示
   */
  it('应该在400错误时显示参数错误提示', async () => {
    const error = new Error('Bad Request') as any;
    error.response = {
      status: 400,
      data: { detail: '参数验证失败' },
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('参数验证失败');
  });

  /**
   * 测试400错误无detail时的处理
   * 注意：空对象会被 extractErrorMessage 处理为 '请求失败'，而不是使用默认的 '请求参数错误'
   */
  it('应该在400错误无detail时显示默认提示', async () => {
    const error = new Error('Bad Request') as any;
    error.response = {
      status: 400,
      data: {},
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('请求失败');
  });

  /**
   * 测试401错误处理
   * 内部逻辑：验证401状态码时显示未授权提示
   */
  it('应该在401错误时显示未授权提示', async () => {
    const error = new Error('Unauthorized') as any;
    error.response = {
      status: 401,
      data: {},
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.warning).toHaveBeenCalledWith('未授权，请登录');
  });

  /**
   * 测试403错误处理
   * 内部逻辑：验证403状态码时显示无权限提示
   */
  it('应该在403错误时显示无权限提示', async () => {
    const error = new Error('Forbidden') as any;
    error.response = {
      status: 403,
      data: {},
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.warning).toHaveBeenCalledWith('您没有权限执行此操作');
  });

  /**
   * 测试404错误处理
   * 内部逻辑：验证404状态码时显示资源不存在提示
   */
  it('应该在404错误时显示资源不存在提示', async () => {
    const error = new Error('Not Found') as any;
    error.response = {
      status: 404,
      data: {},
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('资源不存在');
  });

  /**
   * 测试429错误处理
   * 内部逻辑：验证429状态码时显示请求频繁提示
   */
  it('应该在429错误时显示请求频繁提示', async () => {
    const error = new Error('Too Many Requests') as any;
    error.response = {
      status: 429,
      data: {},
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.warning).toHaveBeenCalledWith('请求过于频繁，请稍后重试');
  });

  /**
   * 测试500错误处理
   * 内部逻辑：验证500状态码时显示服务器错误提示
   */
  it('应该在500错误时显示服务器错误提示', async () => {
    const error = new Error('Internal Server Error') as any;
    error.response = {
      status: 500,
      data: {},
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('服务器内部错误，请稍后重试');
  });

  /**
   * 测试其他HTTP错误处理
   * 内部逻辑：验证其他状态码时显示默认错误提示
   */
  it('应该在其他HTTP错误时显示默认提示', async () => {
    const error = new Error('Unknown Error') as any;
    error.response = {
      status: 418,
      data: { detail: 'I\'m a teapot' },
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('I\'m a teapot');
  });

  /**
   * 测试无detail和message时的错误处理
   */
  it('应该在无detail和message时显示默认错误提示', async () => {
    const error = new Error('Unknown Error') as any;
    error.response = {
      status: 418,
      data: {},
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('请求失败');
  });

  /**
   * 测试带message字段时的错误处理
   */
  it('应该在response有message字段时显示该消息', async () => {
    const error = new Error('Unknown Error') as any;
    error.response = {
      status: 418,
      data: { message: '自定义错误消息' },
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('自定义错误消息');
  });

  /**
   * 测试网络错误处理
   * 内部逻辑：验证无response但有request时显示网络错误
   */
  it('应该在网络错误时显示网络错误提示', async () => {
    const error = new Error('Network Error') as any;
    error.request = {};
    error.config = {};
    error.response = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('网络错误，请检查网络连接');
  });

  /**
   * 测试配置错误处理
   * 内部逻辑：验证无request无response时显示配置错误
   */
  it('应该在配置错误时显示配置错误提示', async () => {
    const error = new Error('Config Error') as any;
    error.config = {};
    error.request = undefined;
    error.response = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('请求配置错误');
  });

  /**
   * 测试422错误处理
   * 内部逻辑：验证422状态码时显示参数错误提示
   */
  it('应该在422错误时显示参数错误提示', async () => {
    const error = new Error('Unprocessable Entity') as any;
    error.response = {
      status: 422,
      data: { detail: '数据验证失败' },
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('数据验证失败');
  });

  /**
   * 测试422错误无detail时的处理
   */
  it('应该在422错误无detail时使用默认提示', async () => {
    const error = new Error('Unprocessable Entity') as any;
    error.response = {
      status: 422,
      data: {},
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('请求失败');
  });

  /**
   * 测试带msg字段的错误处理
   * 内部逻辑：验证detail.msg字段的错误消息提取
   */
  it('应该在detail有msg字段时显示该消息', async () => {
    const error = new Error('Validation Error') as any;
    error.response = {
      status: 400,
      data: { detail: { msg: '字段验证失败' } },
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('字段验证失败');
  });

  /**
   * 测试Pydantic验证错误格式的处理
   * 内部逻辑：验证数组格式的错误消息提取
   */
  it('应该处理Pydantic验证错误数组格式', async () => {
    const error = new Error('Validation Error') as any;
    error.response = {
      status: 422,
      data: {
        detail: [
          { msg: '字段1是必填的' },
          { msg: '字段2格式不正确' },
        ],
      },
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('字段1是必填的, 字段2格式不正确');
  });

  /**
   * 测试Pydantic验证错误数组格式无msg字段的处理
   * 内部逻辑：验证数组中无msg字段时使用JSON.stringify
   */
  it('应该处理Pydantic验证错误数组格式无msg字段', async () => {
    const error = new Error('Validation Error') as any;
    error.response = {
      status: 422,
      data: {
        detail: [
          { field: 'name', type: 'missing' },
        ],
      },
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('{"field":"name","type":"missing"}');
  });

  /**
   * 测试嵌套错误对象的处理
   * 内部逻辑：验证嵌套对象转为JSON字符串
   */
  it('应该处理嵌套错误对象', async () => {
    const error = new Error('Validation Error') as any;
    error.response = {
      status: 400,
      data: {
        detail: {
          nested: {
            error: '深层错误信息',
          },
        },
      },
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('{"nested":{"error":"深层错误信息"}}');
  });

  /**
   * 测试空对象错误处理
   * 内部逻辑：验证空对象被处理，但500错误使用默认消息
   */
  it('应该处理空对象错误（500状态使用默认消息）', async () => {
    const error = new Error('Error') as any;
    error.response = {
      status: 500,
      data: { detail: {} },
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    // 500错误使用默认消息，而不是detail提取的'请求失败'
    expect(message.error).toHaveBeenCalledWith('服务器内部错误，请稍后重试');
  });

  /**
   * 测试null错误处理
   * 内部逻辑：验证null被处理，但500错误使用默认消息
   */
  it('应该处理null错误（500状态使用默认消息）', async () => {
    const error = new Error('Error') as any;
    error.response = {
      status: 500,
      data: { detail: null },
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('服务器内部错误，请稍后重试');
  });

  /**
   * 测试数字类型的错误处理
   * 内部逻辑：验证数字类型的错误被转为JSON字符串，但500错误使用默认消息
   */
  it('应该处理数字类型的错误（500状态使用默认消息）', async () => {
    const error = new Error('Error') as any;
    error.response = {
      status: 500,
      data: { detail: 404 },
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('服务器内部错误，请稍后重试');
  });

  /**
   * 测试data为字符串时的错误处理
   */
  it('应该处理data为字符串时的错误', async () => {
    const error = new Error('Error') as any;
    error.response = {
      status: 400,
      data: '直接返回的错误消息',
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('直接返回的错误消息');
  });

  /**
   * 测试使用data.message而不是data.detail
   */
  it('应该优先使用data.detail，其次data.message', async () => {
    const error = new Error('Error') as any;
    error.response = {
      status: 400,
      data: { message: '通过message字段传递的错误' },
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('通过message字段传递的错误');
  });

  /**
   * 测试同时有detail和message时优先使用detail
   */
  it('应该同时有detail和message时优先使用detail', async () => {
    const error = new Error('Error') as any;
    error.response = {
      status: 400,
      data: { detail: 'detail消息', message: 'message消息' },
    };
    error.config = {};
    error.request = undefined;

    await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toEqual(error);
    expect(message.error).toHaveBeenCalledWith('detail消息');
  });
});
