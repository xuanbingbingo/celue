import React from 'react';

function Header({ strategyName, totalHit, totalScanned, reportTime }) {
  const hitRate = totalScanned > 0 ? ((totalHit / totalScanned) * 100).toFixed(2) : 0;

  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-6 mb-5 shadow-xl">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            🎯 量化扫描仪表盘
          </h1>
          <p className="text-gray-500 mt-1">{strategyName}</p>
        </div>
        
        <div className="flex flex-wrap gap-4">
          <div className="bg-gradient-to-br from-indigo-50 to-purple-50 px-5 py-3 rounded-xl border border-indigo-100">
            <div className="text-xs text-gray-500 mb-1">扫描总数</div>
            <div className="text-xl font-bold text-indigo-600">{totalScanned.toLocaleString()}</div>
          </div>
          
          <div className="bg-gradient-to-br from-emerald-50 to-teal-50 px-5 py-3 rounded-xl border border-emerald-100">
            <div className="text-xs text-gray-500 mb-1">符合条件</div>
            <div className="text-xl font-bold text-emerald-600">{totalHit.toLocaleString()}</div>
          </div>
          
          <div className="bg-gradient-to-br from-amber-50 to-orange-50 px-5 py-3 rounded-xl border border-amber-100">
            <div className="text-xs text-gray-500 mb-1">命中率</div>
            <div className="text-xl font-bold text-amber-600">{hitRate}%</div>
          </div>
          
          <div className="bg-gradient-to-br from-slate-50 to-gray-50 px-5 py-3 rounded-xl border border-slate-100">
            <div className="text-xs text-gray-500 mb-1">报告时间</div>
            <div className="text-sm font-semibold text-slate-600">{reportTime}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Header;
