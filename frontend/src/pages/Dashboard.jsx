import { useState, useMemo } from 'react'
import Header from '../components/Header'
import StageCards from '../components/StageCards'
import ConceptCloud from '../components/ConceptCloud'
import StockTable from '../components/StockTable'
import Toast from '../components/Toast'
import { generateSnapshot } from '../utils/snapshot'
import { copyToClipboard } from '../utils/clipboard'

// 阶段配置
const STAGE_CONFIG = {
  '🚀 启动期（重中之重）': {
    bg: 'bg-rose-100',
    border: 'border-rose-500',
    text: 'text-rose-900',
    desc: '近5日跌破三连阳最低价且收盘下跌，最强烈信号'
  },
  '🚀 启动期（重点）': {
    bg: 'bg-red-100',
    border: 'border-red-400',
    text: 'text-red-800',
    desc: '出现关键突破形态，强烈建议关注'
  },
  '🚀 启动期': {
    bg: 'bg-amber-100',
    border: 'border-amber-400',
    text: 'text-amber-800',
    desc: '已突破 + 回踩确认，建议关注'
  },
  '🧪 蓄势中': {
    bg: 'bg-blue-100',
    border: 'border-blue-400',
    text: 'text-blue-800',
    desc: '吸筹完成 + 洗盘结束，等待突破'
  },
  '🏖️ 整理区': {
    bg: 'bg-emerald-100',
    border: 'border-emerald-400',
    text: 'text-emerald-800',
    desc: '吸筹中或横盘整理，观察为主'
  }
}

function Dashboard({ data }) {
  const [stageFilter, setStageFilter] = useState(null)
  const [conceptFilter, setConceptFilter] = useState(null)
  const [toast, setToast] = useState({ show: false, message: '' })

  // 计算统计数据
  const stats = useMemo(() => {
    const stageCounts = {}
    data.results.forEach(r => {
      stageCounts[r.stage] = (stageCounts[r.stage] || 0) + 1
    })
    return stageCounts
  }, [data])

  // 提取所有概念
  const allConcepts = useMemo(() => {
    const concepts = new Set()
    data.results.forEach(r => {
      if (r.concepts) {
        r.concepts.split(' / ').forEach(c => concepts.add(c))
      }
    })
    return Array.from(concepts).sort()
  }, [data])

  // 筛选后的数据
  const filteredResults = useMemo(() => {
    return data.results.filter(r => {
      if (stageFilter && r.stage !== stageFilter) return false
      if (conceptFilter && (!r.concepts || !r.concepts.includes(conceptFilter))) return false
      return true
    })
  }, [data, stageFilter, conceptFilter])

  // 显示Toast
  const showToast = (message) => {
    setToast({ show: true, message })
    setTimeout(() => setToast({ show: false, message: '' }), 2000)
  }

  // 重置筛选
  const resetFilters = () => {
    setStageFilter(null)
    setConceptFilter(null)
  }

  // 复制全部代码
  const copyAllCodes = () => {
    const codes = filteredResults.map(r => r.code).join(',')
    if (codes) {
      copyToClipboard(codes)
      showToast('✅ 已复制到剪贴板')
    } else {
      showToast('⚠️ 没有可复制的代码')
    }
  }

  // 保存快照
  const saveSnapshot = () => {
    if (filteredResults.length === 0) {
      showToast('⚠️ 没有可保存的股票')
      return
    }

    const stocks = filteredResults.map(r => ({
      code: r.code,
      name: r.name
    }))

    const filterText = stageFilter || conceptFilter || '全部标的'
    generateSnapshot(stocks, data.strategyName, filterText)
    showToast('✅ 快照已保存')
  }

  const currentFilterText = conceptFilter ? `概念: ${conceptFilter}` : (stageFilter || '全部标的')

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-500 to-purple-600 p-5">
      <div className="max-w-7xl mx-auto">
        {/* 头部 */}
        <Header 
          strategyName={data.strategyDisplayName}
          totalHit={data.totalHit}
          totalScanned={data.totalScanned}
          reportTime={new Date().toLocaleString('zh-CN')}
        />

        {/* 阶段卡片 */}
        <StageCards 
          stats={stats}
          stageConfig={STAGE_CONFIG}
          activeStage={stageFilter}
          onStageClick={setStageFilter}
        />

        {/* 概念云 */}
        <ConceptCloud 
          concepts={allConcepts}
          activeConcept={conceptFilter}
          onConceptClick={setConceptFilter}
        />

        {/* 操作栏 */}
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-5 mb-5 shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="text-gray-600">
              当前显示: <span className="font-semibold text-gray-800">{currentFilterText}</span> | 
              共 <span className="font-semibold text-gray-800">{filteredResults.length}</span> 条
            </div>
            <div className="flex gap-3">
              <button 
                onClick={resetFilters}
                className="px-5 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-xl font-semibold transition-all duration-300 flex items-center gap-2"
              >
                🔄 重置筛选
              </button>
              <button 
                onClick={saveSnapshot}
                className="px-5 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-xl font-semibold transition-all duration-300 flex items-center gap-2"
              >
                📸 保存快照
              </button>
              <button 
                onClick={copyAllCodes}
                className="px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-xl font-semibold transition-all duration-300 shadow-lg hover:shadow-xl flex items-center gap-2"
              >
                📋 复制全部代码
              </button>
            </div>
          </div>
        </div>

        {/* 代码框 */}
        <div 
          onClick={() => {
            const codes = filteredResults.map(r => r.code).join(',')
            copyToClipboard(codes)
            showToast('✅ 已复制到剪贴板')
          }}
          className="bg-gradient-to-r from-slate-800 to-slate-900 text-sky-400 p-4 rounded-xl mb-5 cursor-pointer hover:shadow-xl transition-all duration-300 flex justify-between items-center"
        >
          <span className="font-mono text-sm truncate max-w-[calc(100%-100px)]">
            {filteredResults.map(r => r.code).join(',')}
          </span>
          <span className="text-xs text-gray-400 bg-white/10 px-3 py-1 rounded-lg">点击复制</span>
        </div>

        {/* 股票表格 */}
        <StockTable 
          stocks={filteredResults}
          stageConfig={STAGE_CONFIG}
          onConceptClick={setConceptFilter}
        />
      </div>

      {/* Toast */}
      <Toast show={toast.show} message={toast.message} />
    </div>
  )
}

export default Dashboard
