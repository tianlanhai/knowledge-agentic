/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：聊天输入组件
 * 内部逻辑：封装输入框和发送按钮，处理键盘事件
 * 设计模式：受控组件模式 - 通过 props 接收 value 和 onChange
 * 职责：提供消息输入和发送功能
 */

import React from 'react';
import { Input, Button } from 'antd';
import { SendOutlined } from '@ant-design/icons';

const { TextArea } = Input;

/**
 * 属性接口：输入组件属性
 */
interface ChatInputProps {
  /** 输入框内容 */
  value: string;
  /** 内容变化回调 */
  onChange: (value: string) => void;
  /** 发送消息回调 */
  onSend: () => void;
  /** 是否正在加载 */
  loading?: boolean;
  /** 占位提示文本 */
  placeholder?: string;
  /** 最小行数 */
  minRows?: number;
  /** 最大行数 */
  maxRows?: number;
}

/**
 * 聊天输入组件
 * 内部逻辑：处理键盘事件（Enter 发送，Shift+Enter 换行），控制发送按钮状态
 * 返回值：JSX.Element
 */
export const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  onSend,
  loading = false,
  placeholder = '输入您的问题...（Shift + Enter 换行）',
  minRows = 2,
  maxRows = 6,
}) => {
  /**
   * 函数级注释：处理键盘事件
   * 内部逻辑：Enter 发送，Shift + Enter 换行
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  /**
   * 函数级注释：检查是否可以发送
   * 内部逻辑：内容非空且不在加载状态
   */
  const canSend = value.trim().length > 0 && !loading;

  return (
    <div className="chat-input-area">
      <TextArea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        autoSize={{ minRows, maxRows }}
        disabled={loading}
        className="chat-input"
      />
      <Button
        type="primary"
        icon={<SendOutlined />}
        onClick={onSend}
        loading={loading}
        disabled={!canSend}
        className="send-btn"
      >
        发送
      </Button>
    </div>
  );
};

/**
 * 默认导出
 */
export default ChatInput;
