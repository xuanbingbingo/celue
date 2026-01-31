import React from 'react';

function StockTable({ stocks, stageConfig, onConceptClick }) {
  const getStageStyle = (stage) => {
    const config = stageConfig[stage];
    if (!config) return {};
    
    const colorMap = {
      'bg-red-100': '#fef2f2',
      'bg-amber-100': '#fffbeb',
      'bg-blue-100': '#eff6ff',
      'bg-emerald-100': '#ecfdf5',
    };
    
    const textColorMap = {
      'text-red-800': '#991b1b',
      'text-amber-800': '#92400e',
      'text-blue-800': '#1e40af',
      'text-emerald-800': '#065f46',
    };
    
    return {
      backgroundColor: colorMap[config.bg] || '#f3f4f6',
      color: textColorMap[config.text] || '#374151',
    };
  };

  const getChangeStyle = (changeStr) => {
    const change = parseFloat(changeStr.replace('%', ''));
    const isUp = change >= 0;
    return {
      className: isUp 
        ? 'text-red-600 bg-red-50 px-3 py-1 rounded-lg font-bold' 
        : 'text-emerald-600 bg-emerald-50 px-3 py-1 rounded-lg font-bold',
      icon: isUp ? '📈' : '📉'
    };
  };

  if (stocks.length === 0) {
    return (
      <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-10 text-center shadow-xl">
        <div className="text-6xl mb-4">📭</div>
        <div className="text-gray-500 text-lg">暂无符合条件的标的</div>
        <div className="text-gray-400 text-sm mt-2">请尝试调整筛选条件</div>
      </div>
    );
  }

  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-2xl overflow-hidden shadow-xl">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gradient-to-r from-slate-50 to-gray-50 border-b border-gray-200">
              <th className="px-4 py-4 text-left text-sm font-semibold text-gray-600">状态</th>
              <th className="px-4 py-4 text-left text-sm font-semibold text-gray-600">名称</th>
              <th className="px-4 py-4 text-left text-sm font-semibold text-gray-600">代码</th>
              <th className="px-4 py-4 text-left text-sm font-semibold text-gray-600">现价</th>
              <th className="px-4 py-4 text-left text-sm font-semibold text-gray-600">涨跌幅</th>
              <th className="px-4 py-4 text-left text-sm font-semibold text-gray-600">概念板块</th>
              <th className="px-4 py-4 text-left text-sm font-semibold text-gray-600">详情</th>
            </tr>
          </thead>
          <tbody>
            {stocks.map((stock, index) => {
              const changeStyle = getChangeStyle(stock.change);
              const stageStyle = getStageStyle(stock.stage);
              const concepts = stock.concepts ? stock.concepts.split(' / ') : [];
              const m = stock.fullCode?.startsWith('sh') ? 'sh' : 'sz';
              const url = `https://quote.eastmoney.com/concept/${m}${stock.code}.html`;

              return (
                <tr 
                  key={stock.code} 
                  className="border-b border-gray-100 hover:bg-gray-50/50 transition-colors animate-fade-in"
                  style={{ animationDelay: `${index * 0.03}s` }}
                >
                  <td className="px-4 py-4">
                    <span 
                      className="inline-block px-3 py-1.5 rounded-lg text-xs font-semibold"
                      style={stageStyle}
                    >
                      {stock.stage}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <span className="font-semibold text-gray-700 text-sm max-w-[120px] truncate inline-block">
                      {stock.name}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <span className="font-mono font-bold text-gray-800 text-sm">
                      {stock.code}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <span className="font-bold text-gray-800">
                      ¥{stock.price}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <span className={changeStyle.className}>
                      {changeStyle.icon} {stock.change}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex flex-wrap gap-1">
                      {concepts.map(concept => (
                        <span
                          key={concept}
                          onClick={(e) => {
                            e.stopPropagation();
                            onConceptClick(concept);
                          }}
                          className="px-2 py-0.5 bg-sky-50 text-sky-600 rounded-full text-xs cursor-pointer hover:bg-sky-100 transition-colors"
                        >
                          {concept}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <a 
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center justify-center w-9 h-9 bg-gradient-to-br from-slate-100 to-slate-200 rounded-lg hover:from-indigo-500 hover:to-purple-600 hover:scale-110 transition-all duration-300 group"
                    >
                      <svg 
                        width="18" 
                        height="18" 
                        viewBox="0 0 24 24" 
                        fill="none" 
                        stroke="currentColor" 
                        strokeWidth="2"
                        className="text-slate-500 group-hover:text-white transition-colors"
                      >
                        <circle cx="11" cy="11" r="8"></circle>
                        <path d="m21 21-4.35-4.35"></path>
                      </svg>
                    </a>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default StockTable;
