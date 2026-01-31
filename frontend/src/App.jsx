import Dashboard from './pages/Dashboard'

function App() {
  // 从全局变量获取数据
  const data = window.scannerData || { 
    results: [], 
    strategyName: 'ma5', 
    strategyDisplayName: 'MA5均线支撑策略',
    totalScanned: 0,
    totalHit: 0
  }

  return <Dashboard data={data} />
}

export default App
