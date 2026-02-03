/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：表单建造者模式
 * 内部逻辑：使用建造者模式简化复杂表单的构建过程
 * 设计模式：建造者模式（Builder Pattern）、流式接口模式
 * 设计原则：SOLID - 开闭原则、单一职责原则
 *
 * 问题背景：
 *   - 复杂表单有大量字段配置
 *   - 表单验证规则重复
 *   - 表单初始化逻辑分散
 *
 * 解决方案：
 *   - 使用建造者模式流式构建表单配置
 *   - 统一管理验证规则
 *   - 提供表单字段工厂
 */

import { Rule } from 'antd/es/form';

/**
 * 类型：表单字段类型
 */
export type FieldType =
  | 'input'
  | 'textarea'
  | 'password'
  | 'number'
  | 'select'
  | 'multi-select'
  | 'switch'
  | 'radio'
  | 'checkbox'
  | 'date'
  | 'date-range'
  | 'time'
  | 'upload'
  | 'custom';

/**
 * 类型：表单字段配置
 */
export interface FormFieldConfig {
  /** 字段名称 */
  name: string;
  /** 字段标签 */
  label: string;
  /** 字段类型 */
  type: FieldType;
  /** 默认值 */
  defaultValue?: any;
  /** 是否必填 */
  required?: boolean;
  /** 验证规则 */
  rules?: Rule[];
  /** 占位符 */
  placeholder?: string;
  /** 选项（select、radio等使用） */
  options?: Array<{ label: string; value: any; disabled?: boolean }>;
  /** 是否禁用 */
  disabled?: boolean;
  /** 是否隐藏 */
  hidden?: boolean;
  /** 自定义渲染函数 */
  render?: (field: FormFieldConfig) => React.ReactNode;
  /** 字段间依赖 */
  dependencies?: string[];
  /** 字段变化时的回调 */
  onChange?: (value: any, allValues: any) => void;
  /** 额外属性 */
  extraProps?: Record<string, any>;
  /** 提示信息 */
  tooltip?: string;
  /** 帮助文本 */
  help?: string;
  /** 是否显示 */
  shouldUpdate?: boolean | ((prevValues: any, nextValues: any) => boolean);
}

/**
 * 类型：表单配置
 */
export interface FormConfig {
  /** 表单字段列表 */
  fields: FormFieldConfig[];
  /** 表单布局 */
  layout?: 'horizontal' | 'vertical' | 'inline';
  /** 标签宽度 */
  labelWidth?: number | string;
  /** 标签对齐方式 */
  labelAlign?: 'left' | 'right';
  /** 提交按钮文本 */
  submitText?: string;
  /** 是否显示重置按钮 */
  showReset?: boolean;
  /** 重置按钮文本 */
  resetText?: string;
  /** 是否显示取消按钮 */
  showCancel?: boolean;
  /** 取消按钮文本 */
  cancelText?: string;
  /** 提交前的回调 */
  beforeSubmit?: (values: any) => Promise<boolean> | boolean;
  /** 提交成功后的回调 */
  onSubmitSuccess?: (values: any, response: any) => void;
  /** 提交失败后的回调 */
  onSubmitError?: (error: any) => void;
  /** 取消按钮的回调 */
  onCancel?: () => void;
  /** 额外的表单属性 */
  extraProps?: Record<string, any>;
}

/**
 * 类：表单字段验证规则建造者
 * 设计模式：建造者模式
 * 职责：流式构建验证规则
 */
export class ValidationRuleBuilder {
  /** 内部变量：验证规则列表 */
  private rules: Rule[] = [];

  /**
   * 函数级注释：添加必填规则
   * 参数：message - 错误提示信息
   * 返回值：建造者自身（支持链式调用）
   */
  required(message: string = '此字段为必填项'): ValidationRuleBuilder {
    this.rules.push({ required: true, message });
    return this;
  }

  /**
   * 函数级注释：添加最小长度规则
   * 参数：min - 最小长度，message - 错误提示
   * 返回值：建造者自身
   */
  minLength(min: number, message?: string): ValidationRuleBuilder {
    this.rules.push({
      min,
      message: message || `最小长度为 ${min} 个字符`,
    });
    return this;
  }

  /**
   * 函数级注释：添加最大长度规则
   * 参数：max - 最大长度，message - 错误提示
   * 返回值：建造者自身
   */
  maxLength(max: number, message?: string): ValidationRuleBuilder {
    this.rules.push({
      max,
      message: message || `最大长度为 ${max} 个字符`,
    });
    return this;
  }

  /**
   * 函数级注释：添加长度范围规则
   * 参数：min - 最小长度，max - 最大长度，message - 错误提示
   * 返回值：建造者自身
   */
  lengthRange(min: number, max: number, message?: string): ValidationRuleBuilder {
    this.rules.push({
      min,
      max,
      message: message || `长度应在 ${min} 到 ${max} 之间`,
    });
    return this;
  }

  /**
   * 函数级注释：添加邮箱验证规则
   * 参数：message - 错误提示
   * 返回值：建造者自身
   */
  email(message: string = '请输入有效的邮箱地址'): ValidationRuleBuilder {
    this.rules.push({
      type: 'email' as any,
      message,
    });
    return this;
  }

  /**
   * 函数级注释：添加URL验证规则
   * 参数：message - 错误提示
   * 返回值：建造者自身
   */
  url(message: string = '请输入有效的URL'): ValidationRuleBuilder {
    this.rules.push({
      type: 'url' as any,
      message,
    });
    return this;
  }

  /**
   * 函数级注释：添加数字范围规则
   * 参数：min - 最小值，max - 最大值，message - 错误提示
   * 返回值：建造者自身
   */
  numberRange(min?: number, max?: number, message?: string): ValidationRuleBuilder {
    const rule: Rule = { type: 'number' as any };
    if (min !== undefined) rule.min = min;
    if (max !== undefined) rule.max = max;
    if (message) rule.message = message;
    this.rules.push(rule);
    return this;
  }

  /**
   * 函数级注释：添加正则表达式规则
   * 参数：pattern - 正则表达式，message - 错误提示
   * 返回值：建造者自身
   */
  pattern(regex: RegExp, message: string): ValidationRuleBuilder {
    this.rules.push({
      pattern: regex,
      message,
    });
    return this;
  }

  /**
   * 函数级注释：添加自定义验证规则
   * 参数：validator - 验证函数，message - 错误提示
   * 返回值：建造者自身
   */
  custom(
    validator: (rule: Rule, value: any) => Promise<void> | void,
    message?: string
  ): ValidationRuleBuilder {
    this.rules.push({
      validator,
      message,
    });
    return this;
  }

  /**
   * 函数级注释：添加白名单规则
   * 参数：list - 白名单，message - 错误提示
   * 返回值：建造者自身
   */
  whitelist(list: any[], message?: string): ValidationRuleBuilder {
    this.rules.push({
      validator: (_rule, value) => {
        if (value === undefined || value === null || value === '') {
          return Promise.resolve();
        }
        if (list.includes(value)) {
          return Promise.resolve();
        }
        return Promise.reject(new Error(message || `值必须在 ${list.join(', ')} 中`));
      },
    });
    return this;
  }

  /**
   * 函数级注释：构建并返回验证规则
   * 返回值：验证规则数组
   */
  build(): Rule[] {
    return [...this.rules];
  }

  /**
   * 函数级注释：静态方法：快速创建必填规则
   * 参数：message - 错误提示
   * 返回值：验证规则数组
   */
  static required(message?: string): Rule[] {
    return new ValidationRuleBuilder().required(message).build();
  }

  /**
   * 函数级注释：静态方法：快速创建邮箱规则
   * 参数：message - 错误提示
   * 返回值：验证规则数组
   */
  static email(message?: string): Rule[] {
    return new ValidationRuleBuilder().email(message).build();
  }
}

/**
 * 类：表单字段建造者
 * 设计模式：建造者模式
 * 职责：流式构建表单字段配置
 */
export class FormFieldBuilder {
  /** 内部变量：字段配置 */
  private config: Partial<FormFieldConfig> = {};

  /**
   * 函数级注释：设置字段名称
   * 参数：name - 字段名称
   * 返回值：建造者自身
   */
  name(name: string): FormFieldBuilder {
    this.config.name = name;
    return this;
  }

  /**
   * 函数级注释：设置字段标签
   * 参数：label - 字段标签
   * 返回值：建造者自身
   */
  label(label: string): FormFieldBuilder {
    this.config.label = label;
    return this;
  }

  /**
   * 函数级注释：设置字段类型
   * 参数：type - 字段类型
   * 返回值：建造者自身
   */
  type(type: FieldType): FormFieldBuilder {
    this.config.type = type;
    return this;
  }

  /**
   * 函数级注释：设置默认值
   * 参数：value - 默认值
   * 返回值：建造者自身
   */
  defaultValue(value: any): FormFieldBuilder {
    this.config.defaultValue = value;
    return this;
  }

  /**
   * 函数级注释：设置是否必填
   * 参数：required - 是否必填，message - 错误提示
   * 返回值：建造者自身
   */
  required(required: boolean = true, message?: string): FormFieldBuilder {
    this.config.required = required;
    if (required && !this.config.rules) {
      this.config.rules = ValidationRuleBuilder.required(message);
    }
    return this;
  }

  /**
   * 函数级注释：设置验证规则
   * 参数：rules - 验证规则或规则建造者
   * 返回值：建造者自身
   */
  rules(rules: Rule[] | ValidationRuleBuilder): FormFieldBuilder {
    this.config.rules = rules instanceof ValidationRuleBuilder ? rules.build() : rules;
    return this;
  }

  /**
   * 函数级注释：添加验证规则
   * 参数：ruleBuilder - 规则建造者
   * 返回值：建造者自身
   */
  addRules(ruleBuilder: ValidationRuleBuilder): FormFieldBuilder {
    if (!this.config.rules) {
      this.config.rules = [];
    }
    this.config.rules = [...this.config.rules, ...ruleBuilder.build()];
    return this;
  }

  /**
   * 函数级注释：设置占位符
   * 参数：text - 占位符文本
   * 返回值：建造者自身
   */
  placeholder(text: string): FormFieldBuilder {
    this.config.placeholder = text;
    return this;
  }

  /**
   * 函数级注释：设置选项（用于select等）
   * 参数：options - 选项列表
   * 返回值：建造者自身
   */
  options(options: Array<{ label: string; value: any; disabled?: boolean }>): FormFieldBuilder {
    this.config.options = options;
    return this;
  }

  /**
   * 函数级注释：设置是否禁用
   * 参数：disabled - 是否禁用
   * 返回值：建造者自身
   */
  disabled(disabled: boolean = true): FormFieldBuilder {
    this.config.disabled = disabled;
    return this;
  }

  /**
   * 函数级注释：设置是否隐藏
   * 参数：hidden - 是否隐藏
   * 返回值：建造者自身
   */
  hidden(hidden: boolean = true): FormFieldBuilder {
    this.config.hidden = hidden;
    return this;
  }

  /**
   * 函数级注释：设置自定义渲染函数
   * 参数：render - 渲染函数
   * 返回值：建造者自身
   */
  render(render: (field: FormFieldConfig) => React.ReactNode): FormFieldBuilder {
    this.config.render = render;
    return this;
  }

  /**
   * 函数级注释：设置字段依赖
   * 参数：dependencies - 依赖的字段名列表
   * 返回值：建造者自身
   */
  dependencies(dependencies: string[]): FormFieldBuilder {
    this.config.dependencies = dependencies;
    return this;
  }

  /**
   * 函数级注释：设置字段变化回调
   * 参数：onChange - 变化回调函数
   * 返回值：建造者自身
   */
  onChange(onChange: (value: any, allValues: any) => void): FormFieldBuilder {
    this.config.onChange = onChange;
    return this;
  }

  /**
   * 函数级注释：设置额外属性
   * 参数：props - 额外属性对象
   * 返回值：建造者自身
   */
  extraProps(props: Record<string, any>): FormFieldBuilder {
    this.config.extraProps = props;
    return this;
  }

  /**
   * 函数级注释：设置提示信息
   * 参数：tooltip - 提示文本
   * 返回值：建造者自身
   */
  tooltip(tooltip: string): FormFieldBuilder {
    this.config.tooltip = tooltip;
    return this;
  }

  /**
   * 函数级注释：设置帮助文本
   * 参数：help - 帮助文本
   * 返回值：建造者自身
   */
  help(help: string): FormFieldBuilder {
    this.config.help = help;
    return this;
  }

  /**
   * 函数级注释：构建并返回字段配置
   * 返回值：字段配置对象
   * 异常：Error - 当缺少必要属性时抛出
   */
  build(): FormFieldConfig {
    if (!this.config.name) {
      throw new Error('字段必须设置 name 属性');
    }
    if (!this.config.label) {
      throw new Error('字段必须设置 label 属性');
    }
    if (!this.config.type) {
      this.config.type = 'input';
    }

    return {
      name: this.config.name,
      label: this.config.label,
      type: this.config.type,
      defaultValue: this.config.defaultValue,
      required: this.config.required,
      rules: this.config.rules,
      placeholder: this.config.placeholder,
      options: this.config.options,
      disabled: this.config.disabled,
      hidden: this.config.hidden,
      render: this.config.render,
      dependencies: this.config.dependencies,
      onChange: this.config.onChange,
      extraProps: this.config.extraProps,
      tooltip: this.config.tooltip,
      help: this.config.help,
      shouldUpdate: this.config.shouldUpdate,
    };
  }
}

/**
 * 类：表单配置建造者
 * 设计模式：建造者模式
 * 职责：流式构建完整表单配置
 */
export class FormBuilder {
  /** 内部变量：表单配置 */
  private config: Partial<FormConfig> = {
    fields: [],
  };

  /**
   * 函数级注释：添加字段
   * 参数：field - 字段配置或字段建造者
   * 返回值：建造者自身
   */
  addField(field: FormFieldConfig | FormFieldBuilder): FormBuilder {
    const fieldConfig = field instanceof FormFieldBuilder ? field.build() : field;
    this.config.fields!.push(fieldConfig);
    return this;
  }

  /**
   * 函数级注释：批量添加字段
   * 参数：fields - 字段配置列表
   * 返回值：建造者自身
   */
  addFields(fields: Array<FormFieldConfig | FormFieldBuilder>): FormBuilder {
    fields.forEach(field => this.addField(field));
    return this;
  }

  /**
   * 函数级注释：设置表单布局
   * 参数：layout - 布局方式
   * 返回值：建造者自身
   */
  layout(layout: 'horizontal' | 'vertical' | 'inline'): FormBuilder {
    this.config.layout = layout;
    return this;
  }

  /**
   * 函数级注释：设置标签宽度
   * 参数：width - 标签宽度
   * 返回值：建造者自身
   */
  labelWidth(width: number | string): FormBuilder {
    this.config.labelWidth = width;
    return this;
  }

  /**
   * 函数级注释：设置标签对齐方式
   * 参数：align - 对齐方式
   * 返回值：建造者自身
   */
  labelAlign(align: 'left' | 'right'): FormBuilder {
    this.config.labelAlign = align;
    return this;
  }

  /**
   * 函数级注释：设置提交按钮文本
   * 参数：text - 按钮文本
   * 返回值：建造者自身
   */
  submitText(text: string): FormBuilder {
    this.config.submitText = text;
    return this;
  }

  /**
   * 函数级注释：显示重置按钮
   * 参数：show - 是否显示，text - 按钮文本
   * 返回值：建造者自身
   */
  showReset(show: boolean = true, text: string = '重置'): FormBuilder {
    this.config.showReset = show;
    this.config.resetText = text;
    return this;
  }

  /**
   * 函数级注释：显示取消按钮
   * 参数：show - 是否显示，text - 按钮文本
   * 返回值：建造者自身
   */
  showCancel(show: boolean = true, text: string = '取消'): FormBuilder {
    this.config.showCancel = show;
    this.config.cancelText = text;
    return this;
  }

  /**
   * 函数级注释：设置提交前回调
   * 参数：callback - 回调函数
   * 返回值：建造者自身
   */
  beforeSubmit(callback: (values: any) => Promise<boolean> | boolean): FormBuilder {
    this.config.beforeSubmit = callback;
    return this;
  }

  /**
   * 函数级注释：设置提交成功回调
   * 参数：callback - 回调函数
   * 返回值：建造者自身
   */
  onSuccess(callback: (values: any, response: any) => void): FormBuilder {
    this.config.onSubmitSuccess = callback;
    return this;
  }

  /**
   * 函数级注释：设置提交失败回调
   * 参数：callback - 回调函数
   * 返回值：建造者自身
   */
  onError(callback: (error: any) => void): FormBuilder {
    this.config.onSubmitError = callback;
    return this;
  }

  /**
   * 函数级注释：设置取消回调
   * 参数：callback - 回调函数
   * 返回值：建造者自身
   */
  onCancel(callback: () => void): FormBuilder {
    this.config.onCancel = callback;
    return this;
  }

  /**
   * 函数级注释：设置额外属性
   * 参数：props - 额外属性对象
   * 返回值：建造者自身
   */
  extraProps(props: Record<string, any>): FormBuilder {
    this.config.extraProps = props;
    return this;
  }

  /**
   * 函数级注释：构建并返回表单配置
   * 返回值：表单配置对象
   */
  build(): FormConfig {
    return {
      fields: this.config.fields || [],
      layout: this.config.layout,
      labelWidth: this.config.labelWidth,
      labelAlign: this.config.labelAlign,
      submitText: this.config.submitText,
      showReset: this.config.showReset,
      resetText: this.config.resetText,
      showCancel: this.config.showCancel,
      cancelText: this.config.cancelText,
      beforeSubmit: this.config.beforeSubmit,
      onSubmitSuccess: this.config.onSubmitSuccess,
      onSubmitError: this.config.onSubmitError,
      onCancel: this.config.onCancel,
      extraProps: this.config.extraProps,
    };
  }

  /**
   * 函数级注释：静态方法：快速创建文本输入字段
   * 参数：name - 字段名，label - 标签，options - 可选配置
   * 返回值：字段建造者
   */
  static input(
    name: string,
    label: string,
    options?: Partial<FormFieldConfig>
  ): FormFieldBuilder {
    const builder = new FormFieldBuilder()
      .name(name)
      .label(label)
      .type('input');

    if (options?.placeholder) builder.placeholder(options.placeholder);
    if (options?.required) builder.required(true);
    if (options?.rules) builder.rules(options.rules);
    if (options?.defaultValue !== undefined) builder.defaultValue(options.defaultValue);
    if (options?.disabled) builder.disabled(options.disabled);
    if (options?.tooltip) builder.tooltip(options.tooltip);
    if (options?.help) builder.help(options.help);

    return builder;
  }

  /**
   * 函数级注释：静态方法：快速创建选择字段
   * 参数：name - 字段名，label - 标签，options - 选项列表
   * 返回值：字段建造者
   */
  static select(
    name: string,
    label: string,
    options: Array<{ label: string; value: any }>
  ): FormFieldBuilder {
    return new FormFieldBuilder()
      .name(name)
      .label(label)
      .type('select')
      .options(options)
      .placeholder(`请选择${label}`);
  }

  /**
   * 函数级注释：静态方法：快速创建数字输入字段
   * 参数：name - 字段名，label - 标签，options - 可选配置
   * 返回值：字段建造者
   */
  static number(
    name: string,
    label: string,
    options?: Partial<FormFieldConfig>
  ): FormFieldBuilder {
    const builder = new FormFieldBuilder()
      .name(name)
      .label(label)
      .type('number');

    if (options?.placeholder) builder.placeholder(options.placeholder);
    if (options?.required) builder.required(true);
    if (options?.rules) builder.rules(options.rules);
    if (options?.defaultValue !== undefined) builder.defaultValue(options.defaultValue);
    if (options?.min !== undefined) {
      builder.addRules(new ValidationRuleBuilder().numberRange(options.min, options.max));
    }

    return builder;
  }
}

// FormFieldConfig, FormConfig, FieldType 已在上方声明为 export interface/export type，此处不再重复导出
