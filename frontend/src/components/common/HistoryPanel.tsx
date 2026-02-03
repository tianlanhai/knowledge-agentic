/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：历史记录面板组件
 * 内部逻辑：展示历史会话列表，支持加载、删除、继续对话
 */

import { useState } from 'react';
import { List, Card, Button, Empty, Popconfirm, Typography, Tooltip, Badge } from 'antd';
import { 
  HistoryOutlined, 
  DeleteOutlined, 
  MessageOutlined, 
  ClockCircleOutlined,
  CloseOutlined 
} from '@ant-design/icons';
import { useHistoryStore } from '../../stores/historyStore';

const { Text } = Typography;

/**
 * 历史会话卡片组件
 * 展示会话信息和操作按钮
 */
interface HistoryItemProps {
  history: any;
  onLoad: (historyId: string) => void;
  onDelete: (historyId: string) => void;
}

const HistoryItemCard = ({ history, onLoad, onDelete }: HistoryItemProps) => {
  /**
   * 函数级注释：格式化时间
   * 内部逻辑：将Date对象格式化为相对时间字符串
   * 参数：date - 日期对象
   * 返回值：格式化后的时间字符串
   */
  const formatTime = (date: Date | string): string => {
    const d = new Date(date);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    
    // 内部逻辑：根据时间差返回不同的格式
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  };

  return (
    <Card
      hoverable
      className="transition-smooth-hover cursor-pointer card-hover mb-3"
      style={{
        background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
        border: '1px solid rgba(255, 255, 255, 0.05)',
        borderRadius: '12px',
      }}
      onClick={() => onLoad(history.id)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          {/* 会话标题 */}
          <div className="flex items-center gap-2 mb-2">
            <MessageOutlined className="text-[#667eea]" />
            <Text 
              className="text-sm font-semibold text-[#f1f5f9] truncate"
              style={{ marginBottom: 0 }}
            >
              {history.title}
            </Text>
          </div>
          
          {/* 会话信息 */}
          <div className="flex items-center gap-4 text-xs text-[#94a3b8]">
            <div className="flex items-center gap-1">
              <ClockCircleOutlined className="text-[10px]" />
              <span>{formatTime(history.createdAt)}</span>
            </div>
            
            <div className="flex items-center gap-1">
              <MessageOutlined className="text-[10px]" />
              <span>{history.messages.length} 条消息</span>
            </div>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center gap-2">
          <Tooltip title="继续对话">
            <Button
              type="text"
              icon={<MessageOutlined />}
              className="text-[#667eea] hover:text-[#764ba2]"
              style={{ padding: '4px' }}
            />
          </Tooltip>
          
          <Popconfirm
            title="确定要删除这个会话吗？"
            description="删除后将无法恢复"
            onConfirm={() => onDelete(history.id)}
            okText="确定"
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
            <Tooltip title="删除会话">
              <Button
                type="text"
                icon={<DeleteOutlined />}
                danger
                className="hover:text-red-400"
                style={{ padding: '4px' }}
              />
            </Tooltip>
          </Popconfirm>
        </div>
      </div>
    </Card>
  );
};

/**
 * 历史记录面板组件
 */
export const HistoryPanel = () => {
  const { histories, deleteHistory, loadHistory } = useHistoryStore();
  const [searchKeyword, setSearchKeyword] = useState('');

  /**
   * 函数级注释：处理加载会话
   * 参数：historyId - 会话ID
   * 返回值：无
   */
  const handleLoad = (historyId: string) => {
    loadHistory(historyId);
  };

  /**
   * 函数级注释：处理删除会话
   * 参数：historyId - 会话ID
   * 返回值：无
   */
  const handleDelete = (historyId: string) => {
    deleteHistory(historyId);
  };

  /**
   * 函数级注释：过滤历史记录
   * 返回值：过滤后的历史列表
   */
  const filteredHistories = histories.filter((history) =>
    history.title.toLowerCase().includes(searchKeyword.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* 面板头部 */}
      <div
        className="px-5 py-4 flex items-center justify-between"
        style={{
          background: 'rgba(30, 41, 59, 0.6)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        }}
      >
        <div className="flex items-center gap-2">
          <HistoryOutlined className="text-lg text-[#667eea]" />
          <span className="text-base font-semibold text-[#f1f5f9]">历史记录</span>
          <Badge 
            count={histories.length} 
            showZero 
            color="#667eea"
            style={{ backgroundColor: '#667eea' }}
          />
        </div>
        
        {histories.length > 0 && (
          <Popconfirm
            title="确定要清空所有历史记录吗？"
            description="清空后将无法恢复"
            onConfirm={() => deleteHistory('all')}
            okText="确定"
            cancelText="取消"
            okButtonProps={{
              danger: true,
              style: {
                background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                border: 'none',
                color: '#fff',
                borderRadius: '6px',
              },
            }}
            cancelButtonProps={{
              style: {
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#f1f5f9',
                borderRadius: '6px',
              },
            }}
          >
            <Button
              type="text"
              icon={<CloseOutlined />}
              danger
              className="text-xs"
              style={{ padding: '4px 8px' }}
            >
              清空
            </Button>
          </Popconfirm>
        )}
      </div>

      {/* 历史列表 */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        {filteredHistories.length === 0 ? (
          // 空状态
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <span className="text-[#94a3b8]">
                {histories.length === 0 ? '暂无历史记录' : '没有找到匹配的历史'}
              </span>
            }
            style={{
              marginTop: '60px',
            }}
          />
        ) : (
          // 历史列表
          <List
            dataSource={filteredHistories}
            renderItem={(history) => (
              <List.Item style={{ padding: 0, marginBottom: 0 }}>
                <HistoryItemCard
                  history={history}
                  onLoad={handleLoad}
                  onDelete={handleDelete}
                />
              </List.Item>
            )}
          />
        )}
      </div>
    </div>
  );
};
