/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：模型配置管理页面组件
 * 内部逻辑：提供LLM和Embedding模型配置的可视化管理界面
 * 功能：
 *   1. 配置列表展示
 *   2. 添加/编辑配置对话框
 *   3. 设置默认模型（热切换）
 *   4. Ollama模型管理
 * 参考项目：easy-dataset-file
 */

import { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  message,
  Space,
  Tag,
  Popconfirm,
  Tabs,
  Dropdown,
  Switch
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  CheckOutlined,
  ReloadOutlined,
  DownloadOutlined,
  DeleteOutlined,
  ApiOutlined,
  KeyOutlined
} from '@ant-design/icons';
import { modelConfigService } from '../../../services/modelConfigServiceClass';
import type {
  ModelConfig,
  ModelConfigSafe,
  ProviderInfo,
  OllamaModelInfo,
  EmbeddingConfig,
  EmbeddingConfigSafe,
  ConnectionTestResponse,
  EmbeddingConnectionTestResponse,
  LocalModelsResponse,
} from '../../../types/modelConfig';
import './index.css';

/**
 * 模型配置管理页面组件
 */
export const ModelConfigPage = () => {
  // 内部变量：表单实例
  const [llmForm] = Form.useForm<ModelConfig>();
  const [embeddingForm] = Form.useForm();

  // 内部变量：监听表单字段变化（必须在组件顶层调用 hooks）
  const llmProviderId = Form.useWatch('provider_id', llmForm);
  const embeddingProviderId = Form.useWatch('provider_id', embeddingForm);

  // 内部变量：状态管理
  const [loading, setLoading] = useState(false);
  const [llmConfigs, setLLMConfigs] = useState<ModelConfig[]>([]);
  const [embeddingConfigs, setEmbeddingConfigs] = useState<any[]>([]);
  const [providers, setProviders] = useState<{
    llm_providers: ProviderInfo[];
    embedding_providers: ProviderInfo[];
  } | null>(null);
  const [ollamaModels, setOllamaModels] = useState<OllamaModelInfo[]>([]);

  // 内部变量：弹窗状态
  const [llmModalVisible, setLLMModalVisible] = useState(false);
  const [embeddingModalVisible, setEmbeddingModalVisible] = useState(false);
  const [editingLLM, setEditingLLM] = useState<ModelConfig | null>(null);
  const [editingEmbedding, setEditingEmbedding] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('llm');

  // 内部变量：修改密钥 Modal 状态
  const [keyUpdateModalVisible, setKeyUpdateModalVisible] = useState(false);
  const [keyUpdateType, setKeyUpdateType] = useState<'llm' | 'embedding'>('llm');
  const [keyUpdateConfig, setKeyUpdateConfig] = useState<ModelConfigSafe | EmbeddingConfigSafe | null>(null);
  const [keyForm] = Form.useForm<{ api_key: string }>();

  // 内部变量：测试连接相关状态
  const [testingLLMId, setTestingLLMId] = useState<string | null>(null);
  const [testingEmbeddingId, setTestingEmbeddingId] = useState<string | null>(null);
  const [testingInModal, setTestingInModal] = useState(false);

  // 内部变量：动态获取的模型列表（测试连接成功后更新）
  const [dynamicLLMModels, setDynamicLLMModels] = useState<Record<string, string[]>>({});
  const [dynamicEmbeddingModels, setDynamicEmbeddingModels] = useState<Record<string, string[]>>({});

  // 内部变量：本地扫描的Embedding模型列表
  const [localModels, setLocalModels] = useState<string[]>([]);

  /**
   * 函数级注释：加载所有配置数据
   */
  const loadAllData = async () => {
    setLoading(true);
    try {
      const [llmData, providersData, embeddingData] = await Promise.all([
        modelConfigService.llm.getConfigs(),
        modelConfigService.helper.getProviders(),
        modelConfigService.embedding.getConfigs()
      ]);
      setLLMConfigs(llmData.configs);
      setProviders(providersData);
      setEmbeddingConfigs(embeddingData.configs);
    } catch (error) {
      message.error('加载配置失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 函数级注释：刷新Ollama模型列表
   * 参数：
   *   showMessage: 是否显示成功提示消息（默认true，自动加载时为false）
   */
  const refreshOllamaModels = async (showMessage: boolean = true) => {
    try {
      const data = await modelConfigService.helper.getOllamaModels();
      setOllamaModels(data.models || []);
      // 内部逻辑：仅在手动刷新时显示成功消息
      if (showMessage) {
        message.success(`已刷新，找到 ${data.models?.length || 0} 个模型`);
      }
    } catch (error: any) {
      // 内部逻辑：仅在手动刷新时显示错误消息
      if (showMessage) {
        message.error(error.response?.data?.detail || '无法连接Ollama服务');
      }
    }
  };

  /**
   * 函数级注释：拉取新模型
   */
  const handlePullModel = async () => {
    const modelName = await prompt('请输入模型名称（如 llama3:8b）');
    if (!modelName) return;

    const loadingMsg = message.loading('正在拉取模型，请稍候...', 0);

    try {
      await modelConfigService.helper.pullOllamaModel(modelName);
      message.success(`模型 ${modelName} 拉取成功`);
      refreshOllamaModels();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '拉取模型失败');
    } finally {
      loadingMsg();
    }
  };

  /**
   * 函数级注释：启用LLM配置
   */
  const handleSetDefaultLLM = async (configId: string) => {
    try {
      await modelConfigService.llm.setDefault(configId);
      message.success('配置已启用并生效');
      loadAllData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '设置失败');
    }
  };

  /**
   * 函数级注释：删除LLM配置
   */
  const handleDeleteLLM = async (configId: string) => {
    try {
      await modelConfigService.llm.deleteConfig(configId);
      message.success('配置已删除');
      loadAllData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  /**
   * 函数级注释：保存LLM配置
   */
  const handleSaveLLM = async () => {
    try {
      const values = await llmForm.validateFields();
      await modelConfigService.llm.saveConfig(values);
      message.success('配置已保存');
      setLLMModalVisible(false);
      loadAllData();
    } catch (error: any) {
      if (error.errorFields) {
        message.error('请检查必填字段');
      } else {
        message.error(error.response?.data?.detail || '保存失败');
      }
    }
  };

  /**
   * 函数级注释：编辑LLM配置
   * 内部逻辑：编辑时不回填api_key字段，避免暴露完整密钥
   */
  const handleEditLLM = (config: ModelConfig | ModelConfigSafe) => {
    setEditingLLM(config as ModelConfig);
    // 内部逻辑：复制配置但清空 api_key（如果是安全响应类型则使用 api_key_masked 显示）
    const { api_key, api_key_masked, ...configWithoutKey } = config as any;
    llmForm.setFieldsValue({
      ...configWithoutKey,
      // 内部逻辑：api_key 留空，用户需要通过"修改密钥"功能单独更新
      api_key: ''
    });
    setLLMModalVisible(true);
  };

  /**
   * 函数级注释：新增LLM配置
   */
  const handleAddLLM = () => {
    setEditingLLM(null);
    llmForm.resetFields();
    // 设置默认值（新增配置默认禁用，需手动启用）
    llmForm.setFieldsValue({
      type: 'text',
      temperature: 0.7,
      max_tokens: 8192,
      top_p: 0.9,
      top_k: 0,
      device: 'auto',  // 默认自动检测设备
      status: 0
    });
    setLLMModalVisible(true);
  };

  /**
   * 函数级注释：获取模型选项列表
   */
  const getModelOptions = (providerId: string) => {
    // 内部逻辑：优先使用动态获取的模型列表（测试连接成功后）
    if (providerId && dynamicLLMModels[providerId]) {
      return dynamicLLMModels[providerId].map((m: string) => ({ label: m, value: m }));
    }
    // 内部逻辑：否则使用默认模型列表
    if (!providers) return [];
    const provider = providers.llm_providers?.find(p => p.value === providerId);
    return provider?.default_models.map((m: string) => ({ label: m, value: m })) || [];
  };

  /**
   * 函数级注释：保存 Embedding 配置
   */
  const handleSaveEmbedding = async () => {
    try {
      const values = await embeddingForm.validateFields();
      await modelConfigService.embedding.saveConfig(values);
      message.success('Embedding 配置已保存');
      setEmbeddingModalVisible(false);
      loadAllData();
    } catch (error: any) {
      if (error.errorFields) {
        message.error('请检查必填字段');
      } else {
        message.error(error.response?.data?.detail || '保存失败');
      }
    }
  };

  /**
   * 函数级注释：编辑 Embedding 配置
   * 内部逻辑：编辑时不回填api_key字段，避免暴露完整密钥
   */
  const handleEditEmbedding = (config: EmbeddingConfig | EmbeddingConfigSafe) => {
    setEditingEmbedding(config);
    // 内部逻辑：复制配置但清空 api_key
    const { api_key, api_key_masked, ...configWithoutKey } = config as any;
    embeddingForm.setFieldsValue({
      ...configWithoutKey,
      // 内部逻辑：api_key 留空，用户需要通过"修改密钥"功能单独更新
      api_key: ''
    });
    setEmbeddingModalVisible(true);
  };

  /**
   * 函数级注释：新增 Embedding 配置
   */
  const handleAddEmbedding = () => {
    setEditingEmbedding(null);
    embeddingForm.resetFields();
    embeddingForm.setFieldsValue({
      device: 'auto',
      status: 1
    });
    setEmbeddingModalVisible(true);
  };

  /**
   * 函数级注释：启用 Embedding 配置
   */
  const handleSetDefaultEmbedding = async (configId: string) => {
    try {
      await modelConfigService.embedding.setDefault(configId);
      message.success('Embedding配置已启用并生效');
      loadAllData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '设置失败');
    }
  };

  /**
   * 函数级注释：删除 Embedding 配置
   */
  const handleDeleteEmbedding = async (configId: string) => {
    try {
      await modelConfigService.embedding.deleteConfig(configId);
      message.success('Embedding 配置已删除');
      loadAllData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  /**
   * 函数级注释：打开修改LLM API密钥对话框
   * 内部逻辑：设置当前配置并显示对话框，清空表单
   */
  const handleUpdateLLMKey = (config: ModelConfigSafe) => {
    setKeyUpdateType('llm');
    setKeyUpdateConfig(config);
    keyForm.setFieldsValue({ api_key: '' });
    setKeyUpdateModalVisible(true);
  };

  /**
   * 函数级注释：打开修改Embedding API密钥对话框
   * 内部逻辑：设置当前配置并显示对话框，清空表单
   */
  const handleUpdateEmbeddingKey = (config: EmbeddingConfigSafe) => {
    setKeyUpdateType('embedding');
    setKeyUpdateConfig(config);
    keyForm.setFieldsValue({ api_key: '' });
    setKeyUpdateModalVisible(true);
  };

  /**
   * 函数级注释：提交API密钥更新
   * 内部逻辑：调用专门的更新接口，成功后刷新列表并关闭对话框
   */
  const handleKeyUpdateSubmit = async () => {
    try {
      const values = await keyForm.validateFields();

      if (keyUpdateType === 'llm') {
        await modelConfigService.llm.updateAPIKey(keyUpdateConfig!.id!, values.api_key);
        message.success('API密钥已更新');
      } else {
        await modelConfigService.embedding.updateAPIKey(keyUpdateConfig!.id!, values.api_key);
        message.success('API密钥已更新');
      }

      setKeyUpdateModalVisible(false);
      loadAllData();
    } catch (error: any) {
      if (error.errorFields) {
        message.error('请输入API密钥');
      } else {
        message.error(error.response?.data?.detail || '更新失败');
      }
    }
  };

  /**
   * 函数级注释：获取 Embedding 模型选项列表
   */
  const getEmbeddingModelOptions = (providerId: string) => {
    // 内部逻辑：对于local提供商，优先使用扫描的本地模型列表
    if (providerId === 'local') {
      if (localModels.length > 0) {
        return localModels.map((m: string) => ({ label: m, value: m }));
      }
    }

    // 内部逻辑：优先使用动态获取的模型列表（测试连接成功后）
    if (providerId && dynamicEmbeddingModels[providerId]) {
      return dynamicEmbeddingModels[providerId].map((m: string) => ({ label: m, value: m }));
    }
    // 内部逻辑：否则使用默认模型列表
    if (!providers) return [];
    const provider = providers.embedding_providers?.find(p => p.value === providerId);
    return provider?.default_models.map((m: string) => ({ label: m, value: m })) || [];
  };

  /**
   * 函数级注释：在Modal中测试连接（使用当前表单值）
   */
  const handleTestInModal = async (isLLM: boolean = true) => {
    const form = isLLM ? llmForm : embeddingForm;

    try {
      const values = await form.validateFields();
      const providerId = values.provider_id;

      if (!providerId) {
        message.warning('请先选择提供商');
        return;
      }

      // 显示测试中状态
      setTestingInModal(true);
      const hide = message.loading('正在测试连接...', 0);

      try {
        if (isLLM) {
          const result = await modelConfigService.llm.testConnection({
            provider_id: providerId,
            endpoint: values.endpoint || '',
            api_key: values.api_key || '',
            model_name: values.model_name || ''
          });

          hide();

          if (result.success) {
            message.success(`连接成功! ${result.message} (耗时: ${result.latency_ms}ms)`);
            // 内部逻辑：测试成功后，更新动态模型列表
            if (result.models && result.models.length > 0) {
              setDynamicLLMModels(prev => ({
                ...prev,
                [providerId]: result.models!
              }));
              // 内部逻辑：如果当前选择的模型不在新列表中，选择第一个模型
              if (!result.models.includes(values.model_name)) {
                llmForm.setFieldValue('model_name', result.models[0]);
              }
            }
          } else {
            message.error(`连接失败: ${result.error || '未知错误'}`);
          }
        } else {
          const result = await modelConfigService.embedding.testConnection({
            provider_id: providerId,
            endpoint: values.endpoint || '',
            api_key: values.api_key || '',
            model_name: values.model_name || '',
            device: values.device || 'cpu'
          });

          hide();

          if (result.success) {
            message.success(`连接成功! ${result.message} (耗时: ${result.latency_ms}ms)`);
            // 内部逻辑：测试成功后，更新动态模型列表
            if (result.models && result.models.length > 0) {
              setDynamicEmbeddingModels(prev => ({
                ...prev,
                [providerId]: result.models!
              }));
              // 内部逻辑：如果当前选择的模型不在新列表中，选择第一个模型
              if (!result.models.includes(values.model_name)) {
                embeddingForm.setFieldValue('model_name', result.models[0]);
              }
            }
          } else {
            message.error(`连接失败: ${result.error || '未知错误'}`);
          }
        }
      } catch (error: any) {
        hide();
        throw error;
      }
    } catch (error: any) {
      if (error.errorFields) {
        message.warning('请先填写必填字段');
      } else {
        message.error(error.response?.data?.detail || '测试连接失败');
      }
    } finally {
      setTestingInModal(false);
    }
  };

  /**
   * 函数级注释：测试LLM配置连接（从表格操作）
   * 内部逻辑：
   *   1. 对于已保存配置（有id），传递 config_id 让后端从数据库获取真实密钥
   *   2. 对于新增配置（在Modal中），直接使用表单的 api_key
   */
  const handleTestLLM = async (config: ModelConfig | ModelConfigSafe) => {
    const configId = config.id!;
    setTestingLLMId(configId);

    try {
      // 内部逻辑：判断是否有真实 api_key（ModelConfig类型有api_key，ModelConfigSafe只有api_key_masked）
      const hasRealApiKey = 'api_key' in config && !!(config as ModelConfig).api_key;

      const result = await modelConfigService.llm.testConnection({
        provider_id: config.provider_id,
        endpoint: config.endpoint,
        api_key: hasRealApiKey ? (config as ModelConfig).api_key : '',  // 已保存配置留空
        model_name: config.model_name,
        config_id: hasRealApiKey ? undefined : configId  // 已保存配置传递config_id
      });

      if (result.success) {
        message.success(`${result.message} (耗时: ${result.latency_ms}ms)`);
      } else {
        message.error(`连接失败: ${result.error || '未知错误'}`);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '测试连接失败');
    } finally {
      setTestingLLMId(null);
    }
  };

  /**
   * 函数级注释：测试Embedding配置连接（从表格操作）
   * 内部逻辑：
   *   1. 对于已保存配置（有id），传递 config_id 让后端从数据库获取真实密钥
   *   2. 对于新增配置（在Modal中），直接使用表单的 api_key
   */
  const handleTestEmbedding = async (config: EmbeddingConfig | EmbeddingConfigSafe) => {
    const configId = config.id!;
    setTestingEmbeddingId(configId);

    try {
      // 内部逻辑：判断是否有真实 api_key（EmbeddingConfig类型有api_key，EmbeddingConfigSafe只有api_key_masked）
      const hasRealApiKey = 'api_key' in config && !!(config as EmbeddingConfig).api_key;

      const result = await modelConfigService.embedding.testConnection({
        provider_id: config.provider_id,
        endpoint: config.endpoint,
        api_key: hasRealApiKey ? (config as EmbeddingConfig).api_key : '',  // 已保存配置留空
        model_name: config.model_name,
        device: config.device,
        config_id: hasRealApiKey ? undefined : configId  // 已保存配置传递config_id
      });

      if (result.success) {
        message.success(`${result.message} (耗时: ${result.latency_ms}ms)`);
      } else {
        message.error(`连接失败: ${result.error || '未知错误'}`);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '测试连接失败');
    } finally {
      setTestingEmbeddingId(null);
    }
  };

  // 内部逻辑：组件挂载时加载数据
  useEffect(() => {
    loadAllData();
    refreshOllamaModels(false);  // 内部逻辑：自动加载时不显示提示消息
  }, []);

  /**
   * 函数级注释：监听Embedding提供商变化，自动加载本地模型列表
   */
  useEffect(() => {
    // 内部逻辑：当选择local提供商时，自动扫描本地模型
    if (embeddingProviderId === 'local') {
      const loadLocalModels = async () => {
        try {
          const data = await modelConfigService.helper.getLocalModels();
          setLocalModels(data.models || []);
          if (data.models && data.models.length > 0) {
            message.success(`已扫描本地模型目录，发现 ${data.models.length} 个模型`);
          }
        } catch (error: any) {
          // 内部逻辑：静默失败，不影响用户操作
          console.warn('获取本地模型列表失败:', error);
        }
      };
      loadLocalModels();
    }
  }, [embeddingProviderId]);

  /**
   * 函数级注释：LLM配置表格列定义
   */
  const llmColumns = [
    {
      title: '提供商',
      dataIndex: 'provider_name',
      key: 'provider',
      render: (text: string, record: ModelConfig) => (
        <Space>
          {text}
          {record.status === 1 && <Tag color="green">使用中</Tag>}
        </Space>
      )
    },
    { title: '模型', dataIndex: 'model_name', key: 'model_name' },
    {
      title: '端点',
      dataIndex: 'endpoint',
      key: 'endpoint',
      ellipsis: true
    },
    {
      title: '设备',
      dataIndex: 'device',
      key: 'device',
      render: (device: string | undefined, record: ModelConfig) => {
        // 只有本地提供商才显示设备配置
        const isLocalProvider = record.provider_id === 'ollama';
        if (isLocalProvider) {
          return <Tag>{device?.toUpperCase() || 'Auto'}</Tag>;
        }
        return <span style={{ color: '#999' }}>-</span>;
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: number) => (
        <Tag color={status === 1 ? 'green' : 'default'}>
          {status === 1 ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 350,
      render: (_: any, record: ModelConfig | ModelConfigSafe) => (
        <Space>
          {/* 测试按钮 */}
          <Button
            size="small"
            icon={testingLLMId === record.id ? <ReloadOutlined spin /> : <ApiOutlined />}
            onClick={() => handleTestLLM(record as ModelConfig)}
            loading={testingLLMId === record.id}
          >
            测试
          </Button>
          {record.status !== 1 && (
            <Button
              size="small"
              icon={<CheckOutlined />}
              onClick={() => handleSetDefaultLLM(record.id!)}
            >
              启用
            </Button>
          )}
          <Button
            size="small"
            icon={<KeyOutlined />}
            onClick={() => handleUpdateLLMKey(record as ModelConfigSafe)}
          >
            修改密钥
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditLLM(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除此配置？"
            onConfirm={() => handleDeleteLLM(record.id!)}
            okText="确认"
            cancelText="取消"
            okButtonProps={{
              danger: true,
              style: {
                background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                border: 'none',
                color: '#fff',
              },
            }}
            cancelButtonProps={{
              style: {
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#f1f5f9',
              },
            }}
          >
            <Button size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  /**
   * 函数级注释：Embedding 配置表格列定义
   */
  const embeddingColumns = [
    {
      title: '提供商',
      dataIndex: 'provider_name',
      key: 'provider',
      render: (text: string, record: EmbeddingConfig) => (
        <Space>
          {text}
          {record.status === 1 && <Tag color="green">使用中</Tag>}
        </Space>
      )
    },
    { title: '模型', dataIndex: 'model_name', key: 'model_name' },
    {
      title: '端点',
      dataIndex: 'endpoint',
      key: 'endpoint',
      ellipsis: true
    },
    {
      title: '设备',
      dataIndex: 'device',
      key: 'device',
      render: (device: string, record: EmbeddingConfig) => {
        // 只有本地提供商才显示设备配置
        const isLocalProvider = record.provider_id === 'ollama' || record.provider_id === 'local';
        if (isLocalProvider) {
          return <Tag>{device?.toUpperCase() || 'Auto'}</Tag>;
        }
        return <span style={{ color: '#999' }}>-</span>;
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: number) => (
        <Tag color={status === 1 ? 'green' : 'default'}>
          {status === 1 ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 350,
      render: (_: any, record: EmbeddingConfig | EmbeddingConfigSafe) => (
        <Space>
          {/* 测试按钮 */}
          <Button
            size="small"
            icon={testingEmbeddingId === record.id ? <ReloadOutlined spin /> : <ApiOutlined />}
            onClick={() => handleTestEmbedding(record as EmbeddingConfig)}
            loading={testingEmbeddingId === record.id}
          >
            测试
          </Button>
          {record.status !== 1 && (
            <Button
              size="small"
              icon={<CheckOutlined />}
              onClick={() => handleSetDefaultEmbedding(record.id!)}
            >
              启用
            </Button>
          )}
          <Button
            size="small"
            icon={<KeyOutlined />}
            onClick={() => handleUpdateEmbeddingKey(record as EmbeddingConfigSafe)}
          >
            修改密钥
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditEmbedding(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除此配置？"
            onConfirm={() => handleDeleteEmbedding(record.id!)}
            okText="确认"
            cancelText="取消"
            okButtonProps={{
              danger: true,
              style: {
                background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                border: 'none',
                color: '#fff',
              },
            }}
            cancelButtonProps={{
              style: {
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#f1f5f9',
              },
            }}
          >
            <Button size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  /**
   * 函数级注释：LLM配置表单
   */
  const renderLLMModal = () => (
    <Modal
      title={editingLLM ? '编辑LLM配置' : '添加LLM配置'}
      open={llmModalVisible}
      onOk={handleSaveLLM}
      okText="确定"
      cancelText="取消"
      okButtonProps={{
        style: {
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          border: 'none',
          color: '#fff',
        },
      }}
      cancelButtonProps={{
        style: {
          background: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          color: '#f1f5f9',
        },
      }}
      onCancel={() => setLLMModalVisible(false)}
      width={600}
      destroyOnClose
      footer={(_, { OkBtn, CancelBtn }) => (
        <>
          <CancelBtn />
          <Button
            icon={<ApiOutlined />}
            onClick={() => handleTestInModal(true)}
            loading={testingInModal}
          >
            测试连接
          </Button>
          <OkBtn />
        </>
      )}
    >
      <Form form={llmForm} layout="vertical">
        <Form.Item
          label="提供商"
          name="provider_id"
          rules={[{ required: true, message: '请选择提供商' }]}
        >
          <Select
            options={providers?.llm_providers?.map((p: ProviderInfo) => ({
              label: p.label,
              value: p.value
            }))}
            onChange={(value) => {
              const provider = providers?.llm_providers?.find((p: ProviderInfo) => p.value === value);
              if (provider) {
                llmForm.setFieldsValue({
                  provider_name: provider.label,
                  endpoint: provider.default_endpoint,
                  model_id: provider.default_models[0] || '',
                  model_name: provider.default_models[0] || ''
                });
              }
            }}
          />
        </Form.Item>

        <Form.Item label="端点" name="endpoint" rules={[{ required: true }]}>
          <Input placeholder="https://api.openai.com/v1/" />
        </Form.Item>

        <Form.Item
          label="API密钥"
          name="api_key"
          tooltip={editingLLM ? "编辑时不显示密钥，请使用'修改密钥'功能单独更新" : "云端供应商需要配置"}
        >
          <Input.Password
            placeholder={editingLLM ? "编辑时请留空，使用'修改密钥'功能单独更新" : "云端供应商需要配置"}
            disabled={!!editingLLM}
          />
        </Form.Item>

        <Form.Item
          label="模型"
          name="model_name"
          rules={[{ required: true, message: '请选择模型' }]}
        >
          <Select
            showSearch
            options={llmProviderId ? getModelOptions(llmProviderId) : []}
          />
        </Form.Item>

        {/* 只有本地提供商才显示设备配置选项 */}
        {llmProviderId === 'ollama' && (
          <Form.Item
            label="设备"
            name="device"
            tooltip="本地模型可指定运行设备，云端模型无需配置"
          >
            <Select>
              <Select.Option value="cpu">CPU</Select.Option>
              <Select.Option value="cuda">CUDA (GPU)</Select.Option>
              <Select.Option value="auto">自动</Select.Option>
            </Select>
          </Form.Item>
        )}

        <Form.Item label="Temperature" name="temperature">
          <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item label="Max Tokens" name="max_tokens">
          <InputNumber min={1} max={128000} step={1} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item label="Top P" name="top_p">
          <InputNumber min={0} max={1} step={0.1} style={{ width: '100%' }} />
        </Form.Item>
      </Form>
    </Modal>
  );

  /**
   * 函数级注释：Embedding 配置表单 Modal
   */
  const renderEmbeddingModal = () => (
    <Modal
      title={editingEmbedding ? '编辑 Embedding 配置' : '添加 Embedding 配置'}
      open={embeddingModalVisible}
      onOk={handleSaveEmbedding}
      okText="确定"
      cancelText="取消"
      okButtonProps={{
        style: {
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          border: 'none',
          color: '#fff',
        },
      }}
      cancelButtonProps={{
        style: {
          background: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          color: '#f1f5f9',
        },
      }}
      onCancel={() => setEmbeddingModalVisible(false)}
      width={600}
      destroyOnClose
      footer={(_, { OkBtn, CancelBtn }) => (
        <>
          <CancelBtn />
          <Button
            icon={<ApiOutlined />}
            onClick={() => handleTestInModal(false)}
            loading={testingInModal}
          >
            测试连接
          </Button>
          <OkBtn />
        </>
      )}
    >
      <Form form={embeddingForm} layout="vertical">
        {/* 隐藏的 id 字段，用于编辑模式 */}
        <Form.Item name="id" hidden>
          <Input />
        </Form.Item>

        <Form.Item
          label="提供商"
          name="provider_id"
          rules={[{ required: true, message: '请选择提供商' }]}
        >
          <Select
            options={providers?.embedding_providers?.map((p: ProviderInfo) => ({
              label: p.label,
              value: p.value
            }))}
            onChange={(value) => {
              const provider = providers?.embedding_providers?.find((p: ProviderInfo) => p.value === value);
              if (provider) {
                embeddingForm.setFieldsValue({
                  provider_name: provider.label,
                  endpoint: provider.default_endpoint,
                  model_id: provider.default_models[0] || '',
                  model_name: provider.default_models[0] || ''
                });
              }
            }}
          />
        </Form.Item>

        <Form.Item
          label="端点"
          name="endpoint"
          rules={[
            {
              required: embeddingProviderId !== 'local',
              message: '请输入端点地址'
            }
          ]}
        >
          <Input placeholder={embeddingProviderId === 'local' ? '本地模型无需端点' : 'https://api.openai.com/v1/'} />
        </Form.Item>

        <Form.Item
          label="API密钥"
          name="api_key"
          tooltip={editingEmbedding ? "编辑时不显示密钥，请使用'修改密钥'功能单独更新" : "云端供应商需要配置"}
        >
          <Input.Password
            placeholder={editingEmbedding ? "编辑时请留空，使用'修改密钥'功能单独更新" : "云端供应商需要配置"}
            disabled={!!editingEmbedding}
          />
        </Form.Item>

        <Form.Item
          label="模型"
          name="model_name"
          rules={[{ required: true, message: '请选择模型' }]}
        >
          <Select
            showSearch
            options={embeddingProviderId ? getEmbeddingModelOptions(embeddingProviderId) : []}
          />
        </Form.Item>

        {/* 只有本地提供商才显示设备配置选项 */}
        {(embeddingProviderId === 'ollama' || embeddingProviderId === 'local') && (
          <Form.Item
            label="设备"
            name="device"
            tooltip="本地模型可指定运行设备，云端模型无需配置"
          >
            <Select>
              <Select.Option value="cpu">CPU</Select.Option>
              <Select.Option value="cuda">CUDA (GPU)</Select.Option>
              <Select.Option value="auto">自动</Select.Option>
            </Select>
          </Form.Item>
        )}
      </Form>
    </Modal>
  );

  /**
   * 函数级注释：渲染API密钥修改Modal
   * 内部逻辑：独立的对话框用于修改API密钥，显示当前脱敏的密钥
   */
  const renderKeyUpdateModal = () => (
    <Modal
      title="修改API密钥"
      open={keyUpdateModalVisible}
      onOk={handleKeyUpdateSubmit}
      okText="确定"
      cancelText="取消"
      onCancel={() => setKeyUpdateModalVisible(false)}
      width={500}
      destroyOnClose
      okButtonProps={{
        style: {
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          border: 'none',
          color: '#fff',
        },
      }}
      cancelButtonProps={{
        style: {
          background: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          color: '#f1f5f9',
        },
      }}
    >
      <Form form={keyForm} layout="vertical">
        <Form.Item label="当前密钥">
          <Input.Password
            value={keyUpdateConfig ? (keyUpdateConfig as any).api_key_masked || '(未设置)' : '(未设置)'}
            disabled
            style={{ color: '#999', cursor: 'not-allowed' }}
          />
        </Form.Item>
        <Form.Item
          label="新密钥"
          name="api_key"
          rules={[{ required: true, message: '请输入新的API密钥' }]}
          tooltip="输入新的API密钥以更新配置"
        >
          <Input.Password placeholder="请输入新的API密钥" />
        </Form.Item>
      </Form>
    </Modal>
  );

  /**
   * 函数级注释：渲染Ollama管理面板
   */
  const renderOllamaPanel = () => (
    <Card
      title={
        <Space>
          <span>Ollama 模型管理</span>
          <Tag color={ollamaModels.length > 0 ? 'green' : 'orange'}>
            {ollamaModels.length} 个模型
          </Tag>
        </Space>
      }
      extra={
        <Space>
          <Button size="small" icon={<ReloadOutlined />} onClick={refreshOllamaModels}>
            刷新
          </Button>
          <Button size="small" type="primary" icon={<DownloadOutlined />} onClick={handlePullModel}>
            拉取模型
          </Button>
        </Space>
      }
      style={{ marginTop: 16 }}
    >
      {ollamaModels.length === 0 ? (
        <p style={{ color: '#999' }}>未找到Ollama模型</p>
      ) : (
        <Space wrap>
          {ollamaModels.map((model) => (
            <Tag key={model.name} style={{ fontSize: '14px', padding: '4px 8px' }}>
              {model.name} ({(model.size / 1024 / 1024 / 1024).toFixed(2)} GB)
            </Tag>
          ))}
        </Space>
      )}
    </Card>
  );

  if (loading) {
    return <div style={{ padding: 24, textAlign: 'center' }}>加载中...</div>;
  }

  return (
    <div className="model-config-page">
      <div style={{ marginBottom: 16 }}>
        <h1>模型配置管理</h1>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'llm',
            label: 'LLM 配置',
            children: (
              <>
                <Card
                  title="LLM 模型配置"
                  extra={
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleAddLLM}>
                      添加配置
                    </Button>
                  }
                >
                  <Table
                    dataSource={llmConfigs}
                    columns={llmColumns}
                    rowKey="id"
                    pagination={false}
                    scroll={{ x: 'max-content' }}
                  />
                </Card>
                {renderOllamaPanel()}
              </>
            )
          },
          {
            key: 'embedding',
            label: 'Embedding 配置',
            children: (
              <Card
                title="Embedding 模型配置"
                extra={
                  <Button type="primary" icon={<PlusOutlined />} onClick={handleAddEmbedding}>
                    添加配置
                  </Button>
                }
              >
                <Table
                  dataSource={embeddingConfigs}
                  columns={embeddingColumns}
                  rowKey="id"
                  pagination={false}
                  scroll={{ x: 'max-content' }}
              />
              </Card>
            )
          }
        ]}
      />
      {renderLLMModal()}
      {renderEmbeddingModal()}
      {renderKeyUpdateModal()}
    </div>
  );
};
