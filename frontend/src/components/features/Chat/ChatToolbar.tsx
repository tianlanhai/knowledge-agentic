/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：聊天工具栏组件
 * 内部逻辑：封装新对话、智能体开关、清空按钮等功能
 * 设计模式：展示组件模式 - 纯 UI 组件，通过 props 接收数据和回调
 * 职责：提供聊天界面的工具栏操作
 */

import React from 'react';
import { Button, Switch } from 'antd';
import {
  DeleteOutlined,
  ThunderboltOutlined,
  PlusOutlined,
} from '@ant-design/icons';

/**
 * 属性接口：工具栏组件属性
 */
interface ChatToolbarProps {
  /** 是否启用智能体模式 */
  useAgent: boolean;
  /** 切换智能体模式回调 */
  onToggleAgent: () => void;
  /** 新对话回调 */
  onNewConversation: () => void;
  /** 清空对话回调 */
  onClearMessages: () => void;
}

/**
 * 聊天工具栏组件
 * 内部逻辑：渲染工具栏按钮和开关，通过回调函数处理用户操作
 * 返回值：JSX.Element
 */
export const ChatToolbar: React.FC<ChatToolbarProps> = ({
  useAgent,
  onToggleAgent,
  onNewConversation,
  onClearMessages,
}) => {
  return (
    <div className="chat-toolbar">
      {/* 左侧工具区 */}
      <div className="toolbar-left">
        {/* 新对话按钮 */}
        <Button
          icon={<PlusOutlined />}
          onClick={onNewConversation}
          className="new-conversation-btn"
        >
          新对话
        </Button>

        {/* 智能体模式开关 */}
        <div className="agent-toggle">
          <ThunderboltOutlined className="agent-icon" />
          <span className="agent-label">智能体模式</span>
          <Switch
            checked={useAgent}
            onChange={onToggleAgent}
            className="agent-switch"
          />
        </div>
      </div>

      {/* 右侧清空按钮 */}
      <Button
        icon={<DeleteOutlined />}
        onClick={onClearMessages}
        className="clear-btn"
      >
        清空对话
      </Button>
    </div>
  );
};

/**
 * 默认导出
 */
export default ChatToolbar;
