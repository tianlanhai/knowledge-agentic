/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：语义搜索界面组件
 * 内部逻辑：实现基于向量相似度的智能搜索，支持 Markdown 格式化和关键词高亮
 */
import { useState } from 'react';
import { Input, Button, Tag, Slider, Space, Empty, Spin, message, Tooltip } from 'antd';
import {
  SearchOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
  AimOutlined,
} from '@ant-design/icons';
import { searchService } from '../../../services/searchService';
import { SearchResultContent } from './SearchResultContent';
import './Search.css';

const { Search } = Input;

/**
 * 相关度等级配置
 */
const SCORE_LEVELS = {
  HIGH: { threshold: 0.8, color: '#22c55e', text: '高度相关', icon: '🔥' },
  MEDIUM: { threshold: 0.6, color: '#3b82f6', text: '相关', icon: '✨' },
  LOW: { threshold: 0.4, color: '#f59e0b', text: '一般', icon: '⚡' },
  VERY_LOW: { threshold: 0, color: '#ef4444', text: '不相关', icon: '❄️' },
};

/**
 * 获取相关度等级信息
 * 参数说明：score - 相关度分数
 * 返回值：相关度等级对象
 */
const getScoreLevel = (score: number) => {
  if (score >= SCORE_LEVELS.HIGH.threshold) return SCORE_LEVELS.HIGH;
  if (score >= SCORE_LEVELS.MEDIUM.threshold) return SCORE_LEVELS.MEDIUM;
  if (score >= SCORE_LEVELS.LOW.threshold) return SCORE_LEVELS.LOW;
  return SCORE_LEVELS.VERY_LOW;
};

/**
 * 来源类型图标映射
 * 内部变量：来源类型到图标的映射
 */
const SOURCE_TYPE_ICONS: Record<string, string> = {
  FILE: '📄',
  WEB: '🌐',
  DB: '🗄️',
};

/**
 * 来源类型文本映射
 * 内部变量：来源类型到中文的映射
 */
const SOURCE_TYPE_TEXT: Record<string, string> = {
  FILE: '文件',
  WEB: '网页',
  DB: '数据库',
};

/**
 * 搜索结果卡片组件属性接口
 */
interface SearchResultCardProps {
  /** 搜索结果项 */
  item: {
    doc_id: number;
    file_name?: string | null;
    source_type?: string | null;
    content: string;
    score: number;
  };
  /** 索引 */
  index: number;
  /** 搜索关键词 */
  query: string;
  /** 是否展开 */
  isExpanded: boolean;
  /** 切换展开状态 */
  onToggle: () => void;
}

/**
 * 搜索结果卡片组件
 * 内部变量：level - 相关度等级，scorePercent - 分数百分比，displayFileName - 显示的文件名
 * 内部逻辑：根据相关度显示不同样式，高亮显示关键词，支持点击展开
 * 返回值：JSX.Element
 */
const SearchResultCard = ({ item, index, query, isExpanded, onToggle }: SearchResultCardProps) => {
  // 内部变量：获取相关度等级
  const level = getScoreLevel(item.score);
  // 内部变量：计算分数百分比
  const scorePercent = Math.round(item.score * 100);
  // 内部变量：获取来源类型图标
  const sourceIcon = item.source_type ? SOURCE_TYPE_ICONS[item.source_type] || '📄' : '📄';
  // 内部变量：显示的文件名（优先显示文件名，否则显示文档ID）
  const displayFileName = item.file_name || `文档 #${item.doc_id}`;
  // 内部变量：展开/收起图标
  const expandIcon = isExpanded ? '▲' : '▼';

  return (
    <div
      className={`search-result-card ${isExpanded ? 'expanded' : ''}`}
      style={{ animationDelay: `${index * 0.05}s` }}
      onClick={onToggle}
    >
      {/* 头部信息 */}
      <div className="search-result-header">
        <div className="search-result-title">
          <FileTextOutlined className="search-result-icon" />
          <span className="search-result-filename" title={displayFileName}>
            {sourceIcon} {displayFileName}
          </span>
          <span className="search-expand-hint">
            {expandIcon} {isExpanded ? '点击收起' : '点击展开'}
          </span>
        </div>

        {/* 相关度标签 */}
        <div className="search-result-badges">
          <Tooltip title="相关度等级">
            <Tag
              className="search-level-tag"
              style={{
                backgroundColor: `${level.color}20`,
                borderColor: `${level.color}40`,
                color: level.color,
              }}
            >
              <span>{level.icon}</span>
              <span>{level.text}</span>
            </Tag>
          </Tooltip>

          <Tooltip title={`相关度评分: ${scorePercent}%`}>
            <Tag className="search-score-tag">
              <AimOutlined />
              <span>{scorePercent}%</span>
            </Tag>
          </Tooltip>
        </div>
      </div>

      {/* 内容预览 - Markdown 格式化 + 关键词高亮 */}
      <div className={`search-result-content ${isExpanded ? 'content-expanded' : ''}`}>
        <SearchResultContent content={item.content} query={query} />
      </div>

      {/* 相关度进度条 */}
      <div className="search-result-progress">
        <ThunderboltOutlined className="search-progress-icon" />
        <div className="search-progress-track">
          <div
            className="search-progress-fill"
            style={{
              width: `${scorePercent}%`,
              backgroundColor: level.color,
            }}
          >
            <div
              className="search-progress-glow"
              style={{ boxShadow: `0 0 8px ${level.color}` }}
            />
          </div>
        </div>
        <span
          className="search-progress-value"
          style={{ color: level.color }}
        >
          {scorePercent}%
        </span>
      </div>
    </div>
  );
};

/**
 * 语义搜索主界面组件
 * 内部变量：query - 搜索关键词，topK - 返回结果数量，results - 搜索结果，expandedCardId - 展开的卡片ID
 * 内部逻辑：处理搜索请求和结果显示，支持展开/收起搜索结果
 * 返回值：JSX.Element
 */
export const SemanticSearch = () => {
  // 内部变量：搜索关键词
  const [query, setQuery] = useState('');
  // 内部变量：返回结果数量
  const [topK, setTopK] = useState(5);
  // 内部变量：搜索结果
  const [results, setResults] = useState<any[]>([]);
  // 内部变量：加载状态
  const [loading, setLoading] = useState(false);
  // 内部变量：是否已搜索
  const [hasSearched, setHasSearched] = useState(false);
  // 内部变量：展开的卡片索引（-1表示没有展开）
  const [expandedCardIndex, setExpandedCardIndex] = useState(-1);

  /**
   * 处理搜索
   * 内部逻辑：验证输入并调用搜索 API
   */
  const handleSearch = async () => {
    if (!query.trim()) {
      message.error('请输入搜索关键词');
      return;
    }

    setLoading(true);
    setHasSearched(true);
    // 内部逻辑：重置展开状态
    setExpandedCardIndex(-1);
    try {
      const response = await searchService.semanticSearch(query, topK);
      setResults(response);
    } catch (error) {
      message.error('搜索失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 切换卡片展开状态
   * 内部逻辑：如果点击已展开的卡片则收起，否则展开点击的卡片
   * 参数说明：index - 卡片索引
   */
  const handleToggleCard = (index: number) => {
    setExpandedCardIndex(prev => prev === index ? -1 : index);
  };

  /**
   * 处理键盘快捷键
   * 内部逻辑：Enter 键触发搜索
   */
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <div className="search-container">
      {/* 标题栏 */}
      <div className="search-header">
        <div className="search-header-icon">
          <SearchOutlined />
        </div>
        <div className="search-header-title">
          <h3>语义搜索</h3>
          <p>基于向量相似度的智能搜索</p>
        </div>
      </div>

      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* 搜索框 */}
        <div className="search-input-wrapper">
          <label className="search-label">
            <SearchOutlined />
            搜索关键词
          </label>
          <Search
            placeholder="输入您要搜索的内容..."
            enterButton={
              <Button
                type="primary"
                icon={<SearchOutlined />}
                loading={loading}
                disabled={!query.trim()}
              >
                搜索
              </Button>
            }
            size="large"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onSearch={handleSearch}
            onKeyDown={handleKeyDown}
            className="search-input"
          />
        </div>

        {/* 结果数量滑块 */}
        <div className="search-slider-card">
          <div className="search-slider-header">
            <div className="search-slider-title">
              <AimOutlined />
              <span>返回结果数量</span>
            </div>
            <div className="search-slider-value">{topK}</div>
          </div>

          <Slider
            min={1}
            max={20}
            value={topK}
            onChange={setTopK}
            marks={{
              1: '1',
              5: '5',
              10: '10',
              15: '15',
              20: '20',
            }}
            className="search-slider"
          />
        </div>

        {/* 搜索状态 */}
        {loading && (
          <div className="search-loading">
            <Spin size="large" tip="正在搜索知识库..." />
          </div>
        )}

        {/* 无结果状态 */}
        {!loading && hasSearched && results.length === 0 && (
          <Empty
            description={
              <div className="search-empty-text">
                <p>未找到相关结果</p>
                <p className="search-empty-hint">
                  尝试使用不同的关键词或增加返回结果数量
                </p>
              </div>
            }
            image={
              <div className="search-empty-icon">
                <SearchOutlined />
              </div>
            }
          />
        )}

        {/* 搜索结果列表 */}
        {!loading && results.length > 0 && (
          <div className="search-results">
            <div className="search-results-header">
              <span>
                找到 <span className="search-results-count">{results.length}</span> 条相关结果
              </span>
            </div>

            <div className="search-results-list">
              {results.map((item, index) => (
                <SearchResultCard
                  key={index}
                  item={item}
                  index={index}
                  query={query}
                  isExpanded={expandedCardIndex === index}
                  onToggle={() => handleToggleCard(index)}
                />
              ))}
            </div>
          </div>
        )}

        {/* 初始空状态 */}
        {!loading && !hasSearched && (
          <div className="search-intro">
            <div className="search-intro-icon">
              <SearchOutlined />
            </div>
            <h4 className="search-intro-title">开始语义搜索</h4>
            <p className="search-intro-description">
              输入关键词，基于向量相似度搜索知识库中的相关内容
            </p>
            <div className="search-intro-tips">
              <span className="search-tip search-tip-high">🔥 高度相关</span>
              <span className="search-tip search-tip-medium">✨ 相关</span>
              <span className="search-tip search-tip-low">⚡ 一般</span>
            </div>
          </div>
        )}
      </Space>
    </div>
  );
};
