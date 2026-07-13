/**
 * 评委管理模块
 */

// 全局状态
let currentJudgeIndex = null; // 当前正在编辑的评委索引
let currentStreamId = null; // 当前选中的直播流ID
let judgesData = [
	{
		id: 'judge-1',
		name: '评委一',
		role: '主评委',
		avatar: './assets/images/judges/osmanthus.jpg',
		votes: 0
	},
	{
		id: 'judge-2',
		name: '评委二',
		role: '嘉宾评委',
		avatar: './assets/images/judges/osmanthus.jpg',
		votes: 0
	},
	{
		id: 'judge-3',
		name: '评委三',
		role: '嘉宾评委',
		avatar: './assets/images/judges/osmanthus.jpg',
		votes: 0
	}
];

/**
 * 初始化评委管理模块
 */
function initJudgesManagement() {
	console.log('🎯 初始化评委管理模块');

	// 加载直播流列表
	loadStreamsForJudges();

	// 绑定直播流选择事件
	const streamSelect = document.getElementById('judges-stream-select');
	if (streamSelect) {
		streamSelect.addEventListener('change', handleStreamChange);
	}

	// 刷新直播流列表按钮
	const refreshBtn = document.getElementById('judges-refresh-streams-btn');
	if (refreshBtn) {
		refreshBtn.addEventListener('click', loadStreamsForJudges);
	}

	// 绑定所有上传头像按钮
	document.querySelectorAll('.upload-avatar-btn').forEach((btn, index) => {
		btn.addEventListener('click', () => {
			const card = btn.closest('.judge-edit-card');
			const fileInput = card.querySelector('.judge-avatar-upload');
			fileInput.click();
		});
	});

	// 绑定文件输入变化事件
	document.querySelectorAll('.judge-avatar-upload').forEach((input, index) => {
		input.addEventListener('change', (e) => handleAvatarUpload(e, index));
	});

	// 绑定"从用户选择"按钮
	document.querySelectorAll('.select-from-users-btn').forEach((btn, index) => {
		btn.addEventListener('click', () => openUserSelectionModal(index));
	});

	// 绑定头像预览hover效果
	document.querySelectorAll('.judge-avatar-preview').forEach((preview, index) => {
		const overlay = preview.querySelector('.avatar-overlay');
		preview.addEventListener('mouseenter', () => {
			overlay.style.display = 'flex';
		});
		preview.addEventListener('mouseleave', () => {
			overlay.style.display = 'none';
		});
		preview.addEventListener('click', () => {
			const card = preview.closest('.judge-edit-card');
			const fileInput = card.querySelector('.judge-avatar-upload');
			fileInput.click();
		});
	});

	// 绑定保存按钮
	const saveBtn = document.getElementById('save-judges-btn');
	if (saveBtn) {
		saveBtn.addEventListener('click', saveJudgesData);
	}

	// 关闭弹窗按钮
	const closeModalBtn = document.getElementById('close-user-modal');
	if (closeModalBtn) {
		closeModalBtn.addEventListener('click', closeUserSelectionModal);
	}

	// 点击弹窗背景关闭
	const modal = document.getElementById('select-user-modal');
	if (modal) {
		modal.addEventListener('click', (e) => {
			if (e.target === modal) {
				closeUserSelectionModal();
			}
		});
	}

	// 用户搜索
	const userSearch = document.getElementById('modal-user-search');
	if (userSearch) {
		userSearch.addEventListener('input', (e) => {
			filterUsers(e.target.value);
		});
	}

	console.log('✅ 评委管理模块初始化完成');
}

/**
 * 加载直播流列表
 */
async function loadStreamsForJudges() {
	try {
		const response = await fetch(`${getAPIBase()}/api/v1/admin/streams`);
		const result = await response.json();

		const streams = result?.data?.streams || result?.streams || [];
		const select = document.getElementById('judges-stream-select');

		if (!select) return;

		select.innerHTML = '<option value="">请选择要管理的直播流</option>';

		streams.forEach(stream => {
			if (stream.enabled) {
				const option = document.createElement('option');
				option.value = stream.id;
				option.textContent = `${stream.name} (${stream.type?.toUpperCase() || 'HLS'})`;
				select.appendChild(option);
			}
		});

		console.log('✅ 加载直播流列表成功');
	} catch (error) {
		console.error('❌ 加载直播流列表失败:', error);
		showNotification('加载直播流列表失败', 'error');
	}
}

/**
 * 处理直播流选择变化
 */
function handleStreamChange(e) {
	const streamId = e.target.value;
	currentStreamId = streamId;

	const select = e.target;
	const selectedOption = select.options[select.selectedIndex];
	const streamName = selectedOption ? selectedOption.textContent : '-';

	// 显示当前管理的流信息
	const infoDiv = document.getElementById('judges-current-stream-info');
	const nameSpan = document.getElementById('judges-current-stream-name');

	if (streamId && infoDiv && nameSpan) {
		nameSpan.textContent = streamName;
		infoDiv.style.display = 'block';
	} else if (infoDiv) {
		infoDiv.style.display = 'none';
	}

	// 加载该流的评委数据
	if (streamId) {
		loadJudgesDataForStream(streamId);
	}
}

/**
 * 加载指定直播流的评委数据
 */
async function loadJudgesDataForStream(streamId) {
	try {
		// TODO: 调用后端API获取评委数据
		// const response = await fetch(`${getAPIBase()}/api/v1/admin/judges?stream_id=${streamId}`);
		// const result = await response.json();
		// judgesData = result.data || judgesData;

		// 暂时使用默认数据
		console.log('📝 加载评委数据 (使用默认数据)');
		updateJudgesUI();
	} catch (error) {
		console.error('❌ 加载评委数据失败:', error);
		showNotification('加载评委数据失败', 'error');
	}
}

/**
 * 更新评委UI显示
 */
function updateJudgesUI() {
	document.querySelectorAll('.judge-edit-card').forEach((card, index) => {
		if (judgesData[index]) {
			const judge = judgesData[index];
			const nameInput = card.querySelector('.judge-name-input');
			const roleInput = card.querySelector('.judge-role-input');
			const votesInput = card.querySelector('.judge-votes-input');
			const avatarPreview = card.querySelector('.judge-avatar-preview');

			if (nameInput) nameInput.value = judge.name;
			if (roleInput) roleInput.value = judge.role;
			if (votesInput) votesInput.value = judge.votes || 0;
			if (avatarPreview && judge.avatar) {
				avatarPreview.style.backgroundImage = `url('${judge.avatar}')`;
			}
		}
	});
}

/**
 * 处理头像上传
 */
function handleAvatarUpload(event, judgeIndex) {
	const file = event.target.files[0];
	if (!file) return;

	// 验证文件类型
	if (!file.type.startsWith('image/')) {
		showNotification('请选择图片文件', 'error');
		return;
	}

	// 验证文件大小 (最大2MB)
	if (file.size > 2 * 1024 * 1024) {
		showNotification('图片大小不能超过2MB', 'error');
		return;
	}

	// 读取并预览图片
	const reader = new FileReader();
	reader.onload = (e) => {
		const imageUrl = e.target.result;

		// 更新预览
		const card = document.querySelectorAll('.judge-edit-card')[judgeIndex];
		const preview = card.querySelector('.judge-avatar-preview');
		if (preview) {
			preview.style.backgroundImage = `url('${imageUrl}')`;
		}

		// 更新数据
		if (judgesData[judgeIndex]) {
			judgesData[judgeIndex].avatar = imageUrl;
		}

		showNotification('头像上传成功', 'success');
	};

	reader.readAsDataURL(file);
}

/**
 * 打开用户选择弹窗
 */
async function openUserSelectionModal(judgeIndex) {
	currentJudgeIndex = judgeIndex;

	const modal = document.getElementById('select-user-modal');
	if (modal) {
		modal.style.display = 'flex';

		// 加载用户列表
		await loadUsersForSelection();
	}
}

/**
 * 关闭用户选择弹窗
 */
function closeUserSelectionModal() {
	const modal = document.getElementById('select-user-modal');
	if (modal) {
		modal.style.display = 'none';
	}
	currentJudgeIndex = null;
}

/**
 * 加载用户列表供选择
 */
async function loadUsersForSelection() {
	try {
		const response = await fetch(`${getAPIBase()}/api/v1/admin/users`);
		const result = await response.json();

		const users = result?.data?.users || result?.users || [];
		renderUsersList(users);
	} catch (error) {
		console.error('❌ 加载用户列表失败:', error);
		const listDiv = document.getElementById('modal-users-list');
		if (listDiv) {
			listDiv.innerHTML = '<div style="text-align: center; padding: 40px; color: #e74c3c;">加载失败,请重试</div>';
		}
	}
}

/**
 * 渲染用户列表
 */
function renderUsersList(users) {
	const listDiv = document.getElementById('modal-users-list');
	if (!listDiv) return;

	if (!users || users.length === 0) {
		listDiv.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">暂无用户数据</div>';
		return;
	}

	listDiv.innerHTML = users.map(user => `
		<div class="user-select-item" data-user-id="${user.id}" style="display: flex; align-items: center; padding: 12px; border: 1px solid #e9ecef; border-radius: 8px; margin-bottom: 10px; cursor: pointer; transition: all 0.3s;">
			<img src="${user.avatarUrl || '/static/default-avatar.png'}" alt="${user.nickname}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover; margin-right: 15px;">
			<div style="flex: 1;">
				<div style="font-weight: 600; color: #2c3e50; margin-bottom: 4px;">${user.nickname}</div>
				<div style="font-size: 12px; color: #95a5a6;">ID: ${user.id}</div>
			</div>
			<button class="btn btn-sm btn-primary select-this-user-btn" style="padding: 6px 16px;">
				选择
			</button>
		</div>
	`).join('');

	// 绑定选择按钮事件
	listDiv.querySelectorAll('.select-this-user-btn').forEach(btn => {
		btn.addEventListener('click', (e) => {
			e.stopPropagation();
			const item = btn.closest('.user-select-item');
			const userId = item.dataset.userId;
			const user = users.find(u => u.id === userId);
			if (user) {
				selectUserAsJudge(user);
			}
		});
	});

	// 点击整行也可以选择
	listDiv.querySelectorAll('.user-select-item').forEach(item => {
		item.addEventListener('mouseenter', () => {
			item.style.background = '#f8f9fa';
		});
		item.addEventListener('mouseleave', () => {
			item.style.background = 'transparent';
		});
		item.addEventListener('click', () => {
			const userId = item.dataset.userId;
			const user = users.find(u => u.id === userId);
			if (user) {
				selectUserAsJudge(user);
			}
		});
	});
}

/**
 * 选择用户作为评委
 */
function selectUserAsJudge(user) {
	if (currentJudgeIndex === null) return;

	const card = document.querySelectorAll('.judge-edit-card')[currentJudgeIndex];
	if (!card) return;

	// 更新姓名
	const nameInput = card.querySelector('.judge-name-input');
	if (nameInput) {
		nameInput.value = user.nickname || user.name || `评委${currentJudgeIndex + 1}`;
	}

	// 更新头像
	const avatarPreview = card.querySelector('.judge-avatar-preview');
	if (avatarPreview && user.avatarUrl) {
		avatarPreview.style.backgroundImage = `url('${user.avatarUrl}')`;
	}

	// 更新数据
	if (judgesData[currentJudgeIndex]) {
		judgesData[currentJudgeIndex].name = user.nickname || user.name;
		judgesData[currentJudgeIndex].avatar = user.avatarUrl;
	}

	showNotification(`已选择 ${user.nickname} 作为评委`, 'success');
	closeUserSelectionModal();
}

/**
 * 过滤用户列表
 */
function filterUsers(keyword) {
	const items = document.querySelectorAll('.user-select-item');
	items.forEach(item => {
		const text = item.textContent.toLowerCase();
		if (text.includes(keyword.toLowerCase())) {
			item.style.display = 'flex';
		} else {
			item.style.display = 'none';
		}
	});
}

/**
 * 保存评委数据
 */
async function saveJudgesData() {
	if (!currentStreamId) {
		showNotification('请先选择直播流', 'warning');
		return;
	}

	// 收集表单数据
	const cards = document.querySelectorAll('.judge-edit-card');
	const updatedJudges = [];

	cards.forEach((card, index) => {
		const nameInput = card.querySelector('.judge-name-input');
		const roleInput = card.querySelector('.judge-role-input');
		const votesInput = card.querySelector('.judge-votes-input');

		updatedJudges.push({
			id: judgesData[index]?.id || `judge-${index + 1}`,
			name: nameInput?.value || `评委${index + 1}`,
			role: roleInput?.value || '评委',
			avatar: judgesData[index]?.avatar || './assets/images/judges/osmanthus.jpg',
			votes: parseInt(votesInput?.value) || 0
		});
	});

	try {
		// TODO: 调用后端API保存数据
		// const response = await fetch(`${getAPIBase()}/api/v1/admin/judges`, {
		// 	method: 'POST',
		// 	headers: { 'Content-Type': 'application/json' },
		// 	body: JSON.stringify({
		// 		stream_id: currentStreamId,
		// 		judges: updatedJudges
		// 	})
		// });

		// 暂时只更新本地数据
		judgesData = updatedJudges;
		console.log('💾 保存评委数据:', judgesData);

		showNotification('评委信息保存成功', 'success');

		// TODO: 通知大屏幕更新
		notifyVoteDisplayUpdate();

	} catch (error) {
		console.error('❌ 保存评委数据失败:', error);
		showNotification('保存失败,请重试', 'error');
	}
}

/**
 * 通知大屏幕更新评委信息
 */
function notifyVoteDisplayUpdate() {
	// TODO: 通过WebSocket或API通知vote-display.html更新
	console.log('📢 通知大屏幕更新评委信息');
}

/**
 * 显示通知消息
 */
function showNotification(message, type = 'info') {
	// 复用现有的通知系统,或创建简单的通知
	console.log(`📢 [${type.toUpperCase()}] ${message}`);

	// 简单的alert实现(后续可以替换为更好的UI)
	alert(message);
}

/**
 * 获取API基础地址
 */
function getAPIBase() {
	if (window.SERVER_CONFIG && window.SERVER_CONFIG.BASE_URL) {
		return window.SERVER_CONFIG.BASE_URL;
	}
	return 'http://localhost:8081';
}

// 导出函数供外部使用
if (typeof window !== 'undefined') {
	window.initJudgesManagement = initJudgesManagement;
	window.judgesData = judgesData;
}
