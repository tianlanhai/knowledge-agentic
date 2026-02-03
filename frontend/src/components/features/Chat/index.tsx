/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：智能问答界面组件（重构后）
 * 内部逻辑：组合子组件，协调状态，处理业务逻辑
 * 设计模式：组合模式 - 将复杂组件拆分为多个子组件
 * Flat Design 风格 - 干净、专业的聊天界面
 * 集成会话持久化功能
 */
import React, { useState, useEffect, useRef } from 'react';
import { Avatar } from 'antd';
import { RobotOutlined, UserOutlined } from '@ant-design/icons';
import { useSearchParams } from 'react-router-dom';
import { useConversation } from '../../../hooks/useConversation';
import { DocumentFormatter } from './DocumentFormatter';
import type { FormattingOptions, MessageSource } from '../../../types/chat';
import { ChatToolbar } from './ChatToolbar';
import { ChatInput } from './ChatInput';
import { ChatMessages } from './ChatMessages';
import './Chat.css';

/**
 * 导出子组件供其他地方使用
 */
export { ChatToolbar } from './ChatToolbar';
export { ChatInput } from './ChatInput';
export { ChatMessages } from './ChatMessages';

/**
 * 聊天气泡组件属性接口
 */
interface ChatBubbleProps {
  /** 消息角色 */
  role: 'user' | 'assistant';
  /** 消息内容 */
  content: string;
  /** 是否正在输入 */
  isTyping?: boolean;
  /** 格式化选项 */
  formattingOptions?: FormattingOptions;
  /** 是否正在流式输出 */
  isStreaming?: boolean;
}

/**
 * 聊天气泡组件
 * 内部变量：isUser - 是否为用户消息
 * 内部逻辑：根据角色应用不同样式，支持格式化内容和流式输出优化
 * 返回值：JSX.Element
 *
 * 使用 React.memo 优化：只在 props 真正变化时才重新渲染
 * 自定义比较函数：深度比较 formattingOptions（因为它是 useMemo 稳定引用）
 */
export const ChatBubble = React.memo(({ role, content, isTyping = false, formattingOptions, isStreaming = false }: ChatBubbleProps) => {
  // 内部变量：判断是否为用户消息
  const isUser = role === 'user';

  return (
    <div className={`chat-bubble ${isUser ? 'user' : 'assistant'}`}>
      {/* 头像 */}
      <Avatar
        icon={isUser ? <UserOutlined /> : <RobotOutlined />}
        size={40}
        className="chat-avatar"
      />

      {/* 消息内容 */}
      <div className={`chat-message ${isUser ? 'user-message' : 'assistant-message'}`}>
        {/* 发送者名称 */}
        <div className="chat-sender">
          <span className="sender-name">{isUser ? '用户' : 'AI助手'}</span>
          {!isUser && <span className="sender-status">在线</span>}
        </div>

        {/* 消息内容 */}
        <div className={`chat-content ${isTyping ? 'typing' : ''}`}>
          {isUser ? (
            <div className="user-content">
              {content}
            </div>
          ) : (
            <div className="assistant-content">
              {isTyping && !content ? (
                <span className="typing-indicator">AI正在思考...</span>
              ) : formattingOptions ? (
                <DocumentFormatter
                  content={content}
                  options={formattingOptions}
                  isStreaming={isStreaming}
                />
              ) : (
                <div
                  className="raw-content"
                  dangerouslySetInnerHTML={{ __html: content }}
                />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
  /**
   * React.memo 自定义比较函数
   * 内部逻辑：只有真正的变化才重新渲染
   * 返回值：true 表示 props 相等，不需要重新渲染
   */
  return (
    prevProps.role === nextProps.role &&
    prevProps.content === nextProps.content &&
    prevProps.isTyping === nextProps.isTyping &&
    prevProps.isStreaming === nextProps.isStreaming &&
    prevProps.formattingOptions === nextProps.formattingOptions // 引用比较，useMemo 后应该相等
  );
});

/**
 * 来源引用卡片组件属性接口
 */
interface SourceCardProps {
  /** 来源数据 */
  source: MessageSource;
  /** 索引 */
  index: number;
  /** 点击回调 */
  onSourceClick?: (docId: number) => void;
}

/**
 * 来源引用卡片组件
 * 内部变量：scorePercent - 相关度百分比
 * 内部逻辑：根据分数显示不同颜色，支持格式化内容，支持点击跳转
 * 返回值：JSX.Element
 */
export const SourceCard = ({ source, index, onSourceClick }: SourceCardProps) => {
  // 内部变量：计算相关度百分比（score已经是0-100的整数）
  const scorePercent = source.score || 0;

  /**
   * 获取分数对应的颜色类名
   * 参数：score - 0-100的分数
   */
  const getScoreColorClass = (score: number): string => {
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-medium';
    if (score >= 40) return 'score-low';
    return 'score-poor';
  };

  /**
   * 处理文档名点击事件
   * 内部逻辑：如果有回调函数则调用，否则跳转到文档详情
   */
  const handleFileNameClick = () => {
    // 内部变量：优先使用 document_id，其次使用 id
    const docId = source.document_id || source.id;
    if (onSourceClick) {
      onSourceClick(docId);
    } else {
      // 内部逻辑：可以在这里添加跳转逻辑
      console.log('点击了文档:', docId, source.file_name);
    }
  };

  return (
    <div className="source-card">
      <div className="source-header">
        <div className="source-title">
          <span className="source-icon">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M4 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z" />
            </svg>
          </span>
          {/* 内部逻辑：文件名可点击 */}
          <span
            className="source-filename clickable"
            onClick={handleFileNameClick}
            title={`点击查看文档详情: ${source.file_name}`}
          >
            {source.file_name || `文档 #${source.document_id || source.id}`}
          </span>
        </div>
        {source.score !== null && source.score !== undefined && (
          <span className={`source-score ${getScoreColorClass(scorePercent)}`} title={`相关度: ${scorePercent}%`}>
            {scorePercent}%
          </span>
        )}
      </div>

      {/* 内部逻辑：显示文档片段内容 */}
      <div className="source-content">
        {source.text_segment || "暂无内容预览"}
      </div>

      {/* 相关度进度条 */}
      {source.score !== null && source.score !== undefined && (
        <div className="source-progress">
          <div
            className="source-progress-bar"
            style={{ width: `${Math.min(scorePercent, 100)}%` }}
          />
        </div>
      )}
    </div>
  );
};

/**
 * 温馨提示组件属性接口
 */
interface ChatNoticeProps {
  /** 提示图标类型 */
  iconType?: 'info' | 'warning' | 'success';
  /** 提示标题 */
  title?: string;
  /** 提示内容 */
  content?: string;
}

/**
 * 温馨提示组件
 * 内部逻辑：显示AI内容误差提醒，符合玻璃拟态设计风格
 * 返回值：JSX.Element
 */
export const ChatNotice = ({ iconType = 'info', title = '温馨提示', content = 'AI生成的内容可能存在误差，仅供参考' }: ChatNoticeProps) => {
  return (
    <div className="chat-notice">
      <span className="notice-icon notice-icon-info">ℹ</span>
      <div className="notice-content">
        <span className="notice-title">{title}</span>
        <span className="notice-text">{content}</span>
      </div>
    </div>
  );
};

/**
 * 智能问答主界面组件（重构后）
 * 内部变量：input - 输入内容
 * 内部逻辑：组合子组件，协调状态，处理业务逻辑
 * 返回值：JSX.Element
 */
export const ChatInterface = () => {
  // 内部变量：输入框内容
  const [input, setInput] = useState('');

  // 内部变量：从会话 hook 获取持久化功能
  const {
    messages,
    loading,
    sources,
    useAgent,
    isStreaming,
    startNewConversation,
    sendMessage: sendConversationMessage,
    toggleAgent,
    clearMessages,
  } = useConversation();

  // 内部变量：URL 参数检测，用于公司介绍自动展示
  const [searchParams] = useSearchParams();
  // 内部变量：是否已触发自动介绍（防止重复触发）
  const hasTriggeredIntro = useRef(false);
  // 内部变量：组件是否已初始化
  const isInitialized = useRef(false);

  /**
   * 文件级注释：格式化选项
   * 内部变量：formattingOptions - 格式化配置对象
   * 内部逻辑：使用 useMemo 确保只创建一次，避免触发子组件不必要的重渲染
   * 返回值：FormattingOptions
   */
  const formattingOptions: FormattingOptions = React.useMemo(() => ({
    enable_markdown: true,
    enable_structured: true,
    highlight_keywords: ['重要', '关键', '注意', '核心', '重点', '必须', '建议', '警告', '错误', '成功', '失败'],
    max_content_length: 5000,
    code_highlighting: true,
    table_styling: true,
    list_styling: true,
    quote_styling: true,
    heading_styling: true,
    highlight_style: 'background'
  }), []); // 空依赖数组，确保只创建一次

  /**
   * 自动触发公司介绍
   * 内部逻辑：检测 URL 参数 intro=true 时，自动发送公司介绍请求
   */
  useEffect(() => {
    // 内部变量：是否启用公司介绍模式
    const showIntro = searchParams.get('intro') === 'true';

    // 内部逻辑：满足条件时自动触发介绍
    if (showIntro && !hasTriggeredIntro.current && messages.length === 0 && !loading) {
      hasTriggeredIntro.current = true;
      // 内部变量：公司介绍预设提示词
      const introMessage = '请简单介绍一下宇羲伏天智能科技与产品报价（含智能体）。';
      sendConversationMessage(introMessage);
    }
  }, [searchParams, messages, loading, sendConversationMessage]);

  /**
   * 处理发送消息
   * 内部逻辑：验证输入后发送并清空输入框
   */
  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const content = input.trim();
    setInput('');
    await sendConversationMessage(content);
  };

  return (
    <div className="chat-container">
      {/* 主聊天区域 */}
      <div className="chat-main">
        {/* 顶部工具栏 */}
        <ChatToolbar
          useAgent={useAgent}
          onToggleAgent={toggleAgent}
          onNewConversation={startNewConversation}
          onClearMessages={clearMessages}
        />

        {/* 消息列表区域 */}
        <ChatMessages
          messages={messages}
          sources={sources}
          loading={loading}
          isStreaming={isStreaming}
          formattingOptions={formattingOptions}
        />

        {/* 输入区域 */}
        <ChatInput
          value={input}
          onChange={setInput}
          onSend={handleSend}
          loading={loading}
        />
      </div>
    </div>
  );
};
