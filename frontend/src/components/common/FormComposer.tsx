/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：表单组合器组件
 * 内部逻辑：使用组合模式和建造者模式动态构建表单
 * 设计模式：组合模式（Composite Pattern）+ 建造者模式（Builder Pattern）
 * 设计原则：开闭原则、单一职责原则
 *
 * @package frontend/src/components/common
 */

import React, { forwardRef, useImperativeHandle, useRef, useMemo } from 'react';
import { Form } from 'antd';
import type { FormInstance, FormProps } from 'antd';
import type { Rule } from 'antd/es/form';

/**
 * 类级注释：表单字段配置接口
 * 内部逻辑：定义表单字段的配置选项
 */
export interface FormFieldConfig<T = any> {
  /** 字段名称 */
  name: string | string[];
  /** 字段标签 */
  label: string;
  /** 表单组件类型 */
  component: React.ComponentType<any>;
  /** 表单组件属性 */
  componentProps?: Record<string, any>;
  /** 验证规则 */
  rules?: Rule[];
  /** 是否必填 */
  required?: boolean;
  /** 必填错误消息 */
  requiredMessage?: string;
  /** 额外属性 */
  extra?: string;
  /** 提示信息 */
  tooltip?: string;
  /** 是否隐藏 */
  hidden?: boolean;
  /** 条件渲染函数 */
  visible?: (form: FormInstance) => boolean;
  /** 字段依赖（当依赖字段变化时重新渲染） */
  dependencies?: string[];
  /** 初始值 */
  initialValue?: any;
  /** 自定义渲染函数 */
  render?: (field: any, form: FormInstance) => React.ReactNode;
}

/**
 * 类级注释：表单分组配置接口
 */
export interface FormGroupConfig {
  /** 分组标题 */
  title?: string;
  /** 分组字段 */
  fields: FormFieldConfig[];
  /** 分组属性 */
  groupProps?: {
    collapsible?: boolean;
    defaultCollapsed?: boolean;
    extra?: React.ReactNode;
  };
}

/**
 * 类级注释：表单配置选项接口
 */
export interface FormComposerOptions {
  /** 表单布局 */
  layout?: 'horizontal' | 'vertical' | 'inline';
  /** 标签宽度 */
  labelCol?: any;
  /** 包装器宽度 */
  wrapperCol?: any;
  /** 提交成功回调 */
  onSubmitSuccess?: (values: any) => void | Promise<void>;
  /** 提交失败回调 */
  onSubmitError?: (error: any) => void;
  /** 提交前钩子 */
  beforeSubmit?: (values: any) => boolean | Promise<boolean>;
  /** 重置后回调 */
  onReset?: () => void;
  /** 值变化回调 */
  onValuesChange?: (changedValues: any, allValues: any) => void;
  /** 表单名称 */
  name?: string;
  /** 表单初始值 */
  initialValues?: Record<string, any>;
}

/**
 * 类级注释：表单组件暴露的接口
 */
export interface FormComposerRef {
  /** 提交表单 */
  submit: () => Promise<void>;
  /** 重置表单 */
  reset: () => void;
  /** 设置字段值 */
  setFieldValue: (name: string, value: any) => void;
  /** 获取字段值 */
  getFieldValue: (name: string) => any;
  /** 设置表单值 */
  setFieldsValue: (values: Record<string, any>) => void;
  /** 获取表单值 */
  getFieldsValue: (nameList?: string[]) => Record<string, any>;
  /** 验证字段 */
  validateFields: (nameList?: string[]) => Promise<any>;
  /** 获取表单实例 */
  getForm: () => FormInstance;
}

/**
 * 组件：FormComposer
 * 内部逻辑：动态组合表单字段，提供链式API
 * 设计模式：建造者模式 + 组合模式
 *
 * @example
 * ```typescript
 * const form = new FormBuilder()
 *   .addField({
 *     name: 'username',
 *     label: '用户名',
 *     component: Input,
 *     rules: [{ required: true, message: '请输入用户名' }]
 *   })
 *   .addGroup({
 *     title: '高级设置',
 *     fields: [
 *       { name: 'email', label: '邮箱', component: Input }
 *     ]
 *   })
 *   .build();
 * ```
 */
export class FormBuilder {
  /** 内部变量：表单字段列表 */
  private fields: FormFieldConfig[] = [];
  /** 内部变量：表单分组列表 */
  private groups: FormGroupConfig[] = [];
  /** 内部变量：表单配置选项 */
  private options: FormComposerOptions = {};

  /**
   * 函数级注释：添加单个字段
   * 参数：
   *   field - 字段配置
   * 返回值：建造者实例（支持链式调用）
   */
  addField(field: FormFieldConfig): this {
    this.fields.push(field);
    return this;
  }

  /**
   * 函数级注释：批量添加字段
   * 参数：
   *   fields - 字段配置数组
   * 返回值：建造者实例（支持链式调用）
   */
  addFields(fields: FormFieldConfig[]): this {
    this.fields.push(...fields);
    return this;
  }

  /**
   * 函数级注释：添加分组
   * 参数：
   *   group - 分组配置
   * 返回值：建造者实例（支持链式调用）
   */
  addGroup(group: FormGroupConfig): this {
    this.groups.push(group);
    // 内部逻辑：将分组内的字段也添加到字段列表
    this.fields.push(...group.fields);
    return this;
  }

  /**
   * 函数级注释：设置表单配置
   * 参数：
   *   options - 表单配置选项
   * 返回值：建造者实例（支持链式调用）
   */
  setOptions(options: Partial<FormComposerOptions>): this {
    this.options = { ...this.options, ...options };
    return this;
  }

  /**
   * 函数级注释：设置提交成功回调
   * 参数：
   *   callback - 成功回调函数
   * 返回值：建造者实例（支持链式调用）
   */
  onSuccess(callback: (values: any) => void | Promise<void>): this {
    this.options.onSubmitSuccess = callback;
    return this;
  }

  /**
   * 函数级注释：设置提交失败回调
   * 参数：
   *   callback - 失败回调函数
   * 返回值：建造者实例（支持链式调用）
   */
  onError(callback: (error: any) => void): this {
    this.options.onSubmitError = callback;
    return this;
  }

  /**
   * 函数级注释：设置提交前钩子
   * 参数：
   *   hook - 钩子函数，返回false将阻止提交
   * 返回值：建造者实例（支持链式调用）
   */
  beforeSubmit(hook: (values: any) => boolean | Promise<boolean>): this {
    this.options.beforeSubmit = hook;
    return this;
  }

  /**
   * 函数级注释：设置初始值
   * 参数：
   *   values - 初始值对象
   * 返回值：建造者实例（支持链式调用）
   */
  initialValues(values: Record<string, any>): this {
    this.options.initialValues = { ...this.options.initialValues, ...values };
    return this;
  }

  /**
   * 函数级注释：构建表单组件
   * 返回值：React 组件
   */
  build(): React.ForwardRefExoticComponent<React.RefAttributes<FormComposerRef>> {
    // 内部逻辑：创建表单组件
    const FormComponent = forwardRef<FormComposerRef, any>((props, ref) => (
      <FormComposer
        ref={ref}
        fields={this.fields}
        groups={this.groups}
        options={this.options}
        {...props}
      />
    ));
    FormComponent.displayName = 'FormComposer';
    return FormComponent;
  }
}

/**
 * 组件：FormComposer 内部实现
 */
const FormComposer = forwardRef<FormComposerRef, {
  fields: FormFieldConfig[];
  groups?: FormGroupConfig[];
  options?: FormComposerOptions;
  [key: string]: any;
}>((props, ref) => {
  const { fields, groups = [], options = {}, ...restProps } = props;
  const [form] = Form.useForm();
  const formRef = useRef<FormInstance>(null);

  // 内部逻辑：暴露表单方法
  useImperativeHandle(ref, () => ({
    submit: async () => {
      try {
        const values = await form.validateFields();
        if (options.beforeSubmit) {
          const canSubmit = await options.beforeSubmit(values);
          if (!canSubmit) {
            return;
          }
        }
        if (options.onSubmitSuccess) {
          await options.onSubmitSuccess(values);
        }
      } catch (error) {
        if (options.onSubmitError) {
          options.onSubmitError(error);
        }
        throw error;
      }
    },
    reset: () => {
      form.resetFields();
      if (options.onReset) {
        options.onReset();
      }
    },
    setFieldValue: (name: string, value: any) => {
      form.setFieldValue(name, value);
    },
    getFieldValue: (name: string) => {
      return form.getFieldValue(name);
    },
    setFieldsValue: (values: Record<string, any>) => {
      form.setFieldsValue(values);
    },
    getFieldsValue: (nameList?: string[]) => {
      return nameList ? form.getFieldsValue(nameList) : form.getFieldsValue();
    },
    validateFields: (nameList?: string[]) => {
      return form.validateFields(nameList);
    },
    getForm: () => form,
  }));

  // 内部逻辑：渲染字段
  const renderField = (fieldConfig: FormFieldConfig) => {
    const {
      name,
      label,
      component: Component,
      componentProps = {},
      rules = [],
      required,
      requiredMessage,
      extra,
      tooltip,
      hidden,
      visible,
      dependencies = [],
      initialValue,
      render,
    } = fieldConfig;

    // 内部逻辑：检查是否隐藏
    if (hidden) {
      return null;
    }

    // 内部逻辑：检查条件渲染
    if (visible && !visible(form)) {
      return null;
    }

    // 内部逻辑：构建验证规则
    const fieldRules: Rule[] = [...rules];
    if (required) {
      fieldRules.unshift({
        required: true,
        message: requiredMessage || `请输入${label}`,
      });
    }

    // 内部逻辑：构建表单项属性
    const formItemProps: any = {
      name,
      label,
      rules: fieldRules,
      extra,
      initialValue,
      dependencies,
    };

    // 内部逻辑：处理自定义渲染
    if (render) {
      return (
        <Form.Item key={String(name)} {...formItemProps}>
          {render(fieldConfig, form)}
        </Form.Item>
      );
    }

    // 内部逻辑：默认渲染
    return (
      <Form.Item key={String(name)} {...formItemProps}>
        <Component {...componentProps} />
      </Form.Item>
    );
  };

  // 内部逻辑：渲染分组
  const renderGroup = (groupConfig: FormGroupConfig, groupIndex: number) => {
    const { title, fields, groupProps = {} } = groupConfig;

    return (
      <div key={`group-${groupIndex}`} className="form-group">
        {title && <h3 className="form-group-title">{title}</h3>}
        {fields.map(renderField)}
      </div>
    );
  };

  // 内部逻辑：合并字段和分组
  const nonGroupedFields = fields.filter(
    (field: FormFieldConfig) => !groups.some((g: FormGroupConfig) => g.fields.includes(field))
  );

  return (
    <Form
      ref={formRef}
      form={form}
      layout={options.layout || 'vertical'}
      labelCol={options.labelCol}
      wrapperCol={options.wrapperCol}
      initialValues={options.initialValues}
      onValuesChange={options.onValuesChange}
      onFinish={async (values) => {
        if (options.beforeSubmit) {
          const canSubmit = await options.beforeSubmit(values);
          if (!canSubmit) return;
        }
        if (options.onSubmitSuccess) {
          await options.onSubmitSuccess(values);
        }
      }}
      onFinishFailed={options.onSubmitError}
      {...restProps}
    >
      {groups.map((group: FormGroupConfig, index: number) => renderGroup(group, index))}
      {nonGroupedFields.map(renderField)}
    </Form>
  );
});

FormComposer.displayName = 'FormComposer';

/**
 * Hook：useFormComposer
 * 内部逻辑：简化 FormBuilder 的使用
 * 设计模式：工厂模式
 *
 * @example
 * ```typescript
 * const LoginForm = useFormComposer((builder) => builder
 *   .addField({ name: 'username', label: '用户名', component: Input })
 *   .addField({ name: 'password', label: '密码', component: Input.Password })
 *   .onSuccess(async (values) => await login(values))
 * );
 * ```
 */
export function useFormComposer(
  builderFn: (builder: FormBuilder) => FormBuilder
): React.ForwardRefExoticComponent<React.RefAttributes<FormComposerRef>> {
  const builder = new FormBuilder();
  return builderFn(builder).build();
}

/**
 * 组件：QuickForm 快速表单组件
 * 内部逻辑：提供简化的表单创建方式
 *
 * @example
 * ```typescript
 * <QuickForm
 *   fields={[
 *     { name: 'name', label: '姓名', component: Input, rules: [{ required: true }] },
 *     { name: 'email', label: '邮箱', component: Input }
 *   ]}
 *   onSubmit={async (values) => { await submit(values) }}
 * />
 * ```
 */
export const QuickForm = forwardRef<FormComposerRef, {
  fields: FormFieldConfig[];
  onSubmit: (values: any) => void | Promise<void>;
  formProps?: FormProps;
}>((props, ref) => {
  const { fields, onSubmit, formProps = {} } = props;

  const form = useMemo(
    () => new FormBuilder()
      .addFields(fields)
      .onSuccess(onSubmit)
      .build(),
    [fields, onSubmit]
  );

  return React.createElement(form, { ref, ...formProps });
});

QuickForm.displayName = 'QuickForm';

// 导出组件和工具（FormBuilder 已在上方声明为 export class，此处不再重复导出）
export default FormComposer;

/**
 * 样式：表单组合器样式
 * 注：将样式放在组件文件中便于维护
 */
export const formComposerStyles = `
.form-group {
  margin-bottom: 24px;
}

.form-group-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e8e8e8;
}
`;
