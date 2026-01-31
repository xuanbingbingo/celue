// API配置
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

/**
 * 获取策略列表
 */
export async function getStrategies() {
  const response = await fetch(`${API_BASE_URL}/api/strategies`);
  const data = await response.json();
  if (!data.success) {
    throw new Error(data.error || '获取策略列表失败');
  }
  return data.data;
}

/**
 * 执行策略扫描
 * @param {string} strategyName - 策略名称
 */
export async function scanStrategy(strategyName) {
  const response = await fetch(`${API_BASE_URL}/api/scan/${strategyName}`);
  const data = await response.json();
  if (!data.success) {
    throw new Error(data.error || '扫描失败');
  }
  return data.data;
}

/**
 * 健康检查
 */
export async function healthCheck() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    const data = await response.json();
    return data.success && data.status === 'ok';
  } catch {
    return false;
  }
}
