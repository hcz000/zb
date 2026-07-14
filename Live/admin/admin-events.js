// 后台管理系统事件处理器
// 本文件包含所有新功能的按钮事件绑定

// 页面加载完成后绑定事件
document.addEventListener('DOMContentLoaded', () => {
	console.log('🎯 初始化后台管理系统事件处理器...');
	initVotesEvents();
	initAIEvents();
	initLiveControlEvents();
	initDebateFlowEvents();
});

// ==================== 票数管理事件 ====================

function initVotesEvents() {
	// 加载流列表到选择器
	loadVotesStreamsList();
	
	// 刷新流列表按钮
	const refreshStreamsBtn = document.getElementById('votes-refresh-streams-btn');
	if (refreshStreamsBtn) {
		refreshStreamsBtn.addEventListener('click', () => {
			loadVotesStreamsList();
		});
	}
	
	// 流选择变化时，加载对应流的票数
	const streamSelect = document.getElementById('votes-stream-select');
	if (streamSelect) {
		streamSelect.addEventListener('change', async (e) => {
			const streamId = e.target.value;
			if (streamId) {
				await loadVotesByStream(streamId);
			} else {
				// 清空显示
				clearVotesDisplay();
				hideVotesStreamInfo();
			}
		});
	}
	
	// 功能一：设置票数
	const setVotesBtn = document.getElementById('set-votes-btn');
	if (setVotesBtn) {
		setVotesBtn.addEventListener('click', async () => {
			const streamId = document.getElementById('votes-stream-select')?.value;
			if (!streamId) {
				alert('请先选择要管理的直播流');
				return;
			}
			
			const leftVotes = parseInt(document.getElementById('set-left-votes').value) || 0;
			const rightVotes = parseInt(document.getElementById('set-right-votes').value) || 0;
			const reason = document.getElementById('set-votes-reason').value || '手动设置';
			
			if (leftVotes === 0 && rightVotes === 0) {
				alert('请输入要设置的票数');
				return;
			}
			
			if (!confirm(`确定要设置票数为：正方 ${leftVotes}，反方 ${rightVotes} 吗？`)) {
				return;
			}
			
			const result = await updateVotes('set', leftVotes, rightVotes, reason, true, streamId);
			if (result) {
				// 更新显示
				updateVotesDisplay(result.afterUpdate);
				// 清空输入框
				document.getElementById('set-left-votes').value = '';
				document.getElementById('set-right-votes').value = '';
				document.getElementById('set-votes-reason').value = '';
			}
		});
	}
	
	// 功能二：增加票数
	const addVotesBtn = document.getElementById('add-votes-btn');
	if (addVotesBtn) {
		addVotesBtn.addEventListener('click', async () => {
			const streamId = document.getElementById('votes-stream-select')?.value;
			if (!streamId) {
				alert('请先选择要管理的直播流');
				return;
			}
			
			const leftVotes = parseInt(document.getElementById('add-left-votes').value) || 0;
			const rightVotes = parseInt(document.getElementById('add-right-votes').value) || 0;
			const reason = document.getElementById('add-votes-reason').value || '增加票数';
			
			if (leftVotes === 0 && rightVotes === 0) {
				alert('请输入要增加的票数');
				return;
			}
			
			if (!confirm(`确定要增加票数：正方 +${leftVotes}，反方 +${rightVotes} 吗？`)) {
				return;
			}
			
			const result = await updateVotes('add', leftVotes, rightVotes, reason, true, streamId);
			if (result) {
				// 更新显示
				updateVotesDisplay(result.afterUpdate);
				// 清空输入框
				document.getElementById('add-left-votes').value = '';
				document.getElementById('add-right-votes').value = '';
				document.getElementById('add-votes-reason').value = '';
			}
		});
	}
	
	// 功能三：重置票数
	const resetVotesBtn = document.getElementById('reset-votes-btn');
	if (resetVotesBtn) {
		resetVotesBtn.addEventListener('click', async () => {
			const streamId = document.getElementById('votes-stream-select')?.value;
			if (!streamId) {
				alert('请先选择要管理的直播流');
				return;
			}
			
			const leftVotes = parseInt(document.getElementById('reset-left-votes').value) || 0;
			const rightVotes = parseInt(document.getElementById('reset-right-votes').value) || 0;
			
			if (!confirm(`⚠️ 确定要重置票数吗？\n将重置为：正方 ${leftVotes}，反方 ${rightVotes}\n当前数据会被自动备份。`)) {
				return;
			}
			
			const result = await resetVotes(leftVotes, rightVotes, true, true, streamId);
			if (result) {
				// 更新显示
				updateVotesDisplay({
					leftVotes: result.currentVotes.leftVotes,
					rightVotes: result.currentVotes.rightVotes
				});
			}
		});
	}
}

/**
 * 加载流列表到票数管理选择器
 */
async function loadVotesStreamsList() {
	try {
		const streamSelect = document.getElementById('votes-stream-select');
		if (!streamSelect) return;
		
		const streamsResult = await getStreamsList();
		if (!streamsResult || !streamsResult.streams) {
			console.warn('⚠️ 无法获取流列表');
			return;
		}
		
		const streams = streamsResult.streams;
		
		// 保存当前选中的值
		const currentValue = streamSelect.value;
		
		// 清空并重新填充
		streamSelect.innerHTML = '<option value="">请选择要管理的直播流</option>';
		
		streams.forEach(stream => {
			const option = document.createElement('option');
			option.value = stream.id;
			option.textContent = `${stream.name || 'Unnamed'} (${stream.type || 'UNKNOWN'})`;
			streamSelect.appendChild(option);
		});
		
		// 恢复之前选中的值
		if (currentValue) {
			streamSelect.value = currentValue;
		}
		
		console.log('✅ 票数管理流列表已加载');
	} catch (error) {
		console.error('❌ 加载票数管理流列表失败:', error);
	}
}

/**
 * 根据流ID加载票数
 */
async function loadVotesByStream(streamId) {
	try {
		const data = await fetchDashboardByStream(streamId);
		if (!data) {
			console.warn('⚠️ 无法获取流票数数据');
			return;
		}
		
		const leftVotes = data.leftVotes || 0;
		const rightVotes = data.rightVotes || 0;
		const totalVotes = data.totalVotes || (leftVotes + rightVotes);
		const leftPercentage = data.leftPercentage || (totalVotes > 0 ? Math.round((leftVotes / totalVotes) * 100) : 50);
		const rightPercentage = data.rightPercentage || (totalVotes > 0 ? Math.round((rightVotes / totalVotes) * 100) : 50);
		
		updateVotesDisplay({
			leftVotes,
			rightVotes,
			totalVotes,
			leftPercentage,
			rightPercentage
		});
		
		// 显示当前流信息
		const streamsResult = await getStreamsList();
		if (streamsResult && streamsResult.streams) {
			const stream = streamsResult.streams.find(s => s.id === streamId);
			if (stream) {
				showVotesStreamInfo(stream.name || 'Unnamed', data.isLive ? '🟢 直播中' : '⚪ 未开播');
			}
		}
		
		console.log(`✅ 已加载流 ${streamId} 的票数数据`);
	} catch (error) {
		console.error('❌ 加载流票数失败:', error);
		showNotification('加载票数失败', 'error');
	}
}

/**
 * 显示当前流信息
 */
function showVotesStreamInfo(streamName, status) {
	const infoEl = document.getElementById('votes-current-stream-info');
	const nameEl = document.getElementById('votes-current-stream-name');
	const statusEl = document.getElementById('votes-current-stream-status');
	
	if (infoEl) infoEl.style.display = 'block';
	if (nameEl) nameEl.textContent = streamName;
	if (statusEl) statusEl.textContent = status;
}

/**
 * 隐藏当前流信息
 */
function hideVotesStreamInfo() {
	const infoEl = document.getElementById('votes-current-stream-info');
	if (infoEl) infoEl.style.display = 'none';
}

/**
 * 清空票数显示
 */
function clearVotesDisplay() {
	updateVotesDisplay({
		leftVotes: 0,
		rightVotes: 0,
		totalVotes: 0,
		leftPercentage: 50,
		rightPercentage: 50
	});
}

// 更新票数显示
function updateVotesDisplay(data) {
	const leftVotesEl = document.getElementById('admin-left-votes');
	const rightVotesEl = document.getElementById('admin-right-votes');
	const totalVotesEl = document.getElementById('admin-total-votes');
	const percentageEl = document.getElementById('admin-vote-percentage');
	
	if (leftVotesEl) leftVotesEl.textContent = data.leftVotes || 0;
	if (rightVotesEl) rightVotesEl.textContent = data.rightVotes || 0;
	
	const total = (data.leftVotes || 0) + (data.rightVotes || 0);
	if (totalVotesEl) totalVotesEl.textContent = total;
	
	if (percentageEl) {
		const leftPct = data.leftPercentage || (total > 0 ? Math.round((data.leftVotes / total) * 100) : 50);
		const rightPct = data.rightPercentage || (total > 0 ? Math.round((data.rightVotes / total) * 100) : 50);
		percentageEl.textContent = `正方: ${leftPct}% | 反方: ${rightPct}%`;
	}
}

// ==================== AI控制事件 ====================

function initAIEvents() {
	// 🔧 新增：加载AI直播流列表
	loadAIStreamsList();
	
	// 🔧 新增：刷新直播流列表按钮
	const aiRefreshStreamsBtn = document.getElementById('ai-refresh-streams-btn');
	if (aiRefreshStreamsBtn) {
		aiRefreshStreamsBtn.addEventListener('click', () => {
			loadAIStreamsList();
		});
	}
	
	// 🔧 新增：流选择变化时，重新加载AI内容列表
	const aiStreamSelect = document.getElementById('ai-stream-select');
	if (aiStreamSelect) {
		aiStreamSelect.addEventListener('change', async (e) => {
			const streamId = e.target.value;
			if (streamId) {
				// 🔧 新增：查询该流的 AI 状态并更新按钮
				console.log(`🔄 切换到流 ${streamId}，查询 AI 状态...`);
				await updateAIStatusForStream(streamId);
				
				// 重新加载AI内容列表
				await loadAIContentList(1);
			} else {
				// 清空显示
				hideAIContentStreamInfo();
				const container = document.getElementById('ai-content-list');
				if (container) {
					container.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">请先选择要查看的直播流</div>';
				}
				
				// 重置 AI 按钮状态为 stopped
				updateAIControlButtons('stopped');
			}
		});
	}
	
	// 启动AI识别（改为通过直播接口启动）
	const startAIBtn = document.getElementById('start-ai-btn');
	if (startAIBtn) {
		startAIBtn.addEventListener('click', async () => {
			// 🔧 修复：将 originalText 定义在 try 块外，确保 finally 块能访问
			const originalText = startAIBtn.textContent;
			
			try {
				// 🔧 新增：从AI专用的直播流选择器获取streamId（必填）
				const aiStreamSelect = document.getElementById('ai-stream-select');
				const streamId = aiStreamSelect?.value?.trim() || null;
				
				// 🔧 新增：验证是否选择了直播流
				if (!streamId) {
					if (typeof showToast === 'function') {
						showToast('请先选择要操作的直播流！', 'error');
					} else {
						alert('请先选择要操作的直播流！');
					}
					// 高亮显示选择框
					if (aiStreamSelect) {
						aiStreamSelect.style.border = '2px solid #ff4d4f';
						setTimeout(() => {
							aiStreamSelect.style.border = '';
						}, 2000);
					}
					return;
				}
				
				// 获取AI设置（从表单中获取）
				const settings = {
					mode: document.getElementById('ai-mode')?.value || 'realtime',
					interval: parseInt(document.getElementById('ai-interval')?.value) || 5000,
					sensitivity: document.getElementById('ai-sensitivity')?.value || 'high',
					minConfidence: parseFloat(document.getElementById('ai-confidence')?.value) || 0.7
				};
				
				console.log('🚀 启动AI识别，直播流:', streamId, '设置:', settings);
				
				// 禁用按钮，防止重复点击
				startAIBtn.disabled = true;
				startAIBtn.textContent = '启动中...';
				
				// 调用AI启动接口（根据接口文档：/api/v1/admin/ai/start）
				const result = await startAI(settings, streamId, true);
				
				// 🔧 兼容两种返回格式：
				// 1. {success: true, data: {...}}  (接口文档格式)
				// 2. {aiSessionId: "...", status: "running", ...}  (直接返回数据)
				const isSuccess = result && (result.success || result.aiSessionId || result.status === 'running');
				
				if (isSuccess) {
					console.log('✅ AI识别启动成功', result);
					updateAIControlButtons('running');
					
					// 🔧 新增：显示运行中的流信息
					const streamName = aiStreamSelect.options[aiStreamSelect.selectedIndex]?.text || streamId;
					const streamInfoEl = document.getElementById('ai-current-stream-info');
					const streamNameEl = document.getElementById('ai-running-stream-name');
					if (streamInfoEl && streamNameEl) {
						streamNameEl.textContent = streamName;
						streamInfoEl.style.display = 'block';
					}
					
					// 显示成功提示
					if (typeof showToast === 'function') {
						showToast(`AI识别启动成功！（流：${streamName}）`, 'success');
					}
					
					// 启动成功后，延迟订阅AI内容更新（等待后端ASR服务就绪）
					setTimeout(() => {
						if (typeof loadAIContentList === 'function') {
							console.log('📡 开始订阅AI内容更新...');
							loadAIContentList(1);
						}
						
						// 设置定时刷新AI内容列表
						if (window.aiContentRefreshTimer) {
							clearInterval(window.aiContentRefreshTimer);
						}
						window.aiContentRefreshTimer = setInterval(() => {
							if (typeof loadAIContentList === 'function') {
								loadAIContentList(1);
							}
						}, 5000); // 每5秒刷新一次
					}, 2000); // 延迟2秒，等待后端ASR服务启动
				} else {
					console.error('❌ 启动AI识别失败:', result);
					if (typeof showToast === 'function') {
						showToast('启动AI识别失败：' + (result?.message || '未知错误'), 'error');
					}
				}
			} catch (error) {
				console.error('❌ 启动AI识别失败:', error);
				if (typeof showToast === 'function') {
					showToast('启动AI识别失败：' + error.message, 'error');
				}
			} finally {
				// 恢复按钮状态
				startAIBtn.disabled = false;
				startAIBtn.textContent = originalText;
			}
		});
	}
	
	// 停止AI识别
	const stopAIBtn = document.getElementById('stop-ai-btn');
	if (stopAIBtn) {
		stopAIBtn.addEventListener('click', async () => {
			if (!confirm('确定要停止AI识别吗？')) {
				return;
			}
			
			// 🔧 修复：将 originalText 定义在 try 块外，确保 finally 块能访问
			const originalText = stopAIBtn.textContent;
			
			try {
				// 🔧 新增：从AI专用的直播流选择器获取streamId
				const aiStreamSelect = document.getElementById('ai-stream-select');
				const streamId = aiStreamSelect?.value?.trim() || null;
				
				console.log('⏹️ 停止AI识别，直播流:', streamId || '未指定');
				
				// 禁用按钮，防止重复点击
				stopAIBtn.disabled = true;
				stopAIBtn.textContent = '停止中...';
				
				// 调用AI停止接口（根据接口文档：/api/v1/admin/ai/stop）
				const result = await stopAI(streamId, true, true);
				
				// 🔧 兼容两种返回格式：
				// 1. {success: true, data: {...}}  (接口文档格式)
				// 2. {aiSessionId: "...", status: "stopped", ...}  (直接返回数据)
				const isSuccess = result && (result.success || result.aiSessionId || result.status === 'stopped');
				
				if (isSuccess) {
					console.log('✅ AI识别已停止', result);
					updateAIControlButtons('stopped');
					
					// 🔧 新增：隐藏运行中的流信息
					const streamInfoEl = document.getElementById('ai-current-stream-info');
					if (streamInfoEl) {
						streamInfoEl.style.display = 'none';
					}
					
					// 显示成功提示
					if (typeof showToast === 'function') {
						showToast('AI识别已停止', 'success');
					}
					
					// 清理AI内容刷新定时器
					if (window.aiContentRefreshTimer) {
						clearInterval(window.aiContentRefreshTimer);
						window.aiContentRefreshTimer = null;
						console.log('🧹 已清理AI内容刷新定时器');
					}
				} else {
					console.error('❌ 停止AI识别失败:', result);
					if (typeof showToast === 'function') {
						showToast('停止AI识别失败：' + (result?.message || '未知错误'), 'error');
					}
				}
			} catch (error) {
				console.error('❌ 停止AI识别失败:', error);
				if (typeof showToast === 'function') {
					showToast('停止AI识别失败：' + error.message, 'error');
				}
			} finally {
				// 恢复按钮状态
				stopAIBtn.disabled = false;
				stopAIBtn.textContent = originalText;
			}
		});
	}
	
	// 暂停AI识别
	const pauseAIBtn = document.getElementById('pause-ai-btn');
	if (pauseAIBtn) {
		pauseAIBtn.addEventListener('click', async () => {
			// 🔧 修复：将 originalText 定义在 try 块外，确保 finally 块能访问
			const originalText = pauseAIBtn.textContent;
			
			try {
				console.log('⏸️ 暂停AI识别...');
				
				// 禁用按钮，防止重复点击
				pauseAIBtn.disabled = true;
				pauseAIBtn.textContent = '暂停中...';
				
				const result = await toggleAI('pause', true);
				
				// 🔧 兼容两种返回格式
				const isSuccess = result && (result.success || result.status === 'paused');
				
				if (isSuccess) {
					console.log('✅ AI识别已暂停', result);
					updateAIControlButtons('paused');
					if (typeof showToast === 'function') {
						showToast('AI识别已暂停', 'success');
					}
				} else {
					console.error('❌ 暂停AI识别失败:', result);
					if (typeof showToast === 'function') {
						showToast('暂停AI识别失败：' + (result?.message || '未知错误'), 'error');
					}
				}
			} catch (error) {
				console.error('❌ 暂停AI识别失败:', error);
				if (typeof showToast === 'function') {
					showToast('暂停AI识别失败：' + error.message, 'error');
				}
			} finally {
				// 恢复按钮状态
				pauseAIBtn.disabled = false;
				pauseAIBtn.textContent = originalText;
			}
		});
	}
	
	// 恢复AI识别
	const resumeAIBtn = document.getElementById('resume-ai-btn');
	if (resumeAIBtn) {
		resumeAIBtn.addEventListener('click', async () => {
			// 🔧 修复：将 originalText 定义在 try 块外，确保 finally 块能访问
			const originalText = resumeAIBtn.textContent;
			
			try {
				console.log('▶️ 恢复AI识别...');
				
				// 禁用按钮，防止重复点击
				resumeAIBtn.disabled = true;
				resumeAIBtn.textContent = '恢复中...';
				
				const result = await toggleAI('resume', true);
				
				// 🔧 兼容两种返回格式
				const isSuccess = result && (result.success || result.status === 'running');
				
				if (isSuccess) {
					console.log('✅ AI识别已恢复', result);
					updateAIControlButtons('running');
					if (typeof showToast === 'function') {
						showToast('AI识别已恢复', 'success');
					}
				} else {
					console.error('❌ 恢复AI识别失败:', result);
					if (typeof showToast === 'function') {
						showToast('恢复AI识别失败：' + (result?.message || '未知错误'), 'error');
					}
				}
			} catch (error) {
				console.error('❌ 恢复AI识别失败:', error);
				if (typeof showToast === 'function') {
					showToast('恢复AI识别失败：' + error.message, 'error');
				}
			} finally {
				// 恢复按钮状态
				resumeAIBtn.disabled = false;
				resumeAIBtn.textContent = originalText;
			}
		});
	}
	
	// 刷新AI内容
	const refreshAIBtn = document.getElementById('refresh-ai-content-btn');
	if (refreshAIBtn) {
		refreshAIBtn.addEventListener('click', async () => {
			await loadAIContentList();
		});
	}
}

// 更新AI控制按钮状态
function updateAIControlButtons(status) {
	const startBtn = document.getElementById('start-ai-btn');
	const stopBtn = document.getElementById('stop-ai-btn');
	const pauseBtn = document.getElementById('pause-ai-btn');
	const resumeBtn = document.getElementById('resume-ai-btn');
	const statusIcon = document.getElementById('ai-status-icon');
	const statusText = document.getElementById('ai-status-text');
	
	// 更新状态显示
	if (statusIcon && statusText) {
		switch (status) {
			case 'running':
				statusIcon.textContent = '🟢';
				statusText.textContent = '运行中';
				statusText.style.color = '#4CAF50';
				break;
			case 'paused':
				statusIcon.textContent = '🟡';
				statusText.textContent = '已暂停';
				statusText.style.color = '#FF9800';
				break;
			case 'stopped':
				statusIcon.textContent = '⚪';
				statusText.textContent = '未启动';
				statusText.style.color = '#666';
				break;
		}
	}
	
	// 更新按钮状态
	if (startBtn && stopBtn && pauseBtn && resumeBtn) {
		switch (status) {
			case 'running':
				startBtn.disabled = true;
				stopBtn.disabled = false;
				pauseBtn.disabled = false;
				pauseBtn.style.display = '';
				resumeBtn.style.display = 'none';
				break;
			case 'paused':
				startBtn.disabled = true;
				stopBtn.disabled = false;
				pauseBtn.style.display = 'none';
				resumeBtn.style.display = '';
				resumeBtn.disabled = false;
				break;
			case 'stopped':
				startBtn.disabled = false;
				stopBtn.disabled = true;
				pauseBtn.disabled = true;
				pauseBtn.style.display = '';
				resumeBtn.style.display = 'none';
				break;
		}
	}
}

/**
 * 🔧 查询并更新指定流的 AI 状态
 * @param {string} streamId - 直播流ID
 */
async function updateAIStatusForStream(streamId) {
	if (!streamId) {
		console.warn('⚠️ updateAIStatusForStream: streamId 为空');
		updateAIControlButtons('stopped');
		return;
	}
	
	try {
		console.log(`🔍 查询流 ${streamId} 的 AI 状态...`);
		
		// 🔧 关键修复：使用 fetchDashboardByStream 查询特定流的状态
		let dashboard = null;
		
		// 优先使用按 streamId 查询的 API
		if (typeof fetchDashboardByStream === 'function') {
			const result = await fetchDashboardByStream(streamId);
			// 处理响应格式：可能是 {success: true, data: {...}} 或直接是数据
			dashboard = result?.data || result;
			console.log(`📊 流 ${streamId} 的 Dashboard 数据 (按流查询):`, dashboard);
		} else {
			// 降级方案：使用全局 Dashboard API（可能不准确）
			console.warn('⚠️ fetchDashboardByStream 不存在，使用全局 Dashboard API');
			dashboard = await fetchDashboard();
			console.log('📊 Dashboard 数据 (全局):', dashboard);
		}
		
		if (dashboard && dashboard.aiStatus) {
			console.log(`✅ 流 ${streamId} 的 AI 状态: ${dashboard.aiStatus}`);
			updateAIControlButtons(dashboard.aiStatus);
			
			// 更新全局状态
			if (window.globalState) {
				window.globalState.aiStatus = dashboard.aiStatus;
			}
		} else {
			// 如果没有 AI 状态，默认为 stopped
			console.log(`⚠️ 流 ${streamId} 没有 AI 状态信息，默认为 stopped`);
			updateAIControlButtons('stopped');
		}
	} catch (error) {
		console.error(`❌ 查询流 ${streamId} 的 AI 状态失败:`, error);
		// 出错时默认为 stopped
		updateAIControlButtons('stopped');
	}
}

// 加载AI内容列表
async function loadAIContentList(page = 1) {
	// 获取当前选择的流ID（如果有流选择器）
	const streamSelect = document.getElementById('ai-stream-select');
	const streamId = streamSelect ? streamSelect.value : null;
	
	// 如果选择了流，显示流信息；否则隐藏
	if (streamId) {
		const streamsResult = await getStreamsList();
		if (streamsResult && streamsResult.streams) {
			const stream = streamsResult.streams.find(s => s.id === streamId);
			if (stream) {
				showAIContentStreamInfo(stream.name || 'Unnamed');
			}
		}
	} else {
		hideAIContentStreamInfo();
	}
	
	const data = await fetchAIContentList(page, 20, null, null, streamId);
	if (!data) {
		const container = document.getElementById('ai-content-list');
		if (container) {
			container.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">请先选择要查看的直播流</div>';
		}
		return;
	}
	
	const container = document.getElementById('ai-content-list');
	if (!container) return;
	
	if (!data.items || data.items.length === 0) {
		container.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">暂无AI内容</div>';
		return;
	}
	
	// 渲染内容列表
	container.innerHTML = data.items.map(item => {
		// 转义HTML特殊字符以防止XSS
		const safeContent = (item.content || item.text || '').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
		const safeId = (item.id || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
		const timestamp = item.timestamp || '';
		
		return `
			<div class="ai-content-item" style="padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 15px; background: white;">
				<div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
					<div style="flex: 1;">
						<span style="display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; background: ${item.position === 'left' ? '#e8f5e9' : '#e3f2fd'}; color: ${item.position === 'left' ? '#4CAF50' : '#2196F3'}; margin-right: 10px;">
							${item.position === 'left' ? '⚔️ 正方' : '🛡️ 反方'}
						</span>
						<span style="color: #999; font-size: 12px;">${timestamp}</span>
						<span style="color: #999; font-size: 12px; margin-left: 10px;">置信度: ${((item.confidence || 0) * 100).toFixed(0)}%</span>
					</div>
					<button class="btn btn-danger btn-sm" onclick="deleteAIContentItem('${safeId}')" style="padding: 4px 12px;">删除</button>
				</div>
				<div style="color: #333; line-height: 1.6; margin-bottom: 10px;">${safeContent}</div>
				<div style="display: flex; gap: 15px; color: #999; font-size: 12px; margin-bottom: 10px;">
					<span>👁️ ${(item.statistics && item.statistics.views) || 0} 查看</span>
					<span>❤️ ${(item.statistics && item.statistics.likes) || 0} 点赞</span>
					<span>💬 ${(item.statistics && item.statistics.comments) || 0} 评论</span>
				</div>
				<div style="display: flex; gap: 10px;">
					<button class="btn btn-danger btn-sm" onclick="deleteAIContentItem('${safeId}')" style="padding: 4px 12px;">删除</button>
					${(item.statistics && item.statistics.comments > 0) ? `<button class="btn btn-primary btn-sm" onclick='openCommentsModal("${safeId}")' style="padding: 4px 12px;">查看评论 (${item.statistics.comments})</button>` : '<button class="btn btn-secondary btn-sm" disabled style="padding: 4px 12px;">暂无评论</button>'}
				</div>
			</div>
		`;
	}).join('');
	
	// 更新分页（新接口返回格式：{ total, page, items }）
	const pagination = document.getElementById('ai-content-pagination');
	if (pagination) {
		const totalPages = data.total ? Math.ceil(data.total / 20) : 0;
		if (totalPages > 1) {
			pagination.style.display = 'block';
			const pageInfo = document.getElementById('ai-page-info');
			if (pageInfo) {
				pageInfo.textContent = `第 ${data.page || page} 页 / 共 ${totalPages} 页`;
			}
		} else {
			pagination.style.display = 'none';
		}
	}
}

// 删除AI内容（全局函数，供HTML onclick调用）
window.deleteAIContentItem = async function(contentId) {
	if (!confirm('确定要删除这条AI内容吗？')) {
		return;
	}
	
	const reason = prompt('请输入删除原因（可选）：');
	const result = await deleteAIContent(contentId, reason || '管理员删除', true);
	if (result) {
		// 重新加载列表
		await loadAIContentList();
	}
};

// ==================== 直播控制事件 ====================

// 立即更新直播状态UI（乐观更新）
function updateLiveStatusUI(isLive) {
	// 更新顶部控制按钮
	const controlLiveBtn = document.getElementById('control-live-btn');
	if (controlLiveBtn) {
		if (isLive) {
			controlLiveBtn.textContent = '停止直播';
			controlLiveBtn.classList.remove('btn-primary', 'btn-success');
			controlLiveBtn.classList.add('btn-danger');
		} else {
			controlLiveBtn.textContent = '开始直播';
			controlLiveBtn.classList.remove('btn-danger');
			controlLiveBtn.classList.add('btn-primary');
		}
	}
	
	// 更新顶部状态显示
	const statusText = document.getElementById('live-status-text');
	if (statusText) {
		statusText.textContent = isLive ? '直播中' : '未开播';
	}
	const liveStatusEl = document.getElementById('live-status');
	if (liveStatusEl) {
		liveStatusEl.textContent = isLive ? '🟢 直播中' : '⚪ 未开播';
	}
	
	// 更新直播控制页面按钮
	const adminStartLiveBtn = document.getElementById('admin-start-live-btn');
	const adminStopLiveBtn = document.getElementById('admin-stop-live-btn');
	if (adminStartLiveBtn && adminStopLiveBtn) {
		adminStartLiveBtn.disabled = isLive;
		adminStopLiveBtn.disabled = !isLive;
	}
	
	// 更新直播控制页面状态显示
	const liveControlStatusEl = document.getElementById('live-control-status');
	if (liveControlStatusEl) {
		if (isLive) {
			liveControlStatusEl.innerHTML = '<span style="color: #4CAF50;">🟢 直播中</span>';
		} else {
			liveControlStatusEl.innerHTML = '<span style="color: #999;">⚪ 未开播</span>';
			// 隐藏直播流信息
			const streamInfoEl = document.getElementById('live-stream-info');
			if (streamInfoEl) {
				streamInfoEl.style.display = 'none';
			}
		}
	}
	
	// 更新全局状态
	if (window.globalState) {
		window.globalState.isLive = isLive;
	}
}

function initLiveControlEvents() {
	// 顶部直播控制按钮
	const controlLiveBtn = document.getElementById('control-live-btn');
	if (controlLiveBtn) {
		controlLiveBtn.addEventListener('click', async () => {
			// 先从服务器获取最新状态，确保状态同步
			try {
				const dashboard = await fetchDashboard();
				if (!dashboard) {
					console.error('获取直播状态失败');
					return;
				}
				
				const isLive = dashboard.isLive || false;
				
				// 更新 globalState 为最新状态
				if (window.globalState) {
					window.globalState.isLive = isLive;
				}
				
				if (isLive) {
					// 停止直播
					if (!confirm('确定要停止直播吗？')) {
						return;
					}
					
					// 立即更新UI（乐观更新）
					updateLiveStatusUI(false);
					
					try {
						// 从 dashboard 获取当前流ID
						const dashboard = await fetchDashboard();
						const streamId = dashboard?.streamId || null;
						
						const result = await stopLive(streamId, true, true);
						// 判断成功：有 success 为 true，或者有 status === 'stopped'，或者 result 不为空且没有错误字段
						const isSuccess = result && (
							result.success === true || 
							result.status === 'stopped' ||
							result.data?.status === 'stopped' ||
							(!result.error && !result.message)
						);
						
						if (!isSuccess) {
							// API失败，回滚UI
							updateLiveStatusUI(true);
							console.error('停止直播失败:', result);
							return;
						}
						
						console.log('✅ 停止直播成功:', result);
						
						// 清理AI内容刷新定时器
						if (window.aiContentRefreshTimer) {
							clearInterval(window.aiContentRefreshTimer);
							window.aiContentRefreshTimer = null;
							console.log('🧹 已清理AI内容刷新定时器');
						}
						
						// 立即刷新所有流状态列表
						if (typeof loadAllStreamsStatus === 'function') {
							loadAllStreamsStatus();
						}
						
						// 刷新 dashboard 和状态列表
						setTimeout(() => {
							if (typeof loadDashboard === 'function') {
								loadDashboard();
							}
							if (typeof loadAllStreamsStatus === 'function') {
								loadAllStreamsStatus();
							}
						}, 1000); // 延迟1秒，确保后端状态已更新
					} catch (error) {
						// API异常，回滚UI
						updateLiveStatusUI(true);
						console.error('停止直播失败:', error);
					}
				} else {
					// 开始直播
					// 获取选中的直播流ID（从直播控制页面）
					const streamSelect = document.getElementById('stream-select');
					const streamId = streamSelect?.value || null; // 如果未选择，使用默认直播流
					const autoStartAI = confirm('是否同时启动AI识别？');
					
					// 立即更新UI（乐观更新）
					updateLiveStatusUI(true);
					
					try {
						const result = await startLive(streamId, autoStartAI, true);
						// 判断成功：有 success 为 true，或者有 streamUrl 或 status === 'started'
						const isSuccess = result && (
							result.success === true || 
							result.streamUrl || 
							result.status === 'started' ||
							result.data?.streamUrl ||
							result.data?.status === 'started'
						);
						
						if (!isSuccess) {
							// API失败，回滚UI
							updateLiveStatusUI(false);
							console.error('开始直播失败:', result);
							return;
						}
						
						console.log('✅ 开始直播成功:', result);
						
						// 更新直播流信息（如果API返回了）
						if (result.streamUrl || result.data?.streamUrl) {
							const streamUrl = result.streamUrl || result.data?.streamUrl;
							const streamInfoEl = document.getElementById('live-stream-info');
							if (streamInfoEl) {
								streamInfoEl.style.display = 'block';
								const streamIdEl = document.getElementById('live-stream-id');
								const streamUrlEl = document.getElementById('live-stream-url');
								const startTimeEl = document.getElementById('live-start-time');
								if (streamIdEl) streamIdEl.textContent = result.liveId || result.data?.liveId || '-';
								if (streamUrlEl) streamUrlEl.textContent = streamUrl || '-';
								if (startTimeEl) startTimeEl.textContent = result.startTime || result.data?.startTime || '-';
							}
						}
						
						// 如果自动启动了AI，设置定时刷新AI内容
						if (autoStartAI) {
							setTimeout(() => {
								if (typeof loadAIContentList === 'function') {
									console.log('📡 AI已自动启动，开始订阅AI内容更新...');
									loadAIContentList(1);
								}
								
								// 设置定时刷新AI内容列表
								if (window.aiContentRefreshTimer) {
									clearInterval(window.aiContentRefreshTimer);
								}
								window.aiContentRefreshTimer = setInterval(() => {
									if (typeof loadAIContentList === 'function') {
										loadAIContentList(1);
									}
								}, 5000); // 每5秒刷新一次
							}, 2000); // 延迟2秒，等待后端ASR服务启动
						}
						
						// 立即刷新所有流状态列表
						if (typeof loadAllStreamsStatus === 'function') {
							loadAllStreamsStatus();
						}
						
						// 刷新 dashboard 和状态列表
						setTimeout(() => {
							if (typeof loadDashboard === 'function') {
								loadDashboard();
							}
							if (typeof loadAllStreamsStatus === 'function') {
								loadAllStreamsStatus();
							}
						}, 1000); // 延迟1秒，确保后端状态已更新
					} catch (error) {
						// API异常，回滚UI
						updateLiveStatusUI(false);
						console.error('开始直播失败:', error);
					}
				}
			} catch (error) {
				console.error('获取直播状态失败:', error);
			}
		});
	}
	
	// 直播控制页面的开始/停止按钮
	const adminStartLiveBtn = document.getElementById('admin-start-live-btn');
	const adminStopLiveBtn = document.getElementById('admin-stop-live-btn');
	
	if (adminStartLiveBtn) {
		adminStartLiveBtn.addEventListener('click', async () => {
			// 在函数开始就保存按钮文本，确保 finally 块中可以使用
			const originalText = adminStartLiveBtn.textContent;
			
			try {
				const autoStartAI = document.getElementById('auto-start-ai-checkbox')?.checked || false;
				// 获取选中的直播流ID（根据接口文档，streamId是必填的）
				const streamSelect = document.getElementById('stream-select');
				const streamId = streamSelect?.value?.trim() || null;
				
				// 验证 streamId 是否存在
				if (!streamId) {
					alert('请先选择一个直播流！\n\n请在"选择直播流"下拉框中选择一个直播流。');
					return;
				}
				
				// 获取选中的直播流信息用于提示
				const selectedStream = window.liveSetupStreams?.find(s => s.id === streamId);
				const streamName = selectedStream?.name || streamId;
				
				if (!confirm(`确定要开始直播吗？\n\n将使用直播流："${streamName}"\n${autoStartAI ? '（将自动启动AI识别）' : ''}\n\n💡 提示：可以同时开启多个直播流`)) {
					return;
				}
				
				// 禁用按钮，防止重复点击
				adminStartLiveBtn.disabled = true;
				adminStartLiveBtn.textContent = '启动中...';
				
				// 立即更新UI（乐观更新）
				updateLiveStatusUI(true);
				
				// 调用接口（根据接口文档：/api/v1/admin/live/start）
				const result = await startLive(streamId, autoStartAI, true);
				
				// 判断成功：根据接口文档，成功响应格式为 {success: true, data: {...}}
				// 兼容处理：如果返回的数据直接包含 status: 'started' 或 streamUrl，也认为是成功
				const isSuccess = result && (
					result.success === true ||
					(result.data && (result.data.status === 'started' || result.data.streamUrl)) ||
					(result.status === 'started' || result.streamUrl) // 兼容直接返回 {status: 'started', ...}
				);
				
				if (!isSuccess) {
					// API失败，回滚UI
					updateLiveStatusUI(false);
					const errorMsg = result?.detail || result?.message || result?.error || '未知错误';
					console.error('❌ 开始直播失败:', result);
					if (typeof showToast === 'function') {
						showToast('开始直播失败：' + errorMsg, 'error');
					} else {
						alert('开始直播失败：' + errorMsg);
					}
					return;
				}
				
				console.log('✅ 开始直播成功:', result);
				
				// 显示成功提示
				if (typeof showToast === 'function') {
					showToast('直播已开始！', 'success');
				}
				
				// 更新全局状态
				if (window.globalState) {
					window.globalState.isLive = true;
					window.globalState.liveId = streamId;
				}
				
				// 确保UI状态更新为已开播（允许停止直播）
				updateLiveStatusUI(true);
				
				// 更新直播流信息（如果API返回了）
				const responseData = result.data || result;
				if (responseData.streamUrl || responseData.liveId) {
					const streamUrl = responseData.streamUrl;
					const streamInfoEl = document.getElementById('live-stream-info');
					if (streamInfoEl) {
						streamInfoEl.style.display = 'block';
						const streamIdEl = document.getElementById('live-stream-id');
						const streamUrlEl = document.getElementById('live-stream-url');
						const startTimeEl = document.getElementById('live-start-time');
						if (streamIdEl) streamIdEl.textContent = responseData.liveId || streamId || '-';
						if (streamUrlEl) streamUrlEl.textContent = streamUrl || '-';
						if (startTimeEl) startTimeEl.textContent = responseData.startTime || new Date().toLocaleString();
					}
				}
				
				// 如果自动启动了AI，设置定时刷新AI内容
				if (autoStartAI) {
					setTimeout(() => {
						if (typeof loadAIContentList === 'function') {
							console.log('📡 AI已自动启动，开始订阅AI内容更新...');
							loadAIContentList(1);
						}
						
						// 设置定时刷新AI内容列表
						if (window.aiContentRefreshTimer) {
							clearInterval(window.aiContentRefreshTimer);
						}
						window.aiContentRefreshTimer = setInterval(() => {
							if (typeof loadAIContentList === 'function') {
								loadAIContentList(1);
							}
						}, 5000); // 每5秒刷新一次
					}, 2000); // 延迟2秒，等待后端ASR服务启动
				}
				
				// 立即刷新所有流状态列表
				if (typeof loadAllStreamsStatus === 'function') {
					loadAllStreamsStatus();
				}
				
				// 刷新 dashboard 和状态列表（确保状态同步）
				// 注意：延迟刷新，但不要覆盖我们刚设置的本地状态
				setTimeout(() => {
					// 先刷新 dashboard，但不立即更新UI（让 loadLiveSetup 自己处理）
					if (typeof loadDashboard === 'function') {
						loadDashboard();
					}
					if (typeof loadAllStreamsStatus === 'function') {
						loadAllStreamsStatus();
					}
					// 延迟刷新直播设置页面，给后端更多时间更新状态
					setTimeout(() => {
						if (typeof loadLiveSetup === 'function') {
							loadLiveSetup();
						}
					}, 500); // 再延迟500ms，确保后端状态已更新
				}, 1500); // 延迟1.5秒，确保后端状态已更新
			} catch (error) {
				// API异常，回滚UI
				updateLiveStatusUI(false);
				console.error('❌ 开始直播失败:', error);
				const errorMsg = error.message || '网络错误或服务器异常';
				if (typeof showToast === 'function') {
					showToast('开始直播失败：' + errorMsg, 'error');
				} else {
					alert('开始直播失败：' + errorMsg);
				}
			} finally {
				// 延迟恢复按钮状态，确保状态同步完成
				setTimeout(() => {
					if (adminStartLiveBtn) {
						// 使用 updateLiveStatusUI 来确保按钮状态正确
						// 这会根据实际的直播状态来设置按钮
						if (typeof updateLiveStatusUI === 'function') {
							// 先尝试从全局状态获取
							const isLive = window.globalState?.isLive || false;
							updateLiveStatusUI(isLive);
						}
						// 恢复按钮文本
						adminStartLiveBtn.textContent = originalText || '🚀 开始直播';
					}
				}, 500);
			}
		});
	}
	
	if (adminStopLiveBtn) {
		adminStopLiveBtn.addEventListener('click', async () => {
			// 在函数开始就保存按钮文本，确保 finally 块中可以使用
			const originalText = adminStopLiveBtn.textContent;
			
			try {
				// 获取选中的直播流ID（根据接口文档，streamId是必填的）
				// 必须从选择框中选择，不支持自动获取
				const streamSelect = document.getElementById('stream-select');
				const streamId = streamSelect?.value?.trim() || null;
				
				// 验证 streamId 是否存在
				if (!streamId) {
					alert('请先选择一个直播流！\n\n请在"选择直播流"下拉框中选择要停止的直播流。');
					return;
				}
				
				// 获取直播流信息用于提示
				const selectedStream = window.liveSetupStreams?.find(s => s.id === streamId);
				const streamName = selectedStream?.name || streamId;
				
				if (!confirm(`确定要停止直播吗？\n\n将停止直播流："${streamName}"`)) {
					return;
				}
				
				// 禁用按钮，防止重复点击
				adminStopLiveBtn.disabled = true;
				adminStopLiveBtn.textContent = '停止中...';
				
				// 立即更新UI（乐观更新）
				updateLiveStatusUI(false);
				
				// 调用接口（根据接口文档：/api/v1/admin/live/stop）
				const result = await stopLive(streamId, true, true);
				
				// 判断成功：根据接口文档，成功响应格式为 {success: true, data: {status: "stopped"}}
				// 兼容处理：如果返回的数据直接包含 status: 'stopped'，也认为是成功
				const isSuccess = result && (
					result.success === true ||
					(result.data && result.data.status === 'stopped') ||
					(result.status === 'stopped') // 兼容直接返回 {status: 'stopped', ...}
				);
				
				if (!isSuccess) {
					// API失败，回滚UI
					updateLiveStatusUI(true);
					const errorMsg = result?.detail || result?.message || result?.error || '未知错误';
					console.error('❌ 停止直播失败:', result);
					if (typeof showToast === 'function') {
						showToast('停止直播失败：' + errorMsg, 'error');
					} else {
						alert('停止直播失败：' + errorMsg);
					}
					return;
				}
				
				console.log('✅ 停止直播成功:', result);
				
				// 显示成功提示
				const responseData = result.data || result;
				const duration = responseData.duration;
				if (typeof showToast === 'function') {
					const durationText = duration ? `（本次直播时长：${Math.floor(duration / 60)}分${duration % 60}秒）` : '';
					showToast('直播已停止' + durationText, 'success');
				}
				
				// 更新全局状态
				if (window.globalState) {
					window.globalState.isLive = false;
					window.globalState.liveId = null;
				}
				
				// 记录停止时间，防止误触发自动开始
				window.lastStopLiveTime = Date.now();
				
				// 确保UI状态更新为未开播（允许开始新直播）
				updateLiveStatusUI(false);
				
				// 隐藏直播流信息
				const streamInfoEl = document.getElementById('live-stream-info');
				if (streamInfoEl) {
					streamInfoEl.style.display = 'none';
				}
				
				// 清理AI内容刷新定时器
				if (window.aiContentRefreshTimer) {
					clearInterval(window.aiContentRefreshTimer);
					window.aiContentRefreshTimer = null;
					console.log('🧹 已清理AI内容刷新定时器');
				}
				
				// 立即刷新所有流状态列表
				if (typeof loadAllStreamsStatus === 'function') {
					loadAllStreamsStatus();
				}
				
				// 刷新 dashboard 和状态列表（确保状态同步）
				// 注意：延迟刷新，但不要覆盖我们刚设置的本地状态
				setTimeout(() => {
					// 先刷新 dashboard，但不立即更新UI（让 loadLiveSetup 自己处理）
					if (typeof loadDashboard === 'function') {
						loadDashboard();
					}
					if (typeof loadAllStreamsStatus === 'function') {
						loadAllStreamsStatus();
					}
					// 延迟刷新直播设置页面，给后端更多时间更新状态
					setTimeout(() => {
						if (typeof loadLiveSetup === 'function') {
							loadLiveSetup();
						}
					}, 500); // 再延迟500ms，确保后端状态已更新
				}, 1500); // 延迟1.5秒，确保后端状态已更新
			} catch (error) {
				// API异常，回滚UI
				updateLiveStatusUI(true);
				console.error('❌ 停止直播失败:', error);
				const errorMsg = error.message || '网络错误或服务器异常';
				if (typeof showToast === 'function') {
					showToast('停止直播失败：' + errorMsg, 'error');
				} else {
					alert('停止直播失败：' + errorMsg);
				}
			} finally {
				// 延迟恢复按钮状态，确保状态同步完成
				setTimeout(() => {
					if (adminStopLiveBtn) {
						// 使用 updateLiveStatusUI 来确保按钮状态正确
						// 这会根据实际的直播状态来设置按钮
						if (typeof updateLiveStatusUI === 'function') {
							// 先尝试从全局状态获取
							const isLive = window.globalState?.isLive || false;
							updateLiveStatusUI(isLive);
						}
						// 恢复按钮文本
						adminStopLiveBtn.textContent = originalText || '⏹️ 停止直播';
					}
				}, 500);
			}
		});
	}
}

// ==================== AI直播流列表加载 ====================

/**
 * 加载AI控制的直播流列表
 */
async function loadAIStreamsList() {
	const aiStreamSelect = document.getElementById('ai-stream-select');
	if (!aiStreamSelect) return;
	
	try {
		console.log('📡 加载AI直播流列表...');
		
		// 保存当前选中的值
		const currentValue = aiStreamSelect.value;
		
		// 获取直播流列表
		const result = await getStreamsList();
		
		if (result && result.streams) {
			// 清空现有选项（保留默认选项）
			aiStreamSelect.innerHTML = '<option value="">请选择要操作的直播流</option>';
			
			// 添加所有启用的直播流
			const enabledStreams = result.streams.filter(stream => stream.enabled !== false);
			
			if (enabledStreams.length === 0) {
				aiStreamSelect.innerHTML = '<option value="">暂无可用的直播流</option>';
				console.warn('⚠️ 没有可用的直播流');
				return;
			}
			
			enabledStreams.forEach(stream => {
				const option = document.createElement('option');
				option.value = stream.id;
				option.textContent = `${stream.name} (${stream.type.toUpperCase()})`;
				aiStreamSelect.appendChild(option);
			});
			
			// 恢复之前选中的值
			if (currentValue) {
				aiStreamSelect.value = currentValue;
			}
			
			console.log(`✅ AI直播流列表已加载（${enabledStreams.length} 个）`);
		} else {
			console.error('❌ 获取直播流列表失败:', result);
			aiStreamSelect.innerHTML = '<option value="">加载失败，请刷新</option>';
		}
	} catch (error) {
		console.error('❌ 加载AI直播流列表失败:', error);
		aiStreamSelect.innerHTML = '<option value="">加载失败，请刷新</option>';
	}
}

/**
 * 显示AI内容当前流信息
 */
function showAIContentStreamInfo(streamName) {
	const infoEl = document.getElementById('ai-content-stream-info');
	const nameEl = document.getElementById('ai-content-current-stream-name');
	
	if (infoEl) infoEl.style.display = 'block';
	if (nameEl) nameEl.textContent = streamName;
}

/**
 * 隐藏AI内容当前流信息
 */
function hideAIContentStreamInfo() {
	const infoEl = document.getElementById('ai-content-stream-info');
	if (infoEl) infoEl.style.display = 'none';
}

// ==================== 观看人数管理 ====================

/**
 * 更新Dashboard页面的观看人数显示
 * @param {string} streamId - 直播流ID
 * @param {number} count - 观看人数
 * @param {string} action - 触发动作
 */
function updateViewersDisplay(streamId, count, action) {
	// 在Dashboard页面更新观看人数
	const viewersCountEl = document.getElementById('viewers-count');
	const activeUsersEl = document.getElementById('active-users');
	
	if (viewersCountEl) {
		viewersCountEl.textContent = count;
		
		// 添加动画效果
		viewersCountEl.classList.add('highlight');
		setTimeout(() => {
			viewersCountEl.classList.remove('highlight');
		}, 1000);
	}
	
	// 同时更新活跃用户数（假设观看人数等于活跃用户数）
	if (activeUsersEl) {
		activeUsersEl.textContent = count;
		
		// 添加动画效果
		activeUsersEl.classList.add('highlight');
		setTimeout(() => {
			activeUsersEl.classList.remove('highlight');
		}, 1000);
	}
	
	console.log(`✅ 已更新观看人数显示: 流 ${streamId}, 人数 ${count}`);
}

/**
 * 更新多直播总览中某个流的观看人数
 * @param {string} streamId - 直播流ID
 * @param {number} count - 观看人数
 */
function updateStreamViewersInList(streamId, count) {
	// 在多直播总览页面更新指定流的观看人数
	const streamCard = document.querySelector(`[data-stream-id="${streamId}"]`);
	if (!streamCard) {
		console.log(`⚠️ 未找到流 ${streamId} 的卡片元素`);
		return;
	}
	
	const viewersEl = streamCard.querySelector('.stream-viewers, .viewers-count');
	if (viewersEl) {
		viewersEl.textContent = `${count} 人观看`;
		
		// 添加动画效果
		viewersEl.classList.add('highlight');
		setTimeout(() => {
			viewersEl.classList.remove('highlight');
		}, 1000);
		
		console.log(`✅ 已更新流 ${streamId} 的观看人数: ${count}`);
	}
}

/**
 * 初始化观看人数显示
 * @param {string} streamId - 直播流ID（可选）
 */
async function initViewersCount(streamId = null) {
	try {
		let result;
		
		if (streamId) {
			// 获取指定流的观看人数
			result = await getViewersCount(streamId);
			if (result?.success && result.data) {
				updateViewersDisplay(streamId, result.data.viewers, 'manual_broadcast');
			}
		} else {
			// 获取所有流的观看人数
			result = await getAllViewersCount();
			if (result?.success && result.data?.streams) {
				// 更新多直播总览中的观看人数
				Object.entries(result.data.streams).forEach(([sid, count]) => {
					updateStreamViewersInList(sid, count);
				});
			}
		}
	} catch (error) {
		console.error('❌ 初始化观看人数失败:', error);
	}
}

// ==================== 辩论流程管理事件 ====================

/**
 * 初始化辩论流程管理事件
 */
function initDebateFlowEvents() {
	console.log('🎯 初始化辩论流程事件处理器...');
	
	// 加载流列表
	loadDebateFlowStreamsList();
	
	// 刷新流列表按钮
	const refreshStreamsBtn = document.getElementById('debate-flow-refresh-streams-btn');
	if (refreshStreamsBtn) {
		refreshStreamsBtn.addEventListener('click', () => {
			loadDebateFlowStreamsList();
		});
	}
	
	// 流选择变化时，加载对应流的流程配置
	const streamSelect = document.getElementById('debate-flow-stream-select');
	if (streamSelect) {
		streamSelect.addEventListener('change', async (e) => {
			const streamId = e.target.value;
			if (streamId) {
				await loadDebateFlowByStream(streamId);
			} else {
				clearDebateFlowDisplay();
			}
		});
	}
	
	// 添加环节按钮
	const addSegmentBtn = document.getElementById('add-segment-btn');
	if (addSegmentBtn) {
		addSegmentBtn.addEventListener('click', addDebateSegment);
	}
	
	// 保存流程配置按钮
	const saveFlowBtn = document.getElementById('save-debate-flow-btn');
	if (saveFlowBtn) {
		saveFlowBtn.addEventListener('click', async () => {
			const streamId = document.getElementById('debate-flow-stream-select')?.value;
			if (!streamId) {
				alert('请先选择要管理的直播流');
				return;
			}
			await saveDebateFlowConfig(streamId);
		});
	}

	// 大屏流程控制按钮
	document.querySelectorAll('.debate-flow-control-btn').forEach((btn) => {
		btn.addEventListener('click', async () => {
			const action = btn.dataset.action;
			const streamId = document.getElementById('debate-flow-stream-select')?.value;
			if (!streamId) {
				alert('请先选择要控制的直播流');
				return;
			}
			await sendDebateFlowControlFromPage(streamId, action, btn);
		});
	});
}

async function sendDebateFlowControlFromPage(streamId, action, btn) {
	const startIndexInput = document.getElementById('debate-flow-start-index');
	const segmentIndex = Math.max(0, (parseInt(startIndexInput?.value, 10) || 1) - 1);
	const originalHtml = btn.innerHTML;
	try {
		btn.disabled = true;
		btn.textContent = '发送中...';
		const result = await sendDebateFlowControl(streamId, action, segmentIndex);
		if (result) {
			console.log(`✅ 流程控制命令已发送: ${action}`, result);
		}
	} catch (error) {
		console.error('❌ 流程控制命令发送失败:', error);
		alert('流程控制命令发送失败：' + error.message);
	} finally {
		btn.disabled = false;
		btn.innerHTML = originalHtml;
	}
}

/**
 * 加载流列表到辩论流程选择器
 */
async function loadDebateFlowStreamsList() {
	try {
		const streamSelect = document.getElementById('debate-flow-stream-select');
		if (!streamSelect) return;
		
		const streamsResult = await getStreamsList();
		if (!streamsResult || !streamsResult.streams) {
			console.warn('⚠️ 无法获取流列表');
			return;
		}
		
		const currentValue = streamSelect.value;
		streamSelect.innerHTML = '<option value="">请选择要管理的直播流</option>';
		
		streamsResult.streams.forEach(stream => {
			const option = document.createElement('option');
			option.value = stream.id;
			option.textContent = `${stream.name} (${stream.type || 'HLS'})`;
			streamSelect.appendChild(option);
		});
		
		// 恢复之前的选择
		if (currentValue) {
			streamSelect.value = currentValue;
			const event = new Event('change', { bubbles: true });
			streamSelect.dispatchEvent(event);
		}
	} catch (error) {
		console.error('❌ 加载流列表失败:', error);
	}
}

/**
 * 加载指定流的辩论流程配置
 */
async function loadDebateFlowByStream(streamId) {
	try {
		const container = document.getElementById('debate-segments-container');
		if (!container) return;
		
		container.innerHTML = '<div style="text-align: center; padding: 20px;"><span style="color: #999;">加载中...</span></div>';
		
		// 从 API 获取流程配置
		const result = await getDebateFlowConfig(streamId);
		const segments = result?.segments || result?.flow || result?.data?.segments || result?.data?.flow;
		
		if (!Array.isArray(segments)) {
			console.warn('⚠️ 无法获取流程配置');
			container.innerHTML = '<div style="text-align: center; padding: 20px; color: #999;">暂无流程配置，可点击"添加环节"创建新环节</div>';
			return;
		}
		
		// 显示当前流名称
		const streamSelect = document.getElementById('debate-flow-stream-select');
		const currentStream = streamSelect.options[streamSelect.selectedIndex];
		if (currentStream) {
			const streamInfo = document.getElementById('debate-flow-current-stream-info');
			const streamName = document.getElementById('debate-flow-current-stream-name');
			streamName.textContent = currentStream.textContent;
			streamInfo.style.display = 'block';
		}
		
		// 渲染环节
		renderDebateSegments(segments);
	} catch (error) {
		console.error('❌ 加载流程配置失败:', error);
		const container = document.getElementById('debate-segments-container');
		if (container) {
			container.innerHTML = '<div style="text-align: center; padding: 20px; color: #e74c3c;">加载流程配置失败</div>';
		}
	}
}

/**
 * 渲染辩论环节列表
 */
function renderDebateSegments(segments) {
	const container = document.getElementById('debate-segments-container');
	if (!container) return;
	
	if (!segments || segments.length === 0) {
		container.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">暂无环节，可点击"添加环节"创建新环节</div>';
		return;
	}
	
	container.innerHTML = '';
	
	segments.forEach((segment, index) => {
		const segmentEl = document.createElement('div');
		segmentEl.className = 'debate-segment-item';
		segmentEl.dataset.segmentIndex = index;
		segmentEl.style.cssText = `
			background: #f8f9fa;
			padding: 20px;
			border-radius: 8px;
			border: 1px solid #e9ecef;
			display: flex;
			gap: 15px;
			align-items: flex-start;
		`;
		
		segmentEl.innerHTML = `
			<div style="flex: 1; min-width: 0;">
				<div style="display: flex; align-items: center; margin-bottom: 10px;">
					<span style="display: inline-block; width: 30px; height: 30px; background: #3498db; color: white; border-radius: 50%; text-align: center; line-height: 30px; font-weight: bold; margin-right: 10px; flex-shrink: 0;">${index + 1}</span>
					<input type="text" class="segment-name-input form-input" placeholder="环节名称（如：正方发言）" value="${segment.name || ''}" style="flex: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
				</div>
				<div style="display: flex; gap: 10px; align-items: center;">
					<label style="display: flex; align-items: center; gap: 5px; font-size: 14px; color: #666;">
						时长（秒）:
						<input type="number" class="segment-duration-input form-input" placeholder="时长（秒）" value="${segment.duration || 180}" min="10" step="10" style="width: 80px; padding: 6px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
					</label>
					<label style="display: flex; align-items: center; gap: 5px; font-size: 14px; color: #666;">
						方向:
						<select class="segment-side-input form-select" style="padding: 6px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
							<option value="left" ${segment.side === 'left' ? 'selected' : ''}>正方</option>
							<option value="right" ${segment.side === 'right' ? 'selected' : ''}>反方</option>
							<option value="both" ${segment.side === 'both' ? 'selected' : ''}>双方</option>
						</select>
					</label>
				</div>
			</div>
			<button class="btn btn-danger btn-sm delete-segment-btn" style="padding: 8px 12px; display: flex; align-items: center; gap: 6px; flex-shrink: 0;">
				<span style="font-size: 16px;">🗑️</span>
				删除
			</button>
		`;
		
		// 删除按钮事件
		const deleteBtn = segmentEl.querySelector('.delete-segment-btn');
		if (deleteBtn) {
			deleteBtn.addEventListener('click', () => {
				if (confirm('确定要删除这个环节吗？')) {
					segmentEl.remove();
				}
			});
		}
		
		container.appendChild(segmentEl);
	});
}

/**
 * 添加新的辩论环节
 */
function addDebateSegment() {
	const container = document.getElementById('debate-segments-container');
	if (!container) return;
	
	// 如果容器是空提示，先清空
	if (container.innerHTML.includes('暂无环节')) {
		container.innerHTML = '';
	}
	
	const items = container.querySelectorAll('.debate-segment-item');
	const index = items.length;
	
	const segmentEl = document.createElement('div');
	segmentEl.className = 'debate-segment-item';
	segmentEl.dataset.segmentIndex = index;
	segmentEl.style.cssText = `
		background: #f8f9fa;
		padding: 20px;
		border-radius: 8px;
		border: 1px solid #e9ecef;
		display: flex;
		gap: 15px;
		align-items: flex-start;
	`;
	
	segmentEl.innerHTML = `
		<div style="flex: 1; min-width: 0;">
			<div style="display: flex; align-items: center; margin-bottom: 10px;">
				<span style="display: inline-block; width: 30px; height: 30px; background: #3498db; color: white; border-radius: 50%; text-align: center; line-height: 30px; font-weight: bold; margin-right: 10px; flex-shrink: 0;">${index + 1}</span>
				<input type="text" class="segment-name-input form-input" placeholder="环节名称（如：正方发言）" style="flex: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
			</div>
			<div style="display: flex; gap: 10px; align-items: center;">
				<label style="display: flex; align-items: center; gap: 5px; font-size: 14px; color: #666;">
					时长（秒）:
					<input type="number" class="segment-duration-input form-input" placeholder="时长（秒）" value="180" min="10" step="10" style="width: 80px; padding: 6px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
				</label>
				<label style="display: flex; align-items: center; gap: 5px; font-size: 14px; color: #666;">
					方向:
					<select class="segment-side-input form-select" style="padding: 6px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
						<option value="left">正方</option>
						<option value="right">反方</option>
						<option value="both" selected>双方</option>
					</select>
				</label>
			</div>
		</div>
		<button class="btn btn-danger btn-sm delete-segment-btn" style="padding: 8px 12px; display: flex; align-items: center; gap: 6px; flex-shrink: 0;">
			<span style="font-size: 16px;">🗑️</span>
			删除
		</button>
	`;
	
	// 删除按钮事件
	const deleteBtn = segmentEl.querySelector('.delete-segment-btn');
	if (deleteBtn) {
		deleteBtn.addEventListener('click', () => {
			if (confirm('确定要删除这个环节吗？')) {
				segmentEl.remove();
			}
		});
	}
	
	container.appendChild(segmentEl);
}

/**
 * 保存辩论流程配置
 */
async function saveDebateFlowConfig(streamId) {
	try {
		const container = document.getElementById('debate-segments-container');
		const items = container.querySelectorAll('.debate-segment-item');
		
		if (items.length === 0) {
			alert('请至少添加一个环节');
			return;
		}
		
		// 收集所有环节数据
		const segments = [];
		items.forEach((item, index) => {
			const name = item.querySelector('.segment-name-input')?.value || `环节 ${index + 1}`;
			const duration = parseInt(item.querySelector('.segment-duration-input')?.value) || 180;
			const side = item.querySelector('.segment-side-input')?.value || 'both';
			
			if (duration < 10) {
				alert('时长不能少于10秒');
				return;
			}
			
			segments.push({
				name,
				duration,
				side
			});
		});
		
		if (segments.length === 0) return;
		
		// 调用 API 保存
		const result = await saveDebateFlowConfigAPI(streamId, segments);
		
		if (result) {
			alert('✅ 流程配置保存成功！\n\n配置已同步到大屏幕。');
			// 刷新显示
			await loadDebateFlowByStream(streamId);
		}
	} catch (error) {
		console.error('❌ 保存流程配置失败:', error);
		alert('❌ 保存流程配置失败：' + error.message);
	}
}

/**
 * 清空流程显示
 */
function clearDebateFlowDisplay() {
	const container = document.getElementById('debate-segments-container');
	if (container) {
		container.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">选择直播流后，将显示该流的辩论流程</div>';
	}
	
	const streamInfo = document.getElementById('debate-flow-current-stream-info');
	if (streamInfo) {
		streamInfo.style.display = 'none';
	}
}

/**
 * 快速套用模板
 */
function applyTemplate(templateType) {
	const streamId = document.getElementById('debate-flow-stream-select')?.value;
	if (!streamId) {
		alert('请先选择要管理的直播流');
		return;
	}
	
	const templates = {
		standard: [
			{ name: '正方发言', duration: 180, side: 'left' },
			{ name: '反方质问', duration: 120, side: 'right' },
			{ name: '反方发言', duration: 180, side: 'right' },
			{ name: '正方质问', duration: 120, side: 'left' },
			{ name: '自由辩论', duration: 300, side: 'both' },
			{ name: '正方总结', duration: 120, side: 'left' },
			{ name: '反方总结', duration: 120, side: 'right' }
		],
		quick: [
			{ name: '正方发言', duration: 120, side: 'left' },
			{ name: '反方发言', duration: 120, side: 'right' },
			{ name: '自由辩论', duration: 180, side: 'both' },
			{ name: '正方总结', duration: 60, side: 'left' },
			{ name: '反方总结', duration: 60, side: 'right' }
		],
		extended: [
			{ name: '开场陈述', duration: 300, side: 'both' },
			{ name: '正方发言', duration: 240, side: 'left' },
			{ name: '反方质问', duration: 180, side: 'right' },
			{ name: '反方发言', duration: 240, side: 'right' },
			{ name: '正方质问', duration: 180, side: 'left' },
			{ name: '自由辩论', duration: 600, side: 'both' },
			{ name: '正方总结', duration: 180, side: 'left' },
			{ name: '反方总结', duration: 180, side: 'right' },
			{ name: '评委评议', duration: 300, side: 'both' }
		]
	};
	
	const template = templates[templateType];
	if (!template) return;
	
	if (!confirm('确定要套用此模板吗？这会覆盖当前的流程配置。')) {
		return;
	}
	
	const container = document.getElementById('debate-segments-container');
	container.innerHTML = '';
	
	template.forEach((segment, index) => {
		const segmentEl = document.createElement('div');
		segmentEl.className = 'debate-segment-item';
		segmentEl.dataset.segmentIndex = index;
		segmentEl.style.cssText = `
			background: #f8f9fa;
			padding: 20px;
			border-radius: 8px;
			border: 1px solid #e9ecef;
			display: flex;
			gap: 15px;
			align-items: flex-start;
		`;
		
		segmentEl.innerHTML = `
			<div style="flex: 1; min-width: 0;">
				<div style="display: flex; align-items: center; margin-bottom: 10px;">
					<span style="display: inline-block; width: 30px; height: 30px; background: #3498db; color: white; border-radius: 50%; text-align: center; line-height: 30px; font-weight: bold; margin-right: 10px; flex-shrink: 0;">${index + 1}</span>
					<input type="text" class="segment-name-input form-input" placeholder="环节名称" value="${segment.name}" style="flex: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
				</div>
				<div style="display: flex; gap: 10px; align-items: center;">
					<label style="display: flex; align-items: center; gap: 5px; font-size: 14px; color: #666;">
						时长（秒）:
						<input type="number" class="segment-duration-input form-input" placeholder="时长（秒）" value="${segment.duration}" min="10" step="10" style="width: 80px; padding: 6px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
					</label>
					<label style="display: flex; align-items: center; gap: 5px; font-size: 14px; color: #666;">
						方向:
						<select class="segment-side-input form-select" style="padding: 6px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
							<option value="left" ${segment.side === 'left' ? 'selected' : ''}>正方</option>
							<option value="right" ${segment.side === 'right' ? 'selected' : ''}>反方</option>
							<option value="both" ${segment.side === 'both' ? 'selected' : ''}>双方</option>
						</select>
					</label>
				</div>
			</div>
			<button class="btn btn-danger btn-sm delete-segment-btn" style="padding: 8px 12px; display: flex; align-items: center; gap: 6px; flex-shrink: 0;">
				<span style="font-size: 16px;">🗑️</span>
				删除
			</button>
		`;
		
		// 删除按钮事件
		const deleteBtn = segmentEl.querySelector('.delete-segment-btn');
		if (deleteBtn) {
			deleteBtn.addEventListener('click', () => {
				if (confirm('确定要删除这个环节吗？')) {
					segmentEl.remove();
				}
			});
		}
		
		container.appendChild(segmentEl);
	});
}

console.log('✅ 后台管理系统事件处理器加载完成');

