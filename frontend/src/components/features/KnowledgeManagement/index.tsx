/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：知识管理界面组件
 * 内部逻辑：提供文件上传、网页抓取、数据库同步功能
 */
import { FileUpload } from './FileUpload';
import { URLIngest } from './URLIngest';
import { DatabaseSync } from './DatabaseSync';
import './KnowledgeManagement.css';

/**
 * 知识管理主界面组件
 * 内部逻辑：渲染所有知识管理子组件
 * 返回值：JSX.Element
 */
export const KnowledgeManagement = () => {
  return (
    <div className="km-container">
      {/* 功能卡片区 */}
      <div className="km-grid">
        <FileUpload />
        <URLIngest />
        <DatabaseSync />
      </div>
    </div>
  );
};
