/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：文件上传组件
 * 内部逻辑：提供文件拖拽上传、标签管理功能，支持多种文件格式
 */

import { useState } from 'react';
import { Upload, message, Input, Button } from 'antd';
import { InboxOutlined, PlusOutlined, CloudUploadOutlined, TagOutlined } from '@ant-design/icons';
import { ingestService } from '../../../services/ingestService';
import './KnowledgeManagement.css';

const { Dragger } = Upload;

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
 * 内部变量：tag - 标签内容，onClose - 关闭回调函数
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
 * 文件上传组件属性接口
 */
interface FileUploadProps {
  /** 上传成功回调（可选） */
  onUploadSuccess?: (documentId: number) => void;
}

/**
 * 文件上传组件
 * 内部变量：uploading - 上传状态，progress - 上传进度，tags - 标签列表，inputTag - 输入的标签，dragActive - 拖拽激活状态
 * 内部逻辑：处理文件上传和标签管理
 * 返回值：JSX.Element
 */
export const FileUpload = ({ onUploadSuccess }: FileUploadProps) => {
  // 内部变量：上传状态
  const [uploading, setUploading] = useState(false);
  // 内部变量：上传进度
  const [progress, setProgress] = useState(0);
  // 内部变量：标签列表
  const [tags, setTags] = useState<string[]>([]);
  // 内部变量：输入的标签
  const [inputTag, setInputTag] = useState('');
  // 内部变量：拖拽激活状态
  const [dragActive, setDragActive] = useState(false);

  /**
   * 处理文件上传
   * 内部逻辑：上传文件到服务器并更新进度
   * 参数：file - 要上传的文件对象
   */
  const handleUpload = async (file: File) => {
    setUploading(true);
    setProgress(0);

    try {
      const response = await ingestService.uploadFile(file, tags);
      message.success(`上传成功！任务 ID: ${response.id}`);
      setProgress(100);
      setTags([]);

      // 内部逻辑：调用上传成功回调
      if (onUploadSuccess && response.document_id) {
        onUploadSuccess(response.document_id);
      }
    } catch (error) {
      message.error('上传失败');
    } finally {
      setUploading(false);
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

  /**
   * 上传配置对象
   * 属性：name - 表单字段名，multiple - 是否支持多文件上传，accept - 接受的文件类型
   */
  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.pdf,.md,.docx,.txt,.xlsx,.xls',
    beforeUpload: (file: File) => {
      handleUpload(file);
      return false;
    },
    disabled: uploading,
    onDropEnter: () => setDragActive(true),
    onDropLeave: () => setDragActive(false),
  };

  return (
    <div className="km-card">
      {/* 标题栏 */}
      <div className="km-card-header">
        <div className="km-card-icon">
          <CloudUploadOutlined />
        </div>
        <div className="km-card-title">
          <h3>文件上传</h3>
          <p>上传您的文档到知识库</p>
        </div>
      </div>

      {/* 标签输入区域 */}
      <div className="km-form-group">
        <label className="km-form-label">
          <TagOutlined />
          文档标签
        </label>
        <div className="km-tag-input-group">
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
            添加标签
          </Button>
        </div>

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

      {/* 拖拽上传区域 */}
      <Dragger
        {...uploadProps}
        className={`km-uploader ${dragActive ? 'km-uploader-active' : ''}`}
      >
        <div className="km-uploader-content">
          <div className="km-uploader-icon">
            <InboxOutlined />
          </div>
          <p className="km-uploader-text">点击或拖拽文件到此区域上传</p>
          <p className="km-uploader-hint">
            支持 PDF、Markdown、Word、TXT、Excel 格式
          </p>
        </div>
      </Dragger>

      {/* 上传进度条 */}
      {uploading && (
        <div className="km-progress">
          <div className="km-progress-header">
            <span>上传中...</span>
            <span>{progress}%</span>
          </div>
          <div className="km-progress-bar">
            <div className="km-progress-fill" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}
    </div>
  );
};
