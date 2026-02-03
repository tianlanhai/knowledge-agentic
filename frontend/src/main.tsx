/**
 * 上海宇羲伏天智能科技有限公司出品
 *
 * 文件级注释：应用入口文件
 * 内部逻辑：将React应用挂载到DOM节点上
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
