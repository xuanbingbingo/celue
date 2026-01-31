export function generateSnapshot(stocks, strategyName, filterText) {
  // 创建画布
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  // 设置尺寸
  const width = 1400;
  const padding = 60;
  const rowHeight = 50;
  const headerHeight = 100;
  const footerHeight = 60;
  const stocksPerRow = 4;
  const rows = Math.ceil(stocks.length / stocksPerRow);
  const contentHeight = rows * rowHeight;
  const height = headerHeight + contentHeight + footerHeight + padding * 2;

  canvas.width = width;
  canvas.height = height;

  // 绘制背景
  ctx.fillStyle = '#fafafa';
  ctx.fillRect(0, 0, width, height);

  // 绘制标题背景
  ctx.fillStyle = '#1e40af';
  ctx.fillRect(0, 0, width, headerHeight);

  // 绘制标题
  ctx.fillStyle = 'white';
  ctx.font = 'bold 36px Helvetica, Arial, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(`策略: ${strategyName} | ${filterText}`, width / 2, 60);

  // 绘制股票信息
  const startY = headerHeight + padding;
  const stockWidth = (width - padding * 2) / stocksPerRow;

  stocks.forEach((stock, i) => {
    const row = Math.floor(i / stocksPerRow);
    const col = i % stocksPerRow;
    const x = padding + col * stockWidth + 10;
    const y = startY + row * rowHeight + 10;
    const boxW = stockWidth - 20;
    const boxH = rowHeight - 10;

    // 绘制背景框
    ctx.fillStyle = 'white';
    ctx.fillRect(x, y, boxW, boxH);
    ctx.strokeStyle = '#d1d5db';
    ctx.lineWidth = 1;
    ctx.strokeRect(x, y, boxW, boxH);

    // 绘制股票名称（左侧）
    ctx.fillStyle = '#374151';
    ctx.font = 'bold 18px Helvetica, Arial, sans-serif';
    ctx.textAlign = 'left';
    const nameX = x + 15;
    const centerY = y + boxH / 2 + 6;
    ctx.fillText(stock.name, nameX, centerY);

    // 绘制股票代码（右侧）
    ctx.fillStyle = '#1e40af';
    ctx.font = '16px "JetBrains Mono", monospace';
    ctx.textAlign = 'right';
    const codeX = x + boxW - 15;
    ctx.fillText(stock.code, codeX, centerY);
  });

  // 绘制底部信息
  ctx.fillStyle = '#6b7280';
  ctx.font = '16px Helvetica, Arial, sans-serif';
  ctx.textAlign = 'center';
  const now = new Date().toLocaleString('zh-CN');
  ctx.fillText(`共 ${stocks.length} 只股票 | 生成时间: ${now}`, width / 2, height - 25);

  // 下载图片
  canvas.toBlob(blob => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const safeFilterText = filterText.replace(/\s+/g, '_').replace(/[\/\\:*?"<>|]/g, '');
    a.download = `strategy_snapshot_${strategyName}_${safeFilterText}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });
}
