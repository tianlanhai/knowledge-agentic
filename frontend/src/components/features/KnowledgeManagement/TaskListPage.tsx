/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：任务列表页面
 * 内部逻辑：展示所有任务，支持状态筛选和实时更新
 */
import { useEffect } from 'react';
import { Table, Button, Tag, Space, Card, Select, message, Popconfirm, Progress } from 'antd';
import { ReloadOutlined, DeleteOutlined, SyncOutlined, CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useTasks } from '../../../hooks/useTasks';
import type { TaskStatus } from '../../../types/ingest';
import { ingestService } from '../../../services/ingestService';
import './TaskListPage.css';

/**
 * 获取任务状态标签颜色
 * 内部逻辑：根据任务状态返回对应的标签颜色
 * 返回值：string - 标签颜色
 */
const getStatusColor = (status: TaskStatus): string => {
  switch (status) {
    case 'pending':
      return 'default';
    case 'processing':
      return 'processing';
    case 'completed':
      return 'success';
    case 'failed':
      return 'error';
    default:
      return 'default';
  }
};

/**
 * 获取任务状态文本
 * 内部逻辑：根据任务状态返回中文描述
 * 返回值：string - 状态文本
 */
const getStatusText = (status: TaskStatus): string => {
  switch (status) {
    case 'pending':
      return '等待处理';
    case 'processing':
      return '处理中';
    case 'completed':
      return '已完成';
    case 'failed':
      return '失败';
    default:
      return '未知';
  }
};

/**
 * 获取任务状态图标
 * 内部逻辑：根据任务状态返回对应图标
 * 返回值：JSX.Element - 状态图标
 */
const getStatusIcon = (status: TaskStatus) => {
  switch (status) {
    case 'pending':
      return <ClockCircleOutlined />;
    case 'processing':
      return <SyncOutlined spin />;
    case 'completed':
      return <CheckCircleOutlined />;
    case 'failed':
      return <CloseCircleOutlined />;
    default:
      return null;
  }
};

/**
 * 任务列表主页面组件
 * 内部变量：tasks - 任务列表，loading - 加载状态，filterStatus - 筛选状态
 * 内部逻辑：渲染任务表格，支持状态筛选和任务删除
 * 返回值：JSX.Element
 */
export const TaskListPage = () => {
  // 内部变量：从 hook 获取任务数据和方法
  const { tasks, loading, refetch, filterStatus, filterByStatus } = useTasks();

  /**
   * 自动刷新任务列表
   * 内部逻辑：每3秒刷新一次任务列表，保持数据最新
   */
  useEffect(() => {
    const interval = setInterval(() => {
      refetch();
    }, 3000);

    // 内部逻辑：组件卸载时清除定时器
    return () => clearInterval(interval);
  }, []);

  /**
   * 处理任务删除
   * 内部逻辑：确认后删除任务记录
   */
  const handleDeleteTask = async (taskId: number) => {
    try {
      // 内部逻辑：调用删除任务的 API
      await ingestService.deleteTask(taskId);
      message.success('任务删除成功');
      refetch();
    } catch (error) {
      message.error('任务删除失败');
    }
  };

  /**
   * 表格列配置
   */
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      render: (id: number) => <span className="task-id">#{id}</span>,
    },
    {
      title: '任务名称',
      dataIndex: 'file_name',
      key: 'file_name',
      width: 250,
      render: (name: string) => <span className="task-name">{name}</span>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: TaskStatus) => (
        <Tag icon={getStatusIcon(status)} color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      ),
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress: number) => (
        <Progress percent={progress} size="small" status="active" />
      ),
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      key: 'error_message',
      width: 300,
      render: (errorMsg: string) => (
        <span className="task-error">
          {errorMsg || '-'}
        </span>
      ),
    },
    {
      title: '文档ID',
      dataIndex: 'document_id',
      key: 'document_id',
      width: 100,
      render: (docId: number) => (
        <span className="task-doc-id">
          {docId || '-'}
        </span>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (createdAt: string) => (
        <span className="task-created-at">{new Date(createdAt).toLocaleString('zh-CN')}</span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: any) => (
        <Space size="small">
          <Popconfirm
            title="确认删除"
            description="确定要删除这个任务吗？"
            onConfirm={() => handleDeleteTask(record.id)}
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
            <Button
              danger
              icon={<DeleteOutlined />}
              size="small"
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="task-list-page">
      {/* 页面标题 */}
      <Card className="task-list-header">
        <div className="task-list-header-content">
          <div className="task-list-title">
            <h2>任务列表</h2>
            <p>查看和管理所有处理任务</p>
          </div>
          <Button
            icon={<ReloadOutlined />}
            onClick={refetch}
            loading={loading}
            className="task-refresh-btn"
          >
            刷新
          </Button>
        </div>
      </Card>

      {/* 筛选栏 */}
      <Card className="task-list-filter">
        <div className="task-filter-content">
          <span className="task-filter-label">状态筛选：</span>
          <Select
            defaultValue="all"
            value={filterStatus}
            onChange={(value) => filterByStatus(value as TaskStatus | 'all')}
            className="task-filter-select"
            options={[
              { label: '全部', value: 'all' },
              { label: '等待处理', value: 'pending' },
              { label: '处理中', value: 'processing' },
              { label: '已完成', value: 'completed' },
              { label: '失败', value: 'failed' },
            ]}
          />
          <span className="task-filter-count">
            共 {tasks.total} 个任务
          </span>
        </div>
      </Card>

      {/* 任务表格 */}
      <Card className="task-list-table">
        <Table
          columns={columns}
          dataSource={tasks.items}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: false,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
          className="task-table"
        />
      </Card>

      {/* 空状态 */}
      {!loading && tasks.items.length === 0 && (
        <Card className="task-empty-state">
          <ClockCircleOutlined className="task-empty-icon" />
          <h3>暂无任务</h3>
          <p>还没有任何处理任务，开始上传文件或抓取网页吧！</p>
        </Card>
      )}
    </div>
  );
};
