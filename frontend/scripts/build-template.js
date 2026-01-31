#!/usr/bin/env node
/**
 * 构建脚本：将 React 组件打包成单个 HTML 模板文件
 * 用于 Python 后端生成报告时注入数据
 */
const fs = require('fs');
const path = require('path');

// 读取文件内容
function readFile(filePath) {
  return fs.readFileSync(filePath, 'utf-8');
}

// 移除 import 语句
function removeImports(content) {
  return content.replace(/import\s+.*?from\s+['"].*?['"];?\n?/g, '');
}

// 移除 export 关键字（包括 export default 和 export const 等）
function removeExports(content) {
  // 移除 export default
  content = content.replace(/export\s+default\s+/g, '');
  // 移除其他 export（如 export const, export function 等）
  content = content.replace(/\bexport\s+/g, '');
  return content;
}

// 构建模板
function buildTemplate() {
  const srcDir = path.join(__dirname, '..', 'src');
  
  // 读取组件
  const componentsDir = path.join(srcDir, 'components');
  const components = {};
  
  fs.readdirSync(componentsDir).forEach(filename => {
    if (filename.endsWith('.js') || filename.endsWith('.jsx')) {
      const filepath = path.join(componentsDir, filename);
      let content = readFile(filepath);
      content = removeImports(content);
      content = removeExports(content);
      components[filename] = content;
    }
  });
  
  // 读取工具函数
  const utilsDir = path.join(srcDir, 'utils');
  const utils = {};
  
  fs.readdirSync(utilsDir).forEach(filename => {
    if (filename.endsWith('.js')) {
      const filepath = path.join(utilsDir, filename);
      let content = readFile(filepath);
      content = removeImports(content);
      content = removeExports(content);
      utils[filename] = content;
    }
  });
  
  // 读取 Dashboard
  const dashboardPath = path.join(srcDir, 'pages', 'Dashboard.jsx');
  let dashboard = readFile(dashboardPath);
  dashboard = removeImports(dashboard);
  dashboard = removeExports(dashboard);
  
  // 读取 App
  const appPath = path.join(srcDir, 'App.jsx');
  let app = readFile(appPath);
  app = removeImports(app);
  app = removeExports(app);
  
  // 构建 HTML 模板
  const template = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>量化扫描仪表盘</title>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .animate-fade-in { animation: fadeIn 0.3s ease-out; }
    </style>
</head>
<body>
    <div id="root"></div>
    <script>
        // 数据占位符 - Python后端会替换这里
        window.scannerData = {{DATA_PLACEHOLDER}};
    </script>
    <script type="text/babel">
const { useState, useMemo } = React;

// ===== Utils =====
${utils['clipboard.js'] || ''}
${utils['snapshot.js'] || ''}

// ===== Components =====
${components['Header.js'] || components['Header.jsx'] || ''}
${components['StageCards.js'] || components['StageCards.jsx'] || ''}
${components['ConceptCloud.js'] || components['ConceptCloud.jsx'] || ''}
${components['StockTable.js'] || components['StockTable.jsx'] || ''}
${components['Toast.js'] || components['Toast.jsx'] || ''}

// ===== Dashboard =====
${dashboard}

// ===== App =====
${app}

// ===== Render =====
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
    </script>
</body>
</html>`;

  // 保存模板文件到项目根目录
  const outputPath = path.join(__dirname, '..', '..', 'report_template.html');
  fs.writeFileSync(outputPath, template, 'utf-8');
  
  console.log('✅ 模板文件已生成:', outputPath);
  return outputPath;
}

// 执行构建
buildTemplate();
