/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：上传进度显示组件
 * 内部逻辑：显示任务处理进度、状态和错误信息
 */
import { useEffect, useState } from 'react';
import { Progress, Alert, Card, Tag, Button } from 'antd';
import { CheckCircleOutlined, LoadingOutlined, CloseCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { ingestService } from '../../../services/ingestService';
import type { TaskResponse, TaskStatus } from '../../../types/ingest';
import './UploadProgress.css';

interface UploadProgressProps {
  /** 任务ID */
  taskId: number;
  /** 文件名 */
  fileName: string;
  /** 完成回调 */
  onComplete?: (taskId: number, documentId?: number) => void;
  /** 失败回调 */
  onFail?: (taskId: number, error: string) => void;
  /** 关闭回调 */
  onClose?: () => void;
}

/**
 * 上传进度组件
 * 内部变量：task - 任务信息，polling - 轮询状态
 * 内部逻辑：轮询任务状态，显示进度和错误信息
 * 返回值：JSX.Element
 */
export const UploadProgress = ({ taskId, fileName, onComplete, onFail, onClose }: UploadProgressProps) => {
  // 内部变量：任务信息
  const [task, setTask] = useState<TaskResponse | null>(null);
  // 内部变量：轮询状态
  const [polling, setPolling] = useState(true);

  /**
   * 获取任务状态
   * 内部逻辑：从服务器获取最新任务状态
   */
  const fetchTaskStatus = async () => {
    try {
      const taskData = await ingestService.getTaskStatus(taskId);
      setTask(taskData);

      // 内部逻辑：根据任务状态决定是否继续轮询
      if (taskData.status === 'completed') {
        setPolling(false);
        onComplete?.(taskId, taskData.document_id);
      } else if (taskData.status === 'failed') {
        setPolling(false);
        onFail?.(taskId, taskData.error_message || '处理失败');
      }
    } catch (error) {
      console.error('获取任务状态失败:', error);
    }
  };

  /**
   * 重试任务
   * 内部逻辑：重新开始轮询任务状态
   */
  const handleRetry = () => {
    setPolling(true);
    fetchTaskStatus();
  };

  /**
   * 轮询任务状态
   * 内部逻辑：每2秒轮询一次任务状态
   */
  useEffect(() => {
    if (!polling) return;

    // 内部逻辑：立即获取一次状态
    fetchTaskStatus();

    // 内部逻辑：设置定时轮询
    const interval = setInterval(fetchTaskStatus, 2000);

    // 内部逻辑：组件卸载时清除定时器
    return () => clearInterval(interval);
  }, [polling, taskId]);

  /**
   * 获取状态标签颜色
   * 内部逻辑：根据任务状态返回不同的颜色
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
   * 获取状态标签文本
   * 内部逻辑：根据任务状态返回中文描述
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

  if (!task) {
    return null;
  }

  return (
    <Card className="upload-progress-card">
      <div className="upload-progress-header">
        <div className="upload-progress-title">
          <span className="upload-progress-filename">{fileName}</span>
          <Tag color={getStatusColor(task.status)}>
            {getStatusText(task.status)}
          </Tag>
        </div>
        <Button
          type="text"
          icon={<CloseCircleOutlined />}
          onClick={onClose}
          className="upload-progress-close"
        />
      </div>

      <div className="upload-progress-body">
        {task.status === 'processing' && (
          <Progress
            percent={task.progress}
            status="active"
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
        )}

        {task.status === 'completed' && (
          <Alert
            message="处理完成"
            description={`文档 ID: ${task.document_id}`}
            type="success"
            icon={<CheckCircleOutlined />}
            showIcon
          />
        )}

        {task.status === 'failed' && (
          <Alert
            message="处理失败"
            description={task.error_message}
            type="error"
            icon={<CloseCircleOutlined />}
            showIcon
            action={
              <Button
                size="small"
                icon={<ReloadOutlined />}
                onClick={handleRetry}
              >
                重试
              </Button>
            }
          />
        )}

        {task.status === 'pending' && (
          <div className="upload-progress-pending">
            <LoadingOutlined spin />
            <span>等待处理...</span>
          </div>
        )}
      </div>
    </Card>
  );
};
