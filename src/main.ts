import { App, Editor, MarkdownView, Modal, Notice, Plugin, PluginSettingTab, Setting } from 'obsidian';

interface DeepClaudeSettings {
	apiKey: string;
	apiUrl: string;
	deepseekModel: string;
	qwenModel: string;
	isOriginReasoning: boolean;
	language: string;
}

const DEFAULT_SETTINGS: DeepClaudeSettings = {
	apiKey: '',
	apiUrl: 'http://localhost:8000',
	deepseekModel: 'deepseek-r1',
	qwenModel: 'qwen2.5-14b-instruct-1m',
	isOriginReasoning: true,
	language: 'zh_CN'
}

interface DeepClaudeResponse {
	id: string;
	object: string;
	created: number;
	model: string;
	choices: Array<{
		index: number;
		delta?: {
			role?: string;
			content?: string;
			reasoning_content?: string;
		};
		message?: {
			role: string;
			content: string;
			reasoning_content?: string;
		};
	}>;
}

export default class DeepClaudePlugin extends Plugin {
	settings: DeepClaudeSettings;

	async onload() {
		await this.loadSettings();

		this.addCommand({
			id: 'ask-deepclaude',
			name: 'Ask DeepClaude',
			editorCallback: (editor: Editor, view: MarkdownView) => {
				const selection = editor.getSelection();
				new DeepClaudeModal(this.app, selection, async (result) => {
					await this.askDeepClaude(result, editor, view);
				}).open();
			}
		});

		this.addSettingTab(new DeepClaudeSettingTab(this.app, this));
	}

	onunload() {
		// 清理工作
	}

	async loadSettings() {
		this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
	}

	async saveSettings() {
		await this.saveData(this.settings);
	}

	async askDeepClaude(prompt: string, editor: Editor, view: MarkdownView) {
		try {
			if (!this.settings.apiKey) {
				new Notice('请在设置中配置 API Key');
				return;
			}

			const messages = [{
				role: 'user',
				content: prompt
			}];

			const response = await fetch(`${this.settings.apiUrl}/v1/chat/completions`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${this.settings.apiKey}`
				},
				body: JSON.stringify({
					messages: messages,
					model: this.settings.qwenModel,
					stream: true,
					temperature: 0.7,
					top_p: 0.95
				})
			});

			if (!response.ok) {
				throw new Error(`API 请求失败: ${response.statusText}`);
			}

			if (!response.body) {
				throw new Error('响应体为空');
			}

			// 创建响应内容的占位符
			const placeholder = editor.getCursor();
			editor.replaceRange('\n\n正在思考...\n\n', placeholder);
			const startPos = editor.getCursor();

			// 处理流式响应
			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let content = '';
			let reasoning = '';

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				const chunk = decoder.decode(value);
				const lines = chunk.split('\n');

				for (const line of lines) {
					if (line.startsWith('data: ')) {
						const data = line.slice(5);
						if (data === '[DONE]') continue;

						try {
							const parsed: DeepClaudeResponse = JSON.parse(data);
							const choice = parsed.choices[0];

							if (choice.delta?.reasoning_content) {
								reasoning = choice.delta.reasoning_content;
								// 更新思考过程
								editor.replaceRange(`\n\n思考过程：\n${reasoning}\n\n回答：\n`, startPos, editor.getCursor());
							} else if (choice.delta?.content) {
								content += choice.delta.content;
								// 更新回答内容
								const endPos = editor.getCursor();
								editor.replaceRange(content, startPos, endPos);
							}
						} catch (e) {
							console.error('解析响应数据失败:', e);
						}
					}
				}
			}

			new Notice('回答完成');

		} catch (error) {
			console.error('调用 API 时发生错误:', error);
			new Notice(`错误: ${error.message}`);
		}
	}
}

class DeepClaudeModal extends Modal {
	result: string;
	onSubmit: (result: string) => void;

	constructor(app: App, initialPrompt: string, onSubmit: (result: string) => void) {
		super(app);
		this.result = initialPrompt;
		this.onSubmit = onSubmit;
	}

	onOpen() {
		const { contentEl } = this;

		contentEl.createEl("h1", { text: "询问 DeepClaude" });

		const promptInput = contentEl.createEl("textarea", {
			cls: "deepclaude-modal-textarea"
		});
		promptInput.value = this.result;
		promptInput.style.width = "100%";
		promptInput.style.height = "150px";

		const buttonContainer = contentEl.createDiv({
			cls: "deepclaude-modal-button-container"
		});

		const submitButton = buttonContainer.createEl("button", {
			text: "提交",
			cls: "mod-cta"
		});
		submitButton.addEventListener("click", () => {
			this.onSubmit(promptInput.value);
			this.close();
		});

		const cancelButton = buttonContainer.createEl("button", {
			text: "取消"
		});
		cancelButton.addEventListener("click", () => {
			this.close();
		});
	}

	onClose() {
		const { contentEl } = this;
		contentEl.empty();
	}
}

class DeepClaudeSettingTab extends PluginSettingTab {
	plugin: DeepClaudePlugin;

	constructor(app: App, plugin: DeepClaudePlugin) {
		super(app, plugin);
		this.plugin = plugin;
	}

	display(): void {
		const { containerEl } = this;

		containerEl.empty();

		containerEl.createEl('h2', { text: 'DeepClaude 设置' });

		new Setting(containerEl)
			.setName('API Key')
			.setDesc('输入你的 DeepClaude API Key')
			.addText(text => text
				.setPlaceholder('输入 API Key')
				.setValue(this.plugin.settings.apiKey)
				.onChange(async (value) => {
					this.plugin.settings.apiKey = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('API URL')
			.setDesc('输入 DeepClaude API 地址')
			.addText(text => text
				.setPlaceholder('输入 API URL')
				.setValue(this.plugin.settings.apiUrl)
				.onChange(async (value) => {
					this.plugin.settings.apiUrl = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Deepseek 模型')
			.setDesc('选择要使用的 Deepseek 模型')
			.addText(text => text
				.setPlaceholder('输入模型名称')
				.setValue(this.plugin.settings.deepseekModel)
				.onChange(async (value) => {
					this.plugin.settings.deepseekModel = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('生成模型')
			.setDesc('选择要使用的生成模型')
			.addDropdown(dropdown => dropdown
				.addOption('qwen2.5-14b-instruct-1m', '通义千问 2.5')
				.addOption('google/gemini-2.0-pro-exp-02-05:free', 'Gemini 2.0 Pro')
				.addOption('anthropic/claude-3-sonnet', 'Claude 3 Sonnet')
				.setValue(this.plugin.settings.qwenModel)
				.onChange(async (value) => {
					this.plugin.settings.qwenModel = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('原生推理')
			.setDesc('启用原生推理模式')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.isOriginReasoning)
				.onChange(async (value) => {
					this.plugin.settings.isOriginReasoning = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('界面语言')
			.setDesc('选择界面显示语言')
			.addDropdown(dropdown => dropdown
				.addOption('zh_CN', '简体中文')
				.addOption('en_US', 'English')
				.setValue(this.plugin.settings.language)
				.onChange(async (value) => {
					this.plugin.settings.language = value;
					await this.plugin.saveSettings();
				}));
	}
} 