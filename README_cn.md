# Jiahao Cao 个人学术网站

网站地址：**https://jiahao116.github.io/**

本仓库用于维护我的个人学术网站，展示量子信息和量子多体物理相关的研究笔记及个人介绍。

## 本地运行与部署

需要 Node.js 22 或更新版本。

```bash
npm install
npm run dev
```

运行 `npm run build` 可生成静态网站。推送到 `main` 分支后，[GitHub Actions](.github/workflows/deploy.yml) 会自动部署到 GitHub Pages。网站内容位于 `content/`。

## 原始项目与许可证

本网站修改自 [**xyjoey/PRISM**](https://github.com/xyjoey/PRISM)，由该项目 fork/衍生而来。原项目采用 MIT 许可证，其版权和许可声明保留在 [LICENSE](LICENSE)。

[English README](README.md)
