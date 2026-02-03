/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：网站页脚组件，显示备案信息和版权声明
 * 内部逻辑：在页面底部显示可点击的备案号链接
 */
import { Layout } from 'antd';
import './Footer.css';

const { Footer: AntFooter } = Layout;

/**
 * 页脚组件
 * 参数：无
 * 内部变量：无
 * 内部逻辑：渲染备案号链接和版权信息
 * 返回值：JSX.Element
 */
export const AppFooter = () => {
  return (
    <AntFooter className="app-footer">
      <div className="footer-content">
        <a
          href="https://beian.miit.gov.cn/"
          target="_blank"
          rel="noopener noreferrer"
          className="icp-link"
        >
          沪ICP备2026003386号-1
        </a>
        <span className="footer-divider">|</span>
        <span className="copyright">上海宇羲伏天智能科技有限公司 © 2026</span>
      </div>
    </AntFooter>
  );
};
