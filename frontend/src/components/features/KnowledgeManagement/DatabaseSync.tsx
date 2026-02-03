/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 数据库同步组件
 * Flat Design 风格 - 数据库连接和同步功能
 */
import { useState } from 'react';
import { Input, Select, Button, message, Form, Space, Tooltip } from 'antd';
import {
  DatabaseOutlined,
  PlusOutlined,
  LinkOutlined,
  TableOutlined,
  UnorderedListOutlined,
  TagOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { ingestService } from '../../../services/ingestService';
import type { DBIngestRequest } from '../../../types/ingest';
import { useTaskStore } from '../../../stores/taskStore';
import './KnowledgeManagement.css';

/**
 * 标签组件属性接口
 */
interface TagItemProps {
  /** 标签内容 */
  tag: string;
  /** 关闭回调 */
  onClose: () => void;
}

/**
 * 标签组件
 * 内部变量：tag - 标签内容
 * 内部逻辑：点击关闭按钮时移除标签
 * 返回值：JSX.Element
 */
const TagItem = ({ tag, onClose }: TagItemProps) => {
  return (
    <div className="km-tag">
      <TagOutlined className="km-tag-icon" />
      <span className="km-tag-label">{tag}</span>
      <button
        className="km-tag-close"
        onClick={onClose}
        aria-label={`移除标签 ${tag}`}
      >
        ×
      </button>
    </div>
  );
};

/**
 * 数据库同步主组件
 * 内部变量：form - 表单实例，loading - 加载状态，tags - 标签列表
 * 内部逻辑：处理数据库同步和标签管理
 * 返回值：JSX.Element
 */
export const DatabaseSync = () => {
  // 内部变量：表单实例
  const [form] = Form.useForm();
  // 内部变量：加载状态
  const [loading, setLoading] = useState(false);
  // 内部变量：标签列表
  const [tags, setTags] = useState<string[]>([]);
  // 内部变量：输入的标签
  const [inputTag, setInputTag] = useState('');

  const { addTask } = useTaskStore();

  /**
   * 处理数据库同步
   * 内部逻辑：调用服务同步数据库，获取任务ID
   */
  const handleSync = async (values: any) => {
    const request: DBIngestRequest = {
      connection_uri: values.connection_uri,
      table_name: values.table_name,
      content_column: values.content_column,
      metadata_columns: values.metadata_columns,
    };

    setLoading(true);
    try {
      const response = await ingestService.syncDatabase(request);
      message.success(`数据库同步成功！文档 ID: ${response.document_id}`);
      form.resetFields();
      setTags([]);
    } catch (error) {
      message.error('同步失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 添加标签
   * 内部逻辑：验证并添加新标签到列表
   */
  const handleAddTag = () => {
    if (inputTag && !tags.includes(inputTag)) {
      setTags([...tags, inputTag]);
      setInputTag('');
    }
  };

  return (
    <div className="km-card">
      {/* 标题栏 */}
      <div className="km-card-header">
        <div className="km-card-icon">
          <DatabaseOutlined />
        </div>
        <div className="km-card-title">
          <h3>数据库同步</h3>
          <p>从数据库导入数据到知识库</p>
        </div>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSync}
      >
        {/* 数据库连接字符串 */}
        <Form.Item
          label={
            <div className="km-form-label">
              <LinkOutlined />
              数据库连接字符串
              <Tooltip title="支持 SQLite、PostgreSQL、MySQL 等数据库">
                <InfoCircleOutlined style={{ marginLeft: 'auto', cursor: 'help' }} />
              </Tooltip>
            </div>
          }
          name="connection_uri"
          rules={[{ required: true, message: '请输入数据库连接字符串' }]}
        >
          <Input
            placeholder="例如: sqlite:///path/to/database.db"
            size="large"
            className="km-input"
          />
        </Form.Item>

        {/* 表名 */}
        <Form.Item
          label={
            <div className="km-form-label">
              <TableOutlined />
              表名
            </div>
          }
          name="table_name"
          rules={[{ required: true, message: '请输入表名' }]}
        >
          <Input
            placeholder="例如: users"
            size="large"
            className="km-input"
          />
        </Form.Item>

        {/* 内容列 */}
        <Form.Item
          label={
            <div className="km-form-label">
              <UnorderedListOutlined />
              内容列
              <Tooltip title="包含主要文本内容的列名">
                <InfoCircleOutlined style={{ marginLeft: 'auto', cursor: 'help' }} />
              </Tooltip>
            </div>
          }
          name="content_column"
          rules={[{ required: true, message: '请选择内容列' }]}
        >
          <Input
            placeholder="例如: description"
            size="large"
            className="km-input"
          />
        </Form.Item>

        {/* 元数据列 */}
        <Form.Item
          label={
            <div className="km-form-label">
              <UnorderedListOutlined />
              元数据列
              <Tooltip title="可选，用于存储额外的元数据信息">
                <InfoCircleOutlined style={{ marginLeft: 'auto', cursor: 'help' }} />
              </Tooltip>
            </div>
          }
          name="metadata_columns"
          tooltip="可选，用于存储额外的元数据"
        >
          <Select
            mode="tags"
            placeholder="选择或输入元数据列名"
            size="large"
            style={{ width: '100%' }}
            options={[
              { value: 'id', label: 'ID' },
              { value: 'created_at', label: '创建时间' },
              { value: 'updated_at', label: '更新时间' },
            ]}
          />
        </Form.Item>

        {/* 标签 */}
        <div className="km-form-group">
          <label className="km-form-label">
            <TagOutlined />
            文档标签
          </label>
          <Space.Compact style={{ width: '100%' }}>
            <Input
              placeholder="输入标签名称，按 Enter 添加"
              value={inputTag}
              onChange={(e) => setInputTag(e.target.value)}
              onPressEnter={handleAddTag}
              className="km-tag-input"
            />
            <Button
              icon={<PlusOutlined />}
              onClick={handleAddTag}
              className="km-tag-add-btn"
              disabled={!inputTag.trim()}
            >
              添加
            </Button>
          </Space.Compact>

          {/* 标签列表 */}
          {tags.length > 0 && (
            <div className="km-tag-list">
              {tags.map((tag) => (
                <TagItem
                  key={tag}
                  tag={tag}
                  onClose={() => setTags(tags.filter((t) => t !== tag))}
                />
              ))}
            </div>
          )}
        </div>

        {/* 提交按钮 */}
        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            icon={<DatabaseOutlined />}
            className="km-submit-btn"
            block
          >
            开始同步
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};
