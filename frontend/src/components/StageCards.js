import React from 'react';

function StageCards({ stats, stageConfig, activeStage, onStageClick }) {
  const stageOrder = ['🚀 启动期（重点）', '🚀 启动期', '🧪 蓄势中', '🏖️ 整理区'];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
      {stageOrder.map(stage => {
        const count = stats[stage] || 0;
        if (count === 0) return null;

        const config = stageConfig[stage];
        const isActive = activeStage === stage;
        const stageClass = stage.replace(/[🚀🧪🏖️\s（）]/g, '');

        return (
          <div
            key={stage}
            onClick={() => onStageClick(stage)}
            className={`
              ${config.bg} border-2 ${config.border} rounded-2xl p-5 cursor-pointer
              transition-all duration-300 hover:-translate-y-1 hover:shadow-xl
              ${isActive ? 'ring-4 ring-offset-2 ring-indigo-300 scale-105' : ''}
            `}
          >
            <div className={`text-sm font-semibold ${config.text} mb-2`}>{stage}</div>
            <div className={`text-3xl font-bold ${config.text} mb-2`}>{count}</div>
            <div className="text-xs text-gray-500">{config.desc}</div>
          </div>
        );
      })}
    </div>
  );
}

export default StageCards;
