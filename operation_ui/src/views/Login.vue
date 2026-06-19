<template>
	<div class="login-view">
		<div class="login-container">
			<div class="main-card">
				<div class="left-section">
					<div class="design-content">
						<div class="floating-elements">
							<div class="floating-item code-icon">
								<el-icon><Document /></el-icon>
							</div>
							<div class="floating-item book-icon">
								<el-icon><Reading /></el-icon>
							</div>
							<div class="floating-item trophy-icon">
								<el-icon><Trophy /></el-icon>
							</div>
							<div class="floating-item rocket-icon">
								<el-icon><Upload /></el-icon>
							</div>
						</div>
						<div class="main-illustration">
							<div class="gradient-circle"></div>
							<div class="education-icon">
								<el-icon><UserFilled /></el-icon>
							</div>
						</div>
						<div class="welcome-text">
							<h2>AI 驱动，高效运营</h2>
							<p>智能辅助运营平台，助力业务提效与决策</p>
						</div>
						<div class="feature-highlights">
							<div class="feature-item">
								<el-icon><CircleCheck /></el-icon>
								<span>智能运营</span>
							</div>
							<div class="feature-item">
								<el-icon><StarFilled /></el-icon>
								<span>数据洞察</span>
							</div>
							<div class="feature-item">
								<el-icon><Medal /></el-icon>
								<span>效率提升</span>
							</div>
						</div>
					</div>
				</div>
				<div class="right-section">
					<div class="form-content">
						<div class="form-header">
							<div class="logo">
								<div class="logo-icon">AI</div>
								<div class="logo-text">智能辅助运营平台</div>
							</div>
							<p class="description">使用用户名与密码登录</p>
						</div>
						<el-form class="login-form" :model="loginForm" :rules="rules" ref="loginFormRef"
							@keyup.enter="submitForm">
							<el-form-item prop="terminal" v-show="false">
								<el-input v-model="loginForm.terminal"></el-input>
							</el-form-item>
							<el-form-item prop="userName" class="form-item-input">
								<div class="input-wrap input-wrap-user">
									<span class="input-icon">
										<el-icon><User /></el-icon>
									</span>
									<el-input
										v-model="loginForm.userName"
										placeholder="请输入用户名"
										maxlength="32"
										clearable
										class="login-input" />
								</div>
							</el-form-item>
							<el-form-item prop="password" class="form-item-input password-item">
								<div class="input-wrap input-wrap-password">
									<span class="input-icon">
										<el-icon><Lock /></el-icon>
									</span>
									<el-input
										v-model="loginForm.password"
										placeholder="请输入密码"
										maxlength="64"
										clearable
										show-password
										class="login-input" />
								</div>
							</el-form-item>
							<el-form-item style="padding-top: 18px">
								<el-button
									type="primary"
									class="login-btn"
									:loading="loginLoading"
									@click="submitForm">
									登录
								</el-button>
							</el-form-item>
						</el-form>
						<div class="agreement-text">
							<span>点击登录即表示同意</span>
							<a href="#" class="link">《用户协议》</a>
							<span>和</span>
							<a href="#" class="link">《隐私政策》</a>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import CookieUtils from '@/utils/cookie'
import { useUserStore } from '@/store/userStore'
import {
	Document,
	Reading,
	Trophy,
	Upload,
	UserFilled,
	CircleCheck,
	StarFilled,
	Medal,
	User,
	Lock,
} from '@element-plus/icons-vue'

export default {
	name: 'Login',
	components: {
		Document,
		Reading,
		Trophy,
		Upload,
		UserFilled,
		CircleCheck,
		StarFilled,
		Medal,
		User,
		Lock,
	},
	data() {
		const validateUserName = (rule, value, callback) => {
			if (!value) return callback(new Error('请输入用户名或手机号'))
			callback()
		}
		const validatePassword = (rule, value, callback) => {
			if (!value) return callback(new Error('请输入密码'))
			callback()
		}
		return {
			loginForm: {
				terminal: 'WEB',
				userName: '',
				password: '',
			},
			rules: {
				userName: [{ validator: validateUserName, trigger: 'blur' }],
				password: [{ validator: validatePassword, trigger: 'blur' }],
			},
			loginLoading: false,
		}
	},
	computed: {
		userStore() {
			return useUserStore()
		},
	},
	methods: {
		submitForm() {
			this.$refs.loginFormRef.validate((valid) => {
				if (!valid) return
				this.loginLoading = true
				this.$http({
					url: '/login',
					method: 'post',
					data: {
						userName: this.loginForm.userName,
						password: this.loginForm.password,
						terminal: this.loginForm.terminal,
					},
				})
					.then((data) => {
						this.setCookie('userName', this.loginForm.userName, 7)
						this.setCookie('isLoggedIn', 'true', 7)
						this.setCookie('userId', data.userId || '', 7)
						this.setCookie('nickName', data.userName || this.loginForm.userName, 7)
						this.setCookie('accessToken', data.accessToken || '', 7)
						this.setCookie('refreshToken', data.refreshToken || '', 7)
						this.userStore.setUserInfo({
							userId: data.userId,
							userName: data.userName || this.loginForm.userName,
							nickName: data.userName || this.loginForm.userName,
							headImageThumb: data.headImageThumb || '',
						})
						this.$message.success('登录成功')
						const redirect = this.$route.query.redirect || '/create'
						this.$nextTick(() => this.$router.push(redirect))
					})
					.finally(() => {
						this.loginLoading = false
					})
			})
		},
		getCookie(name) {
			return CookieUtils.getCookie(name) || ''
		},
		setCookie(name, value, days = 7) {
			CookieUtils.setCookie(name, value, days)
		},
		checkLoginStatus() {
			const isLoggedIn = this.getCookie('isLoggedIn')
			const userId = this.getCookie('userId')
			if (isLoggedIn === 'true' && userId && userId !== '') {
				this.$nextTick(() => this.$router.push('/create'))
			}
		},
	},
	mounted() {
		this.loginForm.userName = this.getCookie('userName')
		this.loginForm.terminal = this.$enums?.TERMINAL_TYPE?.WEB || 'WEB'
		this.checkLoginStatus()
	},
}
</script>

<style scoped lang="scss">
.login-view {
	width: 100%;
	height: 100vh;
	background: linear-gradient(135deg,
		rgba(255, 107, 71, 0.05) 0%,
		rgba(255, 255, 255, 0.95) 25%,
		rgba(255, 255, 255, 0.98) 50%,
		rgba(255, 107, 71, 0.08) 75%,
		rgba(255, 255, 255, 0.95) 100%);
	display: flex;
	flex-direction: column;
	position: relative;
	overflow: hidden;

	.login-container {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 20px;
	}

	.main-card {
		display: flex;
		width: 100%;
		max-width: 1000px;
		height: 600px;
		background: rgba(255, 255, 255, 0.95);
		backdrop-filter: blur(20px);
		border-radius: 24px;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
		overflow: hidden;
		animation: slideInUp 0.8s ease-out;
	}

	.left-section {
		flex: 1;
		background: linear-gradient(135deg, #FF6B47 0%, #FF8A65 100%);
		position: relative;
		overflow: hidden;

		.design-content {
			position: relative;
			height: 100%;
			padding: 40px;
			display: flex;
			flex-direction: column;
			justify-content: center;
			align-items: center;
			color: white;
		}

		.floating-elements .floating-item {
			position: absolute;
			width: 50px;
			height: 50px;
			border-radius: 50%;
			display: flex;
			align-items: center;
			justify-content: center;
			font-size: 20px;
			color: white;
			background: rgba(255, 255, 255, 0.2);
			backdrop-filter: blur(10px);
			animation: float 3s ease-in-out infinite;
			&.code-icon { top: 15%; left: 15%; animation-delay: 0s; }
			&.book-icon { top: 25%; right: 20%; animation-delay: 0.5s; }
			&.trophy-icon { bottom: 35%; left: 20%; animation-delay: 1s; }
			&.rocket-icon { bottom: 25%; right: 15%; animation-delay: 1.5s; }
		}

		.main-illustration {
			z-index: 2;
			margin-bottom: 30px;
			.gradient-circle {
				width: 120px;
				height: 120px;
				border-radius: 50%;
				background: rgba(255, 255, 255, 0.2);
				backdrop-filter: blur(10px);
				box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
				animation: pulse 2s ease-in-out infinite;
			}
			.education-icon { font-size: 60px; color: white; }
		}

		.welcome-text {
			text-align: center;
			z-index: 2;
			margin-bottom: 30px;
			h2 { font-size: 28px; font-weight: 700; color: white; margin-bottom: 12px; }
			p { font-size: 16px; color: rgba(255, 255, 255, 0.9); line-height: 1.6; }
		}

		.feature-highlights {
			z-index: 2;
			.feature-item {
				display: flex;
				align-items: center;
				margin-bottom: 12px;
				color: rgba(255, 255, 255, 0.9);
				font-size: 14px;
				i { color: white; margin-right: 8px; font-size: 16px; }
			}
		}
	}

	.right-section {
		flex: 1;
		max-width: 400px;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 40px;
		background: white;
	}

	.form-content { width: 100%; max-width: 320px; }

	.form-header {
		text-align: center;
		margin-bottom: 32px;
		.logo {
			display: flex;
			align-items: center;
			justify-content: center;
			margin-bottom: 16px;
			.logo-icon { font-size: 32px; font-weight: 700; color: #FF6B47; margin-right: 8px; }
			.logo-text { font-size: 32px; font-weight: 700; color: #333; }
		}
		.description { font-size: 14px; color: #666; margin: 0; }
	}

	.login-form {
		.el-form-item { margin-bottom: 20px; }
		.form-item-input { margin-bottom: 22px; }
		.password-item { margin-top: 4px; }

		.input-wrap {
			display: flex;
			align-items: center;
			height: 52px;
			padding: 0 16px 0 16px;
			background: #FAFBFC;
			border: 1px solid #E8ECF0;
			border-radius: 14px;
			transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;

			.input-icon {
				display: flex;
				align-items: center;
				justify-content: center;
				width: 36px;
				height: 36px;
				margin-right: 12px;
				border-radius: 10px;
				background: rgba(255, 107, 71, 0.1);
				color: #FF6B47;
				font-size: 18px;
				flex-shrink: 0;
			}

			&:focus-within {
				border-color: #FF6B47;
				box-shadow: 0 0 0 3px rgba(255, 107, 71, 0.12);
				background: #fff;
			}

			.login-input {
				flex: 1;
				height: 100%;
				:deep(.el-input__wrapper) {
					height: 50px;
					padding: 0;
					background: transparent !important;
					box-shadow: none !important;
				}
				:deep(.el-input__inner) {
					height: 50px;
					line-height: 50px;
					font-size: 15px;
					color: #1a1a1a;
					&::placeholder { color: #9CA3AF; }
				}
				:deep(.el-input__suffix) { padding-left: 8px; }
			}
		}
		.login-btn {
			width: 100%;
			height: 48px;
			background: linear-gradient(135deg, #FF6B47 0%, #FF8A65 100%);
			border: none;
			border-radius: 12px;
			color: white;
			font-size: 16px;
			font-weight: 600;
			&:hover:not(:disabled) {
				background: linear-gradient(135deg, #FF5722 0%, #FF7043 100%);
				transform: translateY(-2px);
				box-shadow: 0 8px 25px rgba(255, 107, 71, 0.3);
			}
			&:disabled { background: #F5F7FA; color: #C0C4CC; cursor: not-allowed; }
		}
	}

	.agreement-text {
		text-align: center;
		font-size: 12px;
		color: #666;
		margin-top: 20px;
		.link { color: #FF6B47; text-decoration: none; &:hover { text-decoration: underline; } }
	}
}

@keyframes slideInUp {
	from { opacity: 0; transform: translateY(30px); }
	to { opacity: 1; transform: translateY(0); }
}
@keyframes float {
	0%, 100% { transform: translateY(0); }
	50% { transform: translateY(-10px); }
}
@keyframes pulse {
	0%, 100% { transform: scale(1); }
	50% { transform: scale(1.05); }
}

@media (max-width: 768px) {
	.main-card { flex-direction: column; height: auto; margin: 20px; }
	.left-section { min-height: 300px; order: 1; .floating-elements { display: none; } }
	.right-section { max-width: none; padding: 30px 20px; order: 2; }
}
</style>
