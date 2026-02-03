/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：聊天消息列表组件
 * 内部逻辑：封装消息渲染、自动滚动、来源引用等逻辑
 * 设计模式：容器组件模式 - 管理滚动状态和消息列表
 * 职责：渲染消息列表并处理自动滚动
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Avatar, Collapse, Badge } from 'antd';
import { RobotOutlined, FileTextOutlined } from '@ant-design/icons';
import type { MessageWithSources, MessageSource, FormattingOptions } from '../../../types/chat';
import { ChatBubble } from './index';
import { SourceCard } from './index';
import { ChatNotice } from './index';

/**
 * 属性接口：消息列表组件属性
 */
interface ChatMessagesProps {
  /** 消息列表 */
  messages: MessageWithSources[];
  /** 来源引用列表 */
  sources: MessageSource[];
  /** 是否正在加载 */
  loading: boolean;
  /** 是否正在流式输出 */
  isStreaming: boolean;
  /** 格式化选项 */
  formattingOptions: FormattingOptions;
  /** 来源点击回调 */
  onSourceClick?: (docId: number) => void;
}

/**
 * 比较函数：用于 React.memo 的 props 比较
 * 内部逻辑：仅比较关键属性，避免不必要的重渲染
 * 参数：prevProps - 上一次的 props，nextProps - 新的 props
 * 返回值：true 表示 props 相等不需要重渲染，false 表示需要重渲染
 */
const arePropsEqual = (
  prevProps: ChatMessagesProps,
  nextProps: ChatMessagesProps
): boolean => {
  // 内部逻辑：比较关键属性
  return (
    prevProps.messages === nextProps.messages &&
    prevProps.sources === nextProps.sources &&
    prevProps.loading === nextProps.loading &&
    prevProps.isStreaming === nextProps.isStreaming
  );
};

/**
 * 聊天消息列表组件（性能优化版）
 * 内部逻辑：管理滚动状态，渲染消息列表和来源引用
 * 设计模式：容器组件模式 + 性能优化（React.memo）
 * 职责：渲染消息列表并处理自动滚动
 * 返回值：JSX.Element
 */
export const ChatMessages = React.memo<ChatMessagesProps>(({
  messages,
  sources,
  loading,
  isStreaming,
  formattingOptions,
  onSourceClick,
}) => {
  // 内部变量：消息列表底部引用（用于自动滚动）
  const messagesEndRef = useRef<HTMLDivElement>(null);
  // 内部变量：消息列表容器引用（用于检测用户滚动位置）
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  // 内部变量：是否应该自动滚动（用户没有手动滚动时为 true）
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  // 内部变量：上一次的消息长度（用于检测新消息）
  const prevMessagesLengthRef = useRef(0);

  /**
   * 函数级注释：处理消息列表滚动事件
   * 内部逻辑：当用户手动向上滚动时，暂停自动滚动；滚动到底部附近时恢复
   */
  const handleScroll = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    // 内部变量：计算距离底部的距离
    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight;
    const clientHeight = container.clientHeight;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

    // 内部逻辑：如果距离底部超过 100px，认为用户手动滚动了
    const isNearBottom = distanceFromBottom < 100;
    setShouldAutoScroll(isNearBottom);
  }, []);

  /**
   * 函数级注释：判断消息是否正在流式输出
   * 内部逻辑：检查是否为最后一条 assistant 消息且正在流式状态
   */
  const isMessageStreaming = useCallback((index: number): boolean => {
    return (
      isStreaming &&
      index === messages.length - 1 &&
      messages[index].role === 'assistant' &&
      messages[index].streamingState !== 'completed'
    );
  }, [isStreaming, messages]);

  /**
   * 函数级注释：监听消息长度变化，新消息时恢复自动滚动
   */
  useEffect(() => {
    const currentLength = messages.length;
    if (currentLength > prevMessagesLengthRef.current) {
      // 新消息添加时，恢复自动滚动
      setShouldAutoScroll(true);
    }
    prevMessagesLengthRef.current = currentLength;
  }, [messages.length]);

  /**
   * 函数级注释：监听流式状态变化，流式结束时恢复自动滚动
   */
  useEffect(() => {
    if (!isStreaming) {
      setShouldAutoScroll(true);
    }
  }, [isStreaming]);

  /**
   * 函数级注释：优化后的自动滚动到底部
   * 内部逻辑：只在应该自动滚动时滚动，使用 auto 行为避免动画跳动
   */
  useEffect(() => {
    // 只在应该自动滚动时执行
    if (!shouldAutoScroll) {
      return;
    }

    // 使用 requestAnimationFrame 确保 DOM 更新后再滚动
    const rafId = requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'auto' });
    });

    return () => cancelAnimationFrame(rafId);
  }, [messages, sources, shouldAutoScroll]);

  /**
   * 函数级注释：渲染加载指示器
   */
  const renderLoadingIndicator = () => (
    <div className="chat-bubble assistant">
      <Avatar icon={<RobotOutlined />} size={40} className="chat-avatar" />
      <div className="chat-message assistant-message">
        <div className="chat-sender">
          <span className="sender-name">AI助手</span>
        </div>
        <div className="chat-content">
          <div className="loading-dots">
            <span />
            <span />
            <span />
          </div>
        </div>
      </div>
    </div>
  );

  /**
   * 函数级注释：渲染来源引用
   */
  const renderSources = () => (
    <Collapse
      className="sources-collapse"
      expandIconPlacement="end"
      items={[
        {
          key: 'sources',
          label: (
            <div className="sources-header">
              <FileTextOutlined className="sources-icon" />
              <span>来源引用</span>
              <Badge count={sources.length} color="var(--color-primary-500)" />
            </div>
          ),
          children: (
            <div className="sources-list">
              {sources.map((source, index) => (
                <SourceCard
                  key={index}
                  source={source}
                  index={index}
                  onSourceClick={onSourceClick}
                />
              ))}
            </div>
          ),
        },
      ]}
    />
  );

  return (
    <div
      className="chat-messages"
      ref={messagesContainerRef}
      onScroll={handleScroll}
    >
      {/* 温馨提示 */}
      <ChatNotice />

      {messages.length === 0 ? (
        // 空状态
        <div className="chat-empty">
          <div className="empty-icon">
            <RobotOutlined />
          </div>
          <h3 className="empty-title">开始您的智能对话</h3>
          <p className="empty-description">
            我可以帮您查询知识库、回答问题、分析文档。请输入您的问题开始对话。
          </p>
        </div>
      ) : (
        // 消息列表
        messages.map((msg, index) => (
          <ChatBubble
            key={index}
            role={msg.role as 'user' | 'assistant'}
            content={msg.content}
            isTyping={loading && index === messages.length - 1 && msg.role === 'assistant'}
            formattingOptions={msg.role === 'assistant' ? formattingOptions : undefined}
            isStreaming={isMessageStreaming(index)}
          />
        ))
      )}

      {/* 正在加载指示器 */}
      {loading && messages.length > 0 && renderLoadingIndicator()}

      {/* 来源引用 */}
      {sources.length > 0 && renderSources()}

      {/* 滚动锚点 */}
      <div ref={messagesEndRef} />
    </div>
  );
}, arePropsEqual);

/**
 * 默认导出
 */
export default ChatMessages;
