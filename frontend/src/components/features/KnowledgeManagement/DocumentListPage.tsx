/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：文档列表独立页面
 * 内部逻辑：展示所有已处理完成的文档，支持搜索和删除
 */
import { useState } from 'react';
import { Table, Button, Space, Popconfirm, message, Card, Input, Tooltip } from 'antd';
import { DeleteOutlined, ReloadOutlined, FileTextOutlined, ClockCircleOutlined, SearchOutlined, FolderOutlined } from '@ant-design/icons';
import { useDocuments } from '../../../hooks/useDocuments';
import './DocumentListPage.css';

/**
 * 文档列表独立页面组件
 * 内部变量：searchText - 搜索文本
 * 内部逻辑：渲染文档表格，支持搜索、分页和删除
 * 返回值：JSX.Element
 */
export const DocumentListPage = () => {
  // 内部变量：从 hook 获取文档数据和操作方法
  const { documents, total, loading, refetch, deleteDocument } = useDocuments();
  
  // 内部变量：搜索关键词
  const [searchText, setSearchText] = useState('');

  /**
   * 处理文档删除
   * 内部逻辑：调用删除 API 并刷新列表
   */
  const handleDelete = async (docId: number) => {
    try {
      await deleteDocument(docId);
      message.success('删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  /**
   * 获取文件类型信息接口
   */
  interface TypeInfo {
    /** 图标 */
    icon: string;
    /** 颜色 */
    color: string;
    /** 背景色 */
    bg: string;
  }

  /**
   * 获取文件类型对应的图标和颜色
   * 参数说明：type - 文件类型
   * 返回值：文件类型信息对象
   */
  const getFileTypeInfo = (type: string): TypeInfo => {
    const typeMap: Record<string, TypeInfo> = {
      pdf: { icon: '📄', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)' },
      md: { icon: '📝', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)' },
      docx: { icon: '📄', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)' },
      txt: { icon: '📃', color: '#64748b', bg: 'rgba(100, 116, 139, 0.15)' },
      xlsx: { icon: '📊', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' },
      xls: { icon: '📊', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' },
      WEB: { icon: '🌐', color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.15)' },
      DB: { icon: '🗄️', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)' },
    };
    return typeMap[type] || typeMap.txt;
  };

  /**
   * 文档类型标签组件属性接口
   */
  interface FileTypeTagProps {
    /** 文件类型 */
    type: string;
  }

  /**
   * 文档类型标签组件
   * 内部变量：typeInfo - 文件类型信息
   * 内部逻辑：根据类型显示对应的图标和样式
   * 返回值：JSX.Element
   */
  const FileTypeTag = ({ type }: FileTypeTagProps) => {
    const typeInfo = getFileTypeInfo(type);
    return (
      <span
        className="doc-type-tag"
        style={{
          backgroundColor: typeInfo.bg,
          color: typeInfo.color,
          borderColor: `${typeInfo.color}40`,
        }}
      >
        <span>{typeInfo.icon}</span>
        <span className="doc-type-text">{type}</span>
      </span>
    );
  };

  /**
   * 文档标签组件属性接口
   */
  interface DocTagItemProps {
    /** 标签内容 */
    tag: string;
  }

  /**
   * 文档标签组件
   * 内部变量：tag - 标签内容
   * 返回值：JSX.Element
   */
  const DocTagItem = ({ tag }: DocTagItemProps) => {
    return (
      <span className="doc-tag">{tag}</span>
    );
  };

  /**
   * 过滤文档列表
   * 内部逻辑：根据搜索关键词过滤文档
   */
  const filteredDocuments = documents.filter(doc => {
    if (!searchText) return true;
    const searchLower = searchText.toLowerCase();
    return doc.file_name.toLowerCase().includes(searchLower);
  });

  /**
   * 表格列配置
   */
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      render: (id: number) => (
        <span className="doc-id">#{id}</span>
      ),
    },
    /**
     * 文件名列配置
     * 内部逻辑：自适应宽度，使用 Tooltip 显示完整文件名
     */
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      ellipsis: true,  /* Ant Design 内置省略 */
      render: (name: string) => (
        <div className="doc-name">
          <FileTextOutlined className="doc-name-icon" />
          <Tooltip title={name} placement="topLeft">
            <span className="doc-name-text">{name}</span>
          </Tooltip>
        </div>
      ),
    },
    {
      title: '类型',
      dataIndex: 'source_type',
      key: 'source_type',
      width: 120,
      render: (type: string) => <FileTypeTag type={type} />,
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      width: 200,
      render: (tags: string[]) => (
        <div className="doc-tags">
          {(tags ?? []).length > 0 ? (
            tags.map((tag) => <DocTagItem key={tag} tag={tag} />)
          ) : (
            <span className="doc-no-tags">无标签</span>
          )}
        </div>
      ),
    },
    {
      title: '片段数',
      dataIndex: 'chunk_count',
      key: 'chunk_count',
      width: 100,
      render: (count: number) => (
        <span className="doc-chunk-count">{count}</span>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (createdAt: string) => (
        <div className="doc-time">
          <ClockCircleOutlined className="doc-time-icon" />
          <span>{createdAt}</span>
        </div>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: any) => (
        <Space size="small">
          <Popconfirm
            title="确认删除"
            description="确定要删除这个文档吗？此操作不可恢复。"
            onConfirm={() => handleDelete(record.id)}
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
              className="doc-delete-btn"
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="doc-list-page">
      {/* 页面标题 */}
      <Card className="doc-list-header">
        <div className="doc-list-header-content">
          <div className="doc-list-title">
            <FolderOutlined className="doc-list-icon" />
            <div className="doc-list-title-text">
              <h2>文档列表</h2>
              <p>查看和管理所有已处理的文档</p>
            </div>
          </div>
          <Button
            icon={<ReloadOutlined />}
            onClick={refetch}
            loading={loading}
            className="doc-refresh-btn"
          >
            刷新
          </Button>
        </div>
      </Card>

      {/* 搜索栏 */}
      <Card className="doc-list-search">
        <Input
          placeholder="搜索文档名称"
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          allowClear
          className="doc-search-input"
        />
      </Card>

      {/* 文档表格 */}
      <Card className="doc-list-table">
        <Table
          columns={columns}
          dataSource={filteredDocuments}
          rowKey="id"
          loading={loading}
          scroll={{ x: 'max-content' }}  /* 自适应宽度，内容超出时横向滚动 */
          pagination={{
            total: filteredDocuments.length,
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => (
              <span className="doc-pagination-total">
                共 <span className="doc-count">{total}</span> 条记录
              </span>
            ),
          }}
          className="doc-table"
        />
      </Card>

      {/* 空状态 */}
      {!loading && documents.length === 0 && (
        <div className="doc-empty">
          <div className="doc-empty-icon">
            <FolderOutlined />
          </div>
          <h4 className="doc-empty-title">暂无文档</h4>
          <p className="doc-empty-description">
            上传或抓取第一个文档开始构建您的知识库
          </p>
        </div>
      )}

      {/* 无搜索结果 */}
      {!loading && documents.length > 0 && filteredDocuments.length === 0 && (
        <div className="doc-empty">
          <div className="doc-empty-icon">
            <SearchOutlined />
          </div>
          <h4 className="doc-empty-title">未找到匹配的文档</h4>
          <p className="doc-empty-description">
            尝试使用其他关键词搜索
          </p>
        </div>
      )}
    </div>
  );
};
