/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：文档分析界面组件
 * 内部逻辑：实现文档总结和对比功能，支持导出为Markdown/PDF
 */
import { useState, useMemo } from 'react';
import { Tabs, Select, Button, Spin, Space, Checkbox, Tooltip, Dropdown } from 'antd';
import type { MenuProps } from 'antd';
import {
  FileTextOutlined,
  FileSearchOutlined,
  CopyOutlined,
  FileOutlined,
  CheckOutlined,
  DownloadOutlined,
  FilePdfOutlined,
  FileMarkdownOutlined,
} from '@ant-design/icons';
import { chatService } from '../../../services/chatService';
import { useDocuments } from '../../../hooks/useDocuments';
import { message } from 'antd';
import { DocumentFormatter } from '../Chat/DocumentFormatter';
import type { FormattingOptions } from '../../../types/chat';
import './DocumentAnalysis.css';

/**
 * 函数级注释：导出内容为Markdown文件
 * 内部逻辑：创建Blob对象 -> 触发下载
 * 参数：
 *   content - 要导出的内容
 *   filename - 文件名
 * 返回值：void
 */
const exportAsMarkdown = (content: string, filename: string = 'document-analysis.md') => {
  // 内部变量：创建Markdown格式的Blob
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8;' });

  // 内部逻辑：创建下载链接并触发点击
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * 函数级注释：导出内容为PDF（使用浏览器打印功能）
 * 内部逻辑：创建打印窗口 -> 写入HTML内容 -> 触发打印
 * 参数：
 *   content - 要导出的内容
 *   title - 文档标题
 * 返回值：void
 */
const exportAsPdf = (content: string, title: string = '文档分析') => {
  // 内部变量：创建打印窗口
  const printWindow = window.open('', '_blank');

  if (!printWindow) {
    message.error('无法打开打印窗口，请检查浏览器弹窗设置');
    return;
  }

  // 内部变量：构建打印HTML内容
  const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>${title}</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
          line-height: 1.6;
          color: #333;
          max-width: 800px;
          margin: 40px auto;
          padding: 20px;
        }
        h1 {
          border-bottom: 2px solid #667eea;
          padding-bottom: 10px;
          color: #667eea;
        }
        p {
          margin: 16px 0;
          text-align: justify;
        }
        @media print {
          body { margin: 0; }
        }
      </style>
    </head>
    <body>
      <h1>${title}</h1>
      <div>${content.replace(/\n/g, '<br>')}</div>
      <script>
        window.onload = function() {
          window.print();
          window.onafterprint = function() {
            window.close();
          };
        };
      </script>
    </body>
    </html>
  `;

  // 内部逻辑：写入HTML并触发打印
  printWindow.document.write(htmlContent);
  printWindow.document.close();
};

/**
 * 结果卡片组件属性接口
 */
interface ResultCardProps {
  /** 卡片标题 */
  title: string;
  /** 卡片内容 */
  content: string;
  /** 复制回调 */
  onCopy: () => void;
  /** 格式化选项 */
  options?: FormattingOptions;
}

/**
 * 结果卡片组件
 * 内部变量：copied - 复制状态
 * 内部逻辑：处理内容复制到剪贴板、导出为Markdown/PDF
 * 返回值：JSX.Element
 */
const ResultCard = ({ title, content, onCopy, options }: ResultCardProps) => {
  // 内部变量：复制状态
  const [copied, setCopied] = useState(false);

  /**
   * 处理复制
   * 内部逻辑：复制内容到剪贴板并显示提示
   */
  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    onCopy();
    setTimeout(() => setCopied(false), 2000);
  };

  /**
   * 导出菜单项配置
   */
  const exportMenuItems: MenuProps['items'] = [
    {
      key: 'markdown',
      label: '导出为 Markdown',
      icon: <FileMarkdownOutlined />,
      onClick: () => {
        // 内部逻辑：生成文件名并导出
        const filename = `${title}-${new Date().toISOString().slice(0, 10)}.md`;
        exportAsMarkdown(content, filename);
        message.success('已导出为 Markdown 文件');
      },
    },
    {
      key: 'pdf',
      label: '导出为 PDF',
      icon: <FilePdfOutlined />,
      onClick: () => {
        exportAsPdf(content, title);
        message.info('请在打印对话框中选择"保存为PDF"');
      },
    },
  ];

  return (
    <div className="analysis-result-card">
      {/* 卡片头部 */}
      <div className="analysis-result-header">
        <div className="analysis-result-title">
          <FileTextOutlined />
          <span>{title}</span>
        </div>

        <Space size={4}>
          {/* 导出下拉菜单 */}
          <Dropdown menu={{ items: exportMenuItems }} trigger={['click']}>
            <Button
              type="text"
              icon={<DownloadOutlined />}
              className="analysis-copy-btn"
            >
              导出
            </Button>
          </Dropdown>

          <Tooltip title={copied ? '已复制' : '复制内容'}>
            <Button
              type="text"
              icon={copied ? <CheckOutlined /> : <CopyOutlined />}
              onClick={handleCopy}
              className="analysis-copy-btn"
            >
              {copied ? '已复制' : '复制'}
            </Button>
          </Tooltip>
        </Space>
      </div>

      {/* 卡片内容 */}
      <div className="analysis-result-content">
        <DocumentFormatter content={content} options={options} />
      </div>
    </div>
  );
};

/**
 * 文档选择器组件属性接口
 */
interface DocumentSelectorProps {
  /** 选中的文档 ID */
  value: number | undefined;
  /** 变更回调 */
  onChange: (value: number) => void;
  /** 文档列表 */
  documents: any[];
  /** 占位符文本 */
  placeholder: string;
  /** 标签文本 */
  label: string;
}

/**
 * 文档选择器组件
 * 内部逻辑：提供单选文档功能
 * 返回值：JSX.Element
 */
const DocumentSelector = ({
  value,
  onChange,
  documents,
  placeholder,
  label,
}: DocumentSelectorProps) => {
  return (
    <div className="analysis-form-group">
      <label className="analysis-form-label">
        <FileOutlined />
        {label}
      </label>
      <Select
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        showSearch
        optionFilterProp="children"
        size="large"
        className="analysis-select"
        getPopupContainer={(triggerNode) => triggerNode.parentElement as HTMLElement}
        options={documents.map((doc) => ({
          value: doc.id,
          label: (
            <div className="analysis-option">
              <FileOutlined className="analysis-option-icon" />
              <span>{doc.file_name}</span>
              <span className="analysis-option-type">({doc.source_type})</span>
            </div>
          ),
        }))}
      />
    </div>
  );
};

/**
 * 文档对比复选框组件属性接口
 */
interface DocumentCheckboxProps {
  /** 选中的文档 ID 列表 */
  value: number[];
  /** 变更回调 */
  onChange: (values: number[]) => void;
  /** 文档列表 */
  documents: any[];
  /** 标签文本 */
  label: string;
}

/**
 * 文档复选框组组件
 * 内部逻辑：提供多选文档功能
 * 返回值：JSX.Element
 */
const DocumentCheckboxGroup = ({
  value,
  onChange,
  documents,
  label,
}: DocumentCheckboxProps) => {
  return (
    <div className="analysis-form-group">
      <label className="analysis-form-label">
        <FileOutlined />
        {label}
      </label>
      <Checkbox.Group
        value={value}
        onChange={onChange}
        className="analysis-checkbox-group"
      >
        {documents.map((doc) => (
          <Checkbox key={doc.id} value={doc.id} className="analysis-checkbox">
            <div className="analysis-checkbox-content">
              <FileOutlined className="analysis-checkbox-icon" />
              <span className="analysis-checkbox-label">{doc.file_name}</span>
              <span className="analysis-checkbox-type">({doc.source_type})</span>
            </div>
          </Checkbox>
        ))}
      </Checkbox.Group>
    </div>
  );
};

/**
 * 文档分析主界面组件
 * 内部变量：summaryDocId - 总结文档 ID，compareDocIds - 对比文档 ID 列表
 * 内部逻辑：处理文档总结和对比功能
 * 返回值：JSX.Element
 */
export const DocumentAnalysis = () => {
  // 内部变量：总结文档 ID
  const [summaryDocId, setSummaryDocId] = useState<number | undefined>();
  // 内部变量：对比文档 ID 列表
  const [compareDocIds, setCompareDocIds] = useState<number[]>([]);
  // 内部变量：总结加载状态
  const [summaryLoading, setSummaryLoading] = useState(false);
  // 内部变量：对比加载状态
  const [compareLoading, setCompareLoading] = useState(false);
  // 内部变量：总结结果
  const [summaryResult, setSummaryResult] = useState('');
  // 内部变量：对比结果
  const [compareResult, setCompareResult] = useState('');
  // 内部变量：获取文档列表
  const { documents } = useDocuments();

  /**
   * 格式化选项配置
   * 内部逻辑：配置 Markdown 渲染选项，启用标题、代码、列表等样式
   */
  const formattingOptions: FormattingOptions = useMemo(() => ({
    enable_markdown: true,
    enable_structured: true,
    highlight_keywords: ['重要', '关键', '注意', '核心', '重点', '总结', '对比', '差异', '相同'],
    max_content_length: 10000,
    code_highlighting: true,
    table_styling: true,
    list_styling: true,
    quote_styling: true,
    heading_styling: true,
    highlight_style: 'background'
  }), []);

  /**
   * 处理文档总结
   * 内部逻辑：调用 API 生成文档总结
   */
  const handleSummarize = async () => {
    if (!summaryDocId) {
      message.error('请选择要总结的文档');
      return;
    }

    setSummaryLoading(true);
    try {
      const response = await chatService.summarizeDocument(summaryDocId);
      setSummaryResult(response.result);
    } catch (error) {
      message.error('总结失败');
    } finally {
      setSummaryLoading(false);
    }
  };

  /**
   * 处理文档对比
   * 内部逻辑：调用 API 对比多个文档
   */
  const handleCompare = async () => {
    if (compareDocIds.length < 2) {
      message.error('请至少选择两个文档进行对比');
      return;
    }

    setCompareLoading(true);
    try {
      const response = await chatService.compareDocuments(compareDocIds);
      setCompareResult(response.result);
    } catch (error) {
      message.error('对比失败');
    } finally {
      setCompareLoading(false);
    }
  };

  /**
   * 处理复制成功
   * 内部逻辑：显示成功提示
   */
  const handleCopySuccess = () => {
    message.success(
      <div className="flex items-center gap-2 text-[#22c55e]">
        <CheckOutlined />
        <span>已复制到剪贴板</span>
      </div>
    );
  };

  /**
   * 标签页配置
   */
  const tabItems = [
    {
      key: 'summary',
      label: (
        <span className="analysis-tab-label">
          <FileTextOutlined />
          <span>文档总结</span>
        </span>
      ),
      children: (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 文档选择器 */}
          <DocumentSelector
            value={summaryDocId}
            onChange={setSummaryDocId}
            documents={documents}
            placeholder="请选择要总结的文档"
            label="选择文档"
          />

          {/* 生成总结按钮 */}
          <Button
            type="primary"
            icon={<FileTextOutlined />}
            onClick={handleSummarize}
            loading={summaryLoading}
            disabled={!summaryDocId}
            className="analysis-submit-btn"
            block
            size="large"
          >
            生成总结
          </Button>

          {/* 加载中状态 */}
          {summaryLoading && (
            <div className="analysis-loading">
              <Spin size="large" tip="正在生成总结，请稍候..." />
            </div>
          )}

          {/* 总结结果 */}
          {summaryResult && !summaryLoading && (
            <ResultCard
              title="总结结果"
              content={summaryResult}
              onCopy={handleCopySuccess}
              options={formattingOptions}
            />
          )}
        </Space>
      ),
    },
    {
      key: 'compare',
      label: (
        <span className="analysis-tab-label">
          <FileSearchOutlined />
          <span>文档对比</span>
        </span>
      ),
      children: (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 文档对比选择器 */}
          <DocumentCheckboxGroup
            value={compareDocIds}
            onChange={(values) => setCompareDocIds(values as number[])}
            documents={documents}
            label="选择文档（至少2个）"
          />

          {/* 开始对比按钮 */}
          <Button
            type="primary"
            icon={<FileSearchOutlined />}
            onClick={handleCompare}
            loading={compareLoading}
            disabled={compareDocIds.length < 2}
            className="analysis-submit-btn"
            block
            size="large"
          >
            开始对比
          </Button>

          {/* 加载中状态 */}
          {compareLoading && (
            <div className="analysis-loading">
              <Spin size="large" tip="正在对比分析，请稍候..." />
            </div>
          )}

          {/* 对比结果 */}
          {compareResult && !compareLoading && (
            <ResultCard
              title="对比结果"
              content={compareResult}
              onCopy={handleCopySuccess}
              options={formattingOptions}
            />
          )}
        </Space>
      ),
    },
  ];

  return (
    <div className="analysis-container">
      {/* 标题栏 */}
      <div className="analysis-header">
        <div className="analysis-header-icon">
          <FileSearchOutlined />
        </div>
        <div className="analysis-header-title">
          <h3>文档分析</h3>
          <p>总结和对比文档内容</p>
        </div>
      </div>

      {/* 功能切换标签 */}
      {documents.length > 0 ? (
        <Tabs
          defaultActiveKey="summary"
          items={tabItems}
          className="analysis-tabs"
          size="large"
        />
      ) : (
        // 空状态
        <div className="analysis-empty">
          <div className="analysis-empty-icon">
            <FileOutlined />
          </div>
          <h4 className="analysis-empty-title">暂无文档</h4>
          <p className="analysis-empty-description">
            请先上传或抓取文档，然后可以进行文档总结和对比分析
          </p>
        </div>
      )}
    </div>
  );
};
