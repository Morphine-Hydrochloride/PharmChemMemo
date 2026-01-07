# 不背药化 (NoMedChem) 💊

> 让药化不再难背——高效、可视化的药物化学智能辅助学习系统。

**不背药化** 是一个现代化的药物化学复习工具，专为药学专业学生设计。它结合了最新的前端技术与专业的药化数据，提供分子结构可视化、智能记忆曲线和题目练习功能，帮助你更高效地掌握复杂的药物化学知识。

## ✨ 核心功能

- 🧬 **分子结构可视化**：集成 JSME 编辑器与 SVG 渲染，直观展示药物分子结构，支持 3D 旋转与高亮。
- 🧠 **智能抽认卡**：基于遗忘曲线的复习算法，自动安排每日复习计划，提升记忆效率。
- 📝 **题目练习模式**：包含丰富的单选题与多选题库，支持实时反馈与错题解析。
- 📊 **学习进度追踪**：直观的仪表盘展示学习状态、掌握程度和每日打卡记录。
- 📱 **响应式设计**：完美适配桌面端与移动端，随时随地开启复习。

## 🛠 技术栈

本项目基于现代前端工具链构建：

- **核心框架**: [React](https://react.dev/)
- **构建工具**: [Vite](https://vitejs.dev/)
- **样式方案**: [TailwindCSS](https://tailwindcss.com/)
- **图标库**: [Phosphor Icons](https://phosphoricons.com/)

## 🚀 快速开始

如果你想在本地运行本项目：

1.  **克隆仓库**
    ```bash
    git clone https://github.com/Morphine-Hydrochloride/NoMedChem.git
    cd local_project
    ```

2.  **安装依赖**
    ```bash
    npm install
    ```

3.  **启动开发服务器**
    ```bash
    npm run dev
    ```

4.  **构建生产版本**
    ```bash
    npm run build
    ```

## ☁️ 部署

本项目支持通过 **Cloudflare Pages** 进行自动化部署：
1.  Fork 本仓库。
2.  在 Cloudflare Pages 中连接你的 GitHub 账号。
3.  选择本项目，构建命令设置为 `npm run build`，输出目录设置为 `dist`。
4.  点击部署即可。

## 📄 许可证

MIT License
