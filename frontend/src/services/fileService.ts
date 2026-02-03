/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：文件处理服务
 * 内部逻辑：提供统一的文件验证、处理和上传功能
 * 设计模式：策略模式、工厂模式、单例模式
 * 设计原则：单一职责原则、开闭原则
 */

/**
 * 文件类型配置接口
 */
interface FileTypeConfig {
  /** 文件扩展名列表 */
  extensions: string[];
  /** MIME 类型列表 */
  mimeTypes: string[];
  /** 最大文件大小（字节） */
  maxSize: number;
  /** 是否允许上传 */
  allowUpload: boolean;
}

/**
 * 文件验证结果接口
 */
interface ValidationResult {
  /** 是否通过验证 */
  valid: boolean;
  /** 错误消息 */
  error?: string;
  /** 错误代码 */
  errorCode?: 'SIZE_LIMIT' | 'TYPE_NOT_ALLOWED' | 'EMPTY_FILE';
}

/**
 * 文件处理策略接口
 */
interface FileProcessingStrategy {
  /** 策略名称 */
  name: string;
  /** 验证文件 */
  validate(file: File): ValidationResult;
  /** 处理文件（可选） */
  process?(file: File): Promise<File | Blob>;
}

/**
 * 文件类型配置管理器
 * 设计模式：单例模式
 */
class FileTypeConfigManager {
  /** 内部变量：单例实例 */
  private static instance: FileTypeConfigManager;

  /** 内部变量：文件类型配置映射 */
  private configs: Map<string, FileTypeConfig> = new Map();

  /** 私有构造函数 */
  private constructor() {
    this._initializeDefaultConfigs();
  }

  /**
   * 函数级注释：获取单例实例
   */
  static getInstance(): FileTypeConfigManager {
    if (!FileTypeConfigManager.instance) {
      FileTypeConfigManager.instance = new FileTypeConfigManager();
    }
    return FileTypeConfigManager.instance;
  }

  /**
   * 函数级注释：初始化默认文件类型配置
   */
  private _initializeDefaultConfigs(): void {
    // PDF 配置
    this.registerConfig('pdf', {
      extensions: ['.pdf'],
      mimeTypes: ['application/pdf'],
      maxSize: 50 * 1024 * 1024, // 50MB
      allowUpload: true,
    });

    // Word 配置
    this.registerConfig('docx', {
      extensions: ['.docx', '.doc'],
      mimeTypes: [
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
      ],
      maxSize: 20 * 1024 * 1024, // 20MB
      allowUpload: true,
    });

    // Markdown 配置
    this.registerConfig('md', {
      extensions: ['.md'],
      mimeTypes: ['text/markdown', 'text/plain'],
      maxSize: 5 * 1024 * 1024, // 5MB
      allowUpload: true,
    });

    // TXT 配置
    this.registerConfig('txt', {
      extensions: ['.txt'],
      mimeTypes: ['text/plain'],
      maxSize: 5 * 1024 * 1024, // 5MB
      allowUpload: true,
    });

    // Excel 配置
    this.registerConfig('xlsx', {
      extensions: ['.xlsx', '.xls'],
      mimeTypes: [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
      ],
      maxSize: 20 * 1024 * 1024, // 20MB
      allowUpload: true,
    });

    // PPT 配置
    this.registerConfig('pptx', {
      extensions: ['.pptx', '.ppt'],
      mimeTypes: [
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.ms-powerpoint',
      ],
      maxSize: 30 * 1024 * 1024, // 30MB
      allowUpload: true,
    });
  }

  /**
   * 函数级注释：注册文件类型配置
   * 参数：
   *   type - 文件类型标识
   *   config - 配置对象
   */
  registerConfig(type: string, config: FileTypeConfig): void {
    this.configs.set(type.toLowerCase(), config);
  }

  /**
   * 函数级注释：获取文件类型配置
   * 参数：
   *   type - 文件类型标识
   * 返回值：配置对象，未找到返回 undefined
   */
  getConfig(type: string): FileTypeConfig | undefined {
    return this.configs.get(type.toLowerCase());
  }

  /**
   * 函数级注释：根据文件扩展名获取配置
   * 参数：
   *   filename - 文件名
   * 返回值：配置对象，未找到返回 undefined
   */
  getConfigByFilename(filename: string): FileTypeConfig | undefined {
    const ext = this._getExtension(filename);
    for (const [, config] of this.configs) {
      if (config.extensions.includes(ext)) {
        return config;
      }
    }
    return undefined;
  }

  /**
   * 函数级注释：获取文件扩展名
   */
  private _getExtension(filename: string): string {
    const idx = filename.lastIndexOf('.');
    return idx >= 0 ? filename.slice(idx).toLowerCase() : '';
  }

  /**
   * 函数级注释：获取所有允许的文件扩展名
   * 返回值：扩展名字符串
   */
  getAllowedExtensions(): string {
    const extensions: string[] = [];
    for (const [, config] of this.configs) {
      if (config.allowUpload) {
        extensions.push(...config.extensions);
      }
    }
    return extensions.join(',');
  }
}

/**
 * 默认文件处理策略
 * 设计模式：策略模式
 */
class DefaultFileProcessingStrategy implements FileProcessingStrategy {
  name = 'default';

  validate(file: File): ValidationResult {
    // 内部逻辑：检查文件是否为空
    if (file.size === 0) {
      return {
        valid: false,
        error: '文件不能为空',
        errorCode: 'EMPTY_FILE',
      };
    }

    // 内部逻辑：获取文件类型配置
    const manager = FileTypeConfigManager.getInstance();
    const config = manager.getConfigByFilename(file.name);

    if (!config) {
      return {
        valid: false,
        error: '不支持的文件类型',
        errorCode: 'TYPE_NOT_ALLOWED',
      };
    }

    // 内部逻辑：检查是否允许上传
    if (!config.allowUpload) {
      return {
        valid: false,
        error: '该文件类型不允许上传',
        errorCode: 'TYPE_NOT_ALLOWED',
      };
    }

    // 内部逻辑：检查文件大小
    if (file.size > config.maxSize) {
      const maxSizeMB = (config.maxSize / (1024 * 1024)).toFixed(0);
      return {
        valid: false,
        error: `文件大小超过限制（最大 ${maxSizeMB}MB）`,
        errorCode: 'SIZE_LIMIT',
      };
    }

    return { valid: true };
  }
}

/**
 * 文件服务类
 * 设计模式：门面模式
 * 职责：提供统一的文件处理接口
 */
export class FileService {
  /** 内部变量：处理策略 */
  private strategy: FileProcessingStrategy;

  /** 内部变量：配置管理器 */
  private configManager: FileTypeConfigManager;

  constructor(strategy?: FileProcessingStrategy) {
    this.strategy = strategy || new DefaultFileProcessingStrategy();
    this.configManager = FileTypeConfigManager.getInstance();
  }

  /**
   * 函数级注释：验证文件
   * 参数：
   *   file - 要验证的文件
   * 返回值：验证结果
   */
  validateFile(file: File): ValidationResult {
    return this.strategy.validate(file);
  }

  /**
   * 函数级注释：验证多个文件
   * 参数：
   *   files - 文件列表
   * 返回值：验证结果数组
   */
  validateFiles(files: File[]): ValidationResult[] {
    return files.map(file => this.validateFile(file));
  }

  /**
   * 函数级注释：处理文件
   * 参数：
   *   file - 要处理的文件
   * 返回值：处理后的文件
   */
  async processFile(file: File): Promise<File | Blob> {
    if (this.strategy.process) {
      return this.strategy.process(file);
    }
    return file;
  }

  /**
   * 函数级注释：设置处理策略
   * 参数：
   *   strategy - 新的处理策略
   */
  setStrategy(strategy: FileProcessingStrategy): void {
    this.strategy = strategy;
  }

  /**
   * 函数级注释：获取允许的文件扩展名
   * 返回值：扩展名字符串，如 ".pdf,.docx,.txt"
   */
  getAllowedExtensions(): string {
    return this.configManager.getAllowedExtensions();
  }

  /**
   * 函数级注释：格式化文件大小显示
   * 参数：
   *   bytes - 字节数
   * 返回值：格式化后的字符串，如 "5.2 MB"
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  }
}

// 导出单例实例
export const fileService = new FileService();

// 导出便捷函数
export const validateFile = (file: File) => fileService.validateFile(file);
export const getAllowedExtensions = () => fileService.getAllowedExtensions();
export const formatFileSize = (bytes: number) => fileService.formatFileSize(bytes);
