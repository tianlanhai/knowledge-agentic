/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：网页抓取组件
 * 内部逻辑：提供网页 URL 抓取、标签管理功能
 */

import { useState } from 'react';
import { Input, Button, message } from 'antd';
import { LinkOutlined, PlusOutlined, TagOutlined } from '@ant-design/icons';
import { ingestService } from '../../../services/ingestService';
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
 * 网页抓取组件属性接口
 */
interface URLIngestProps {
  /** 抓取成功回调（可选） */
  onIngestSuccess?: (documentId: string) => void;
}

/**
 * 网页抓取组件
 * 内部变量：url - 网页地址，tags - 标签列表，inputTag - 输入的标签，loading - 加载状态
 * 内部逻辑：处理网页内容抓取
 * 返回值：JSX.Element
 */
export const URLIngest = ({ onIngestSuccess }: URLIngestProps) => {
  // 内部变量：URL 输入
  const [url, setUrl] = useState('');
  // 内部变量：标签列表
  const [tags, setTags] = useState<string[]>([]);
  // 内部变量：输入的标签
  const [inputTag, setInputTag] = useState('');
  // 内部变量：加载状态
  const [loading, setLoading] = useState(false);

  /**
   * 处理网页抓取
   * 内部逻辑：调用服务抓取网页内容
   */
  const handleIngest = async () => {
    if (!url) {
      message.error('请输入 URL');
      return;
    }

    setLoading(true);
    try {
      const response = await ingestService.ingestUrl(url, tags);
      message.success(`抓取成功！文档 ID: ${response.document_id}，片段数量: ${response.chunk_count}`);
      setUrl('');
      setTags([]);

      // 内部逻辑：调用抓取成功回调
      if (onIngestSuccess) {
        onIngestSuccess(response.document_id.toString());
      }
    } catch (error) {
      message.error('抓取失败');
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
          <LinkOutlined />
        </div>
        <div className="km-card-title">
          <h3>网页抓取</h3>
          <p>从网页 URL 导入内容到知识库</p>
        </div>
      </div>

      {/* URL 输入区域 */}
      <div className="km-form-group">
        <label className="km-form-label">
          <LinkOutlined />
          网页链接
        </label>
        <Input
          placeholder="https://example.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          size="large"
          className="km-input"
        />
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

      {/* 抓取按钮 */}
      <Button
        type="primary"
        icon={<LinkOutlined />}
        onClick={handleIngest}
        loading={loading}
        disabled={!url.trim()}
        className="km-submit-btn"
        block
      >
        开始抓取
      </Button>
    </div>
  );
};
