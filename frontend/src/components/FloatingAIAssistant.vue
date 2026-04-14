<template>
  <div v-if="shouldRender" class="ai-float-root">
    <transition name="ai-float-pop">
      <section v-show="open" class="ai-float-panel app-glass-card">
        <header class="ai-float-header">
          <div class="title-wrap">
            <span class="title-dot" />
            <span class="title-text">AI 助手</span>
            <el-tag size="small" type="success" effect="plain">{{ providerTagLabel }}</el-tag>
          </div>
          <div class="header-actions">
            <el-button text size="small" @click="open = false">收起</el-button>
          </div>
        </header>

        <div class="ai-float-body">
          <aside class="conversation-pane">
            <div class="conversation-pane-header">
              <el-button type="primary" plain size="small" :disabled="conversationBusy" @click="startNewConversation">
                开启新对话
              </el-button>
            </div>
            <div class="conversation-list" v-loading="conversationLoading">
              <div
                v-for="item in conversations"
                :key="item.id"
                class="conversation-item"
                :class="{
                  'is-active': item.id === activeConversationId,
                  'is-menu-open': openedConversationMenuId === item.id,
                }"
              >
                <button
                  type="button"
                  class="conversation-main"
                  :disabled="scienceLoading || conversationSwitching || editingHistoryConversationId !== null"
                  @click="switchConversation(item.id)"
                >
                  <div class="conversation-name-row">
                    <div class="conversation-name">
                      <el-input
                        v-if="editingHistoryConversationId === item.id"
                        v-model="historyTitleDraft"
                        class="history-title-editor"
                        size="small"
                        @click.stop
                        @keyup.enter.stop="submitHistoryTitleEdit(item)"
                        @keyup.esc.stop="cancelHistoryTitleEdit"
                        @blur="submitHistoryTitleEdit(item)"
                      />
                      <template v-else>
                        {{ item.title || '新对话' }}
                      </template>
                    </div>
                    <el-tag v-if="item.is_pinned" size="small" effect="plain" type="warning">置顶</el-tag>
                  </div>
                </button>

                <div class="conversation-menu-wrap" @click.stop>
                  <el-button
                    text
                    circle
                    class="conversation-more-btn"
                    :disabled="scienceLoading || conversationSwitching || editingHistoryConversationId !== null"
                    @click.stop="toggleConversationMenu(item.id)"
                  >
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <div
                    v-if="openedConversationMenuId === item.id"
                    class="conversation-inline-menu"
                    @click.stop
                  >
                    <button type="button" class="conversation-menu-item" @click="handleConversationMenuAction('rename', item)">
                      重命名对话
                    </button>
                    <button type="button" class="conversation-menu-item" @click="handleConversationMenuAction('pin', item)">
                      {{ item.is_pinned ? '取消置顶' : '置顶对话' }}
                    </button>
                    <button
                      type="button"
                      class="conversation-menu-item conversation-menu-item-danger"
                      @click="handleConversationMenuAction('delete', item)"
                    >
                      删除对话
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </aside>

          <main class="chat-pane">
            <div class="conversation-toolbar">
              <div class="conversation-title">
                {{ activeConversation?.title || '新对话' }}
              </div>
            </div>

            <div class="quick-row">
              <el-tag
                v-for="item in activePromptSet"
                :key="item"
                class="quick-tag"
                effect="light"
                @click="askScience(item)"
              >
                {{ item }}
              </el-tag>
              <el-button text size="small" :disabled="scienceLoading" @click="rotatePrompts">换一换</el-button>
            </div>

            <div ref="scienceScrollRef" class="chat-window" @scroll="handleChatScroll">
              <div v-if="scienceMessages.length === 0" class="chat-empty">
                可直接提问课堂科学问题，或输入“请根据以下要点扩写/完整生成文章”等自然语言命令。
              </div>
              <div
                v-for="msg in scienceMessages"
                :key="msg.id"
                class="chat-msg"
                :class="`is-${msg.role}`"
              >
                <div class="chat-meta">
                  <span>{{ msg.role === 'user' ? '你' : 'AI' }}</span>
                  <el-tag v-if="msg.role === 'assistant' && getModelLabel(msg.model)" size="small" effect="plain">
                    {{ getModelLabel(msg.model) }}
                  </el-tag>
                  <el-tag v-if="msg.role === 'assistant' && getSourceLabel(msg.source)" size="small" effect="plain">
                    {{ getSourceLabel(msg.source) }}
                  </el-tag>
                </div>
                <div class="chat-bubble" :class="{ 'is-error': msg.status === 'error' }">
                  <details v-if="msg.reasoning" class="chat-reasoning" :open="msg.status === 'streaming'">
                    <summary>思考过程</summary>
                    <div class="reasoning-content">{{ msg.reasoning }}</div>
                  </details>
                  <template v-if="msg.role === 'assistant'">
                    <AIMarkdownContent
                      v-if="msg.content && msg.status !== 'streaming'"
                      :content="msg.content"
                    />
                    <div v-else class="chat-plain-text">
                      {{ msg.content || (msg.reasoning ? '' : '思考中...') }}
                    </div>
                  </template>
                  <div v-else class="chat-plain-text">
                    {{ msg.content }}
                  </div>
                  <span v-if="msg.status === 'streaming'" class="typing">▍</span>
                </div>
                <div v-if="msg.role === 'assistant' && msg.webSearchNotice" class="search-note">
                  {{ msg.webSearchNotice }}
                </div>
                <div
                  v-if="msg.role === 'assistant' && msg.status === 'done' && getVisibleCitations(msg).length"
                  class="source-wrap"
                >
                  <el-button
                    text
                    size="small"
                    class="source-toggle"
                    @click="toggleCitationExpanded(msg.id)"
                  >
                    {{ isCitationExpanded(msg.id) ? '隐藏来源' : `查看来源（${getVisibleCitations(msg).length}）` }}
                  </el-button>
                  <div v-show="isCitationExpanded(msg.id)" class="source-list">
                    <div class="source-title">来源链接</div>
                    <a
                      v-for="(item, index) in getVisibleCitations(msg)"
                      :key="`${msg.id}-${item.url}-${index}`"
                      class="source-link"
                      :href="item.url"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <span class="source-link-title">{{ index + 1 }}. {{ item.title || item.url }}</span>
                      <span v-if="item.snippet" class="source-link-snippet">{{ item.snippet }}</span>
                      <span class="source-link-url">{{ item.url }}</span>
                    </a>
                  </div>
                </div>
                <div
                  v-if="msg.role === 'assistant' && msg.status === 'done' && msg.content.trim()"
                  class="chat-actions"
                >
                  <el-button
                    v-if="canInsertIntoTeaching"
                    text
                    size="small"
                    @click="insertAssistantContent(msg.content)"
                  >
                    插入到教学正文（Markdown）
                  </el-button>
                  <span v-else class="insert-tip">打开教学内容中的文章编辑器后，可一键插入</span>
                </div>
              </div>
            </div>

            <transition name="fade-slide">
              <el-button
                v-show="showScrollToBottom"
                class="scroll-bottom-btn"
                type="primary"
                plain
                size="small"
                @click="scrollToLatest"
              >
                回到底部
              </el-button>
            </transition>

            <div class="input-row">
              <el-input
                v-model="scienceQuestion"
                maxlength="400"
                show-word-limit
                placeholder="例如：请把以下要点扩写成 800 字课堂文章：..."
                :disabled="conversationSwitching || conversationLoading"
                @keyup.enter="askScience()"
              />
              <el-button
                type="primary"
                :loading="scienceLoading"
                :disabled="!scienceQuestion.trim() || conversationSwitching || conversationLoading"
                @click="askScience()"
              >
                发送
              </el-button>
              <el-button v-if="scienceLoading" type="danger" plain @click="stopScience">停止</el-button>
            </div>

            <div class="option-row">
              <label class="option-item">
                <span>深度思考</span>
                <el-switch v-model="deepThinkingEnabled" size="small" />
              </label>
              <label class="option-item">
                <span>智能搜索</span>
                <el-switch v-model="smartSearchEnabled" size="small" />
              </label>
            </div>
          </main>
        </div>
      </section>
    </transition>

    <el-button class="ai-fab" type="primary" circle @click="togglePanel">
      <el-icon><ChatDotRound /></el-icon>
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { MoreFilled } from '@element-plus/icons-vue';
import AIMarkdownContent from './AIMarkdownContent.vue';
import {
  askScienceAssistantInConversation,
  createAIConversation,
  deleteAIConversation,
  getApiBaseUrl,
  getAIConversationDetail,
  getAIConversations,
  pinAIConversation,
  renameAIConversation,
  streamScienceAssistantInConversation,
  type AIConversationMessage,
  type AIConversationSummary,
  type AIConversationAskRequest,
  type AIScienceStreamMeta,
  type AISourceLink,
} from '../api';
import { getErrorMessage } from '../utils/error';

type ChatRole = 'user' | 'assistant';
type ChatStatus = 'streaming' | 'done' | 'error';

type ChatMessage = {
  id: number;
  role: ChatRole;
  content: string;
  reasoning?: string;
  source?: string;
  model?: string;
  citations?: AISourceLink[];
  webSearchNotice?: string | null;
  status: ChatStatus;
};

const CITATION_INDEX_PATTERN = /\[(\d{1,2})\]/g;

const extractCitationIndexes = (content: string, maxIndex: number): number[] => {
  if (!content || maxIndex <= 0) {
    return [];
  }

  const result: number[] = [];
  const seen = new Set<number>();
  let match: RegExpExecArray | null = null;
  CITATION_INDEX_PATTERN.lastIndex = 0;
  while ((match = CITATION_INDEX_PATTERN.exec(content)) !== null) {
    const value = Number(match[1]);
    if (!Number.isInteger(value) || value < 1 || value > maxIndex || seen.has(value)) {
      continue;
    }
    seen.add(value);
    result.push(value);
  }

  return result;
};

const getVisibleCitations = (message: ChatMessage): AISourceLink[] => {
  const citations = message.citations || [];
  if (!citations.length) {
    return [];
  }

  const indexes = extractCitationIndexes(message.content || '', citations.length);
  if (!indexes.length) {
    return [];
  }

  return indexes
    .map((index) => citations[index - 1])
    .filter((item): item is AISourceLink => Boolean(item?.url));
};

const route = useRoute();

const open = ref(false);
const authToken = ref<string | null>(null);

const syncAuthToken = () => {
  if (typeof window === 'undefined') {
    authToken.value = null;
    return;
  }

  authToken.value = localStorage.getItem('token');
};

const shouldRender = computed(() => {
  return Boolean(authToken.value) && route.path !== '/login' && route.path !== '/display';
});

const providerTag = ref('chat');
const deepThinkingEnabled = ref(false);
const smartSearchEnabled = ref(false);

const getModelLabel = (model?: string | null): string => {
  const key = String(model || '').trim().toLowerCase();
  if (!key) return '';
  if (key.includes('reasoner')) return '深度模型';
  if (key.includes('chat')) return '标准模型';
  if (key.includes('weather')) return '实时天气';
  return 'AI 模型';
};

const getSourceLabel = (source?: string | null): string => {
  const key = String(source || '').trim().toLowerCase();
  if (!key) return '';
  if (key.includes('weather-api')) return '实时天气';
  if (key.includes('langchain')) return '智能检索';
  if (key.includes('rule-based')) return '本地兜底';
  if (key.includes('deepseek') || key.includes('qwen') || key.includes('llm')) return '在线模型';
  return 'AI 来源';
};

const providerTagLabel = computed(() => {
  return getModelLabel(providerTag.value) || getSourceLabel(providerTag.value) || 'AI 引擎';
});

const DEEP_THINKING_SESSION_KEY = 'floating-ai-deep-thinking-enabled';
const SMART_SEARCH_SESSION_KEY = 'floating-ai-smart-search-enabled';

const scienceQuestion = ref('');
const scienceMessages = ref<ChatMessage[]>([]);
const scienceLoading = ref(false);
const scienceScrollRef = ref<HTMLElement | null>(null);
const autoScrollEnabled = ref(true);
const showScrollToBottom = ref(false);
const promptSetIndex = ref(0);
const canInsertIntoTeaching = ref(false);
const conversations = ref<AIConversationSummary[]>([]);
const activeConversationId = ref<number | null>(null);
const conversationLoading = ref(false);
const conversationSwitching = ref(false);
const conversationsReady = ref(false);
const editingHistoryConversationId = ref<number | null>(null);
const historyTitleDraft = ref('');
const openedConversationMenuId = ref<number | null>(null);
const citationExpandedState = ref<Record<number, boolean>>({});

const nextLocalMessageId = ref(-1);
let scienceAbortController: AbortController | null = null;

const promptSets = [
  [
    '请根据当前数据判断是否需要浇水，并给出理由。',
    '请用适合小学生的话解释当前温湿度变化。',
    '请给我三条 10 分钟内可执行的调优建议。',
  ],
  [
    '请把以下要点扩写成 900 字课堂文章：\n- 观察温度\n- 记录叶片\n- 讨论蒸腾作用',
    '请根据以下要点生成完整教学文章，包含学习目标和课后思考：\n- 光照与生长\n- 水分管理',
    '请将这段内容改成更适合学生阅读的语气：...',
  ],
  [
    '如果温度持续升高，课堂上可以做什么对照实验？',
    '请把当前建议改写成学生可执行的三步任务。',
    '请用“现象-原因-建议”结构回答。',
  ],
];

const activePromptSet = computed(() => promptSets[promptSetIndex.value % promptSets.length]);
const activeConversation = computed(() => {
  if (!activeConversationId.value) return null;
  return conversations.value.find((item) => item.id === activeConversationId.value) || null;
});
const conversationBusy = computed(() => conversationLoading.value || conversationSwitching.value || scienceLoading.value);

const togglePanel = () => {
  open.value = !open.value;
};

const rotatePrompts = () => {
  promptSetIndex.value = (promptSetIndex.value + 1) % promptSets.length;
};

const getLocalMessageId = (): number => {
  const current = nextLocalMessageId.value;
  nextLocalMessageId.value -= 1;
  return current;
};

const CHAT_SCROLL_THRESHOLD = 48;

const sortConversations = (items: AIConversationSummary[]): AIConversationSummary[] => {
  return [...items].sort((a, b) => {
    const pinnedDelta = Number(Boolean(b.is_pinned)) - Number(Boolean(a.is_pinned));
    if (pinnedDelta !== 0) {
      return pinnedDelta;
    }

    if (a.is_pinned && b.is_pinned) {
      const pinnedTimeA = new Date(a.pinned_at || a.updated_at || a.created_at).getTime();
      const pinnedTimeB = new Date(b.pinned_at || b.updated_at || b.created_at).getTime();
      if (pinnedTimeA !== pinnedTimeB) {
        return pinnedTimeB - pinnedTimeA;
      }
    }

    const timeA = new Date(a.last_message_at || a.updated_at || a.created_at).getTime();
    const timeB = new Date(b.last_message_at || b.updated_at || b.created_at).getTime();
    if (timeA !== timeB) {
      return timeB - timeA;
    }
    return b.id - a.id;
  });
};

const isPlaceholderConversation = (item: AIConversationSummary): boolean => {
  const title = (item.title || '').trim();
  const preview = (item.preview || '').trim();
  return item.message_count === 0 && !preview && (title === '' || title === '新对话');
};

const compactConversationsForDisplay = (items: AIConversationSummary[]): AIConversationSummary[] => {
  const sorted = sortConversations(items);
  const nonPlaceholder = sorted.filter((item) => !isPlaceholderConversation(item) || item.is_pinned);
  const placeholder = sorted.find((item) => isPlaceholderConversation(item) && !item.is_pinned);
  return placeholder ? [...nonPlaceholder, placeholder] : nonPlaceholder;
};

const syncConversationList = async (preferredId?: number | null): Promise<number | null> => {
  const list = compactConversationsForDisplay(await getAIConversations());

  conversations.value = list;

  let targetId = preferredId ?? activeConversationId.value ?? list[0]?.id ?? null;
  if (targetId && !list.some((item) => item.id === targetId)) {
    targetId = list[0]?.id ?? null;
  }

  activeConversationId.value = targetId;
  return targetId;
};

const scrollChatToBottom = (force = false) => {
  nextTick(() => {
    const el = scienceScrollRef.value;
    if (!el) return;
    if (!force && !autoScrollEnabled.value) return;
    el.scrollTop = el.scrollHeight;
    autoScrollEnabled.value = true;
    showScrollToBottom.value = false;
  });
};

const handleChatScroll = () => {
  const el = scienceScrollRef.value;
  if (!el) return;

  const distanceToBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
  const atBottom = distanceToBottom <= CHAT_SCROLL_THRESHOLD;
  autoScrollEnabled.value = atBottom;
  showScrollToBottom.value = !atBottom;
};

const scrollToLatest = () => {
  scrollChatToBottom(true);
};

const closeConversationMenu = () => {
  openedConversationMenuId.value = null;
};

const handleOutsideConversationMenuClick = () => {
  closeConversationMenu();
};

const toggleConversationMenu = (conversationId: number) => {
  openedConversationMenuId.value = openedConversationMenuId.value === conversationId ? null : conversationId;
};

const resetCitationExpandedState = () => {
  citationExpandedState.value = {};
};

const isCitationExpanded = (messageId: number): boolean => {
  return Boolean(citationExpandedState.value[messageId]);
};

const toggleCitationExpanded = (messageId: number) => {
  citationExpandedState.value = {
    ...citationExpandedState.value,
    [messageId]: !citationExpandedState.value[messageId],
  };
};

const pushScienceMessage = (
  role: ChatRole,
  content: string,
  status: ChatStatus,
  forceScroll = false,
): number => {
  const id = getLocalMessageId();
  scienceMessages.value.push({ id, role, content, status });
  if (forceScroll) {
    autoScrollEnabled.value = true;
  }
  scrollChatToBottom(forceScroll);
  return id;
};

const updateScienceMessage = (id: number, updater: (message: ChatMessage) => void) => {
  const target = scienceMessages.value.find((item) => item.id === id);
  if (!target) return;
  updater(target);
  scrollChatToBottom();
};

const pickProviderTag = (model?: string | null, source?: string | null): string => {
  if (model && model.trim()) {
    return model.trim();
  }
  if (source && source.trim()) {
    return source.trim();
  }
  return providerTag.value || 'chat';
};

const applyAssistantMeta = (assistantId: number, meta?: AIScienceStreamMeta | null) => {
  if (!meta) return;

  providerTag.value = pickProviderTag(meta.model, meta.source);
  updateScienceMessage(assistantId, (message) => {
    if (meta.source) {
      message.source = meta.source;
    }
    if (meta.model) {
      message.model = meta.model;
    }
    if (Array.isArray(meta.citations)) {
      message.citations = meta.citations;
    }
    if (meta.web_search_notice !== undefined) {
      message.webSearchNotice = meta.web_search_notice;
    }
  });
};

const mapApiMessage = (item: AIConversationMessage): ChatMessage => {
  return {
    id: item.id,
    role: item.role,
    content: item.content || '',
    reasoning: item.reasoning || undefined,
    source: item.source || undefined,
    model: item.model || undefined,
    citations: item.citations || [],
    webSearchNotice: item.web_search_notice ?? undefined,
    status: item.status === 'error' ? 'error' : 'done',
  };
};

const syncProviderTagFromMessages = () => {
  const latestAssistant = [...scienceMessages.value].reverse().find(
    (item) => item.role === 'assistant' && (item.model || item.source)
  );
  if (latestAssistant) {
    providerTag.value = pickProviderTag(latestAssistant.model, latestAssistant.source);
  }
};

const loadConversationMessages = async (conversationId: number) => {
  const detail = await getAIConversationDetail(conversationId);
  scienceMessages.value = detail.messages.map(mapApiMessage);
  resetCitationExpandedState();
  syncProviderTagFromMessages();
  autoScrollEnabled.value = true;
  showScrollToBottom.value = false;
  scrollChatToBottom(true);
};

const initializeConversations = async () => {
  if (conversationsReady.value || !shouldRender.value) {
    return;
  }

  conversationLoading.value = true;
  try {
    const targetId = await syncConversationList();
    if (targetId) {
      await loadConversationMessages(targetId);
    } else {
      scienceMessages.value = [];
      resetCitationExpandedState();
    }
    conversationsReady.value = true;
  } catch (error: any) {
    const detail = getErrorMessage(error, '请稍后重试');
    if (/network error|failed to fetch|load failed/i.test(detail.toLowerCase())) {
      ElMessage.error(`初始化会话失败：无法连接后端（当前 ${getApiBaseUrl()}），请确认后端已启动并检查前端来源地址/CORS 配置`);
    } else {
      ElMessage.error(`初始化会话失败：${detail}`);
    }
  } finally {
    conversationLoading.value = false;
  }
};

const ensureActiveConversation = async (): Promise<number | null> => {
  if (!conversationsReady.value) {
    await initializeConversations();
  }

  if (!activeConversationId.value) {
    conversationLoading.value = true;
    try {
      const created = await createAIConversation({});
      await syncConversationList(created.id);
      activeConversationId.value = created.id;
      scienceMessages.value = [];
      resetCitationExpandedState();
    } catch (error: any) {
      ElMessage.error(`创建会话失败：${getErrorMessage(error, '请稍后重试')}`);
      return null;
    } finally {
      conversationLoading.value = false;
    }
  }

  return activeConversationId.value;
};

const startNewConversation = async () => {
  if (scienceLoading.value) {
    ElMessage.warning('AI 生成中，暂不能新建会话');
    return;
  }

  conversationLoading.value = true;
  try {
    const created = await createAIConversation({});
    await syncConversationList(created.id);
    activeConversationId.value = created.id;
    scienceMessages.value = [];
    resetCitationExpandedState();
    open.value = true;
  } catch (error: any) {
    ElMessage.error(`新建会话失败：${getErrorMessage(error, '请稍后重试')}`);
  } finally {
    conversationLoading.value = false;
  }
};

const switchConversation = async (conversationId: number, force = false) => {
  if (editingHistoryConversationId.value !== null) {
    return;
  }

  closeConversationMenu();

  if (scienceLoading.value && !force) {
    ElMessage.warning('AI 生成中，暂不能切换会话');
    return;
  }

  if (!force && activeConversationId.value === conversationId && scienceMessages.value.length > 0) {
    return;
  }

  conversationSwitching.value = true;
  try {
    activeConversationId.value = conversationId;
    await loadConversationMessages(conversationId);
  } catch (error: any) {
    ElMessage.error(`加载会话失败：${getErrorMessage(error, '请稍后重试')}`);
  } finally {
    conversationSwitching.value = false;
  }
};

const beginEditHistoryTitle = (item: AIConversationSummary) => {
  if (conversationBusy.value) {
    return;
  }

  closeConversationMenu();

  editingHistoryConversationId.value = item.id;
  historyTitleDraft.value = item.title || '新对话';

  nextTick(() => {
    const input = document.querySelector('.history-title-editor input') as HTMLInputElement | null;
    input?.focus();
    input?.select();
  });
};

const cancelHistoryTitleEdit = () => {
  editingHistoryConversationId.value = null;
  historyTitleDraft.value = '';
};

const submitHistoryTitleEdit = async (item: AIConversationSummary) => {
  if (editingHistoryConversationId.value !== item.id) {
    return;
  }

  const nextTitle = historyTitleDraft.value.trim();
  const originalTitle = item.title || '新对话';

  if (!nextTitle) {
    ElMessage.warning('标题不能为空');
    historyTitleDraft.value = originalTitle;
    return;
  }

  if (nextTitle === originalTitle) {
    cancelHistoryTitleEdit();
    return;
  }

  conversationLoading.value = true;
  try {
    await renameAIConversation(item.id, nextTitle);
    await syncConversationList(item.id);
    ElMessage.success('会话已重命名');
    cancelHistoryTitleEdit();
  } catch (error: any) {
    ElMessage.error(`重命名失败：${getErrorMessage(error, '请稍后重试')}`);
  } finally {
    conversationLoading.value = false;
  }
};

type ConversationCommand = 'rename' | 'pin' | 'delete';

const toggleConversationPin = async (item: AIConversationSummary) => {
  if (conversationBusy.value) {
    ElMessage.warning('AI 生成中，暂不能调整置顶');
    return;
  }

  conversationLoading.value = true;
  try {
    await pinAIConversation(item.id, !item.is_pinned);
    await syncConversationList(item.id);
    ElMessage.success(item.is_pinned ? '已取消置顶' : '已置顶对话');
  } catch (error: any) {
    ElMessage.error(`置顶操作失败：${getErrorMessage(error, '请稍后重试')}`);
  } finally {
    conversationLoading.value = false;
  }
};

const deleteConversation = async (targetConversation?: AIConversationSummary | null) => {
  const item = targetConversation || activeConversation.value;
  if (!item) return;

  closeConversationMenu();

  try {
    await ElMessageBox.confirm('删除后不可恢复，确定继续吗？', '删除会话', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    });

    const deletingId = item.id;
    conversationLoading.value = true;

    await deleteAIConversation(deletingId);

    let nextId = await syncConversationList();
    if (!nextId) {
      const created = await createAIConversation({});
      nextId = created.id;
      await syncConversationList(nextId);
    }

    scienceMessages.value = [];
    resetCitationExpandedState();
    if (nextId) {
      await switchConversation(nextId, true);
    }

    ElMessage.success('会话已删除');
  } catch (error: any) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(`删除失败：${getErrorMessage(error, '请稍后重试')}`);
    }
  } finally {
    conversationLoading.value = false;
  }
};

const handleConversationCommand = async (command: string | number | object, item: AIConversationSummary) => {
  const action = String(command) as ConversationCommand;
  if (action === 'rename') {
    beginEditHistoryTitle(item);
    return;
  }
  if (action === 'pin') {
    await toggleConversationPin(item);
    return;
  }
  if (action === 'delete') {
    await deleteConversation(item);
  }
};

const handleConversationMenuAction = async (command: ConversationCommand, item: AIConversationSummary) => {
  closeConversationMenu();
  await handleConversationCommand(command, item);
};

const insertAssistantContent = (content: string) => {
  const normalized = (content || '').trim();
  if (!normalized) return;

  if (!canInsertIntoTeaching.value) {
    ElMessage.warning('未检测到可编辑的教学文章，请先在教学内容页打开文章编辑器');
    return;
  }

  window.dispatchEvent(new CustomEvent('ai-teaching-insert-content', {
    detail: { content: normalized },
  }));
};

const handleTeachingInsertAvailability = (event: Event) => {
  const detail = (event as CustomEvent<{ enabled?: boolean }>).detail;
  canInsertIntoTeaching.value = Boolean(detail?.enabled);
};

const askScience = async (questionOverride?: string) => {
  const question = (questionOverride ?? scienceQuestion.value).trim();
  if (!question) return;

  open.value = true;

  const conversationId = await ensureActiveConversation();
  if (!conversationId) {
    return;
  }

  const requestPayload: AIConversationAskRequest = {
    question,
    enable_deep_thinking: deepThinkingEnabled.value,
    enable_web_search: smartSearchEnabled.value,
  };

  if (!questionOverride) {
    scienceQuestion.value = '';
  }

  pushScienceMessage('user', question, 'done', true);
  const assistantId = pushScienceMessage('assistant', '', 'streaming', true);

  scienceLoading.value = true;
  let streamedAnyToken = false;

  if (scienceAbortController) {
    scienceAbortController.abort();
  }
  const currentController = new AbortController();
  scienceAbortController = currentController;

  try {
    await streamScienceAssistantInConversation(
      conversationId,
      requestPayload,
      (text, reasoning) => {
        streamedAnyToken = true;
        updateScienceMessage(assistantId, (message) => {
          message.content += text;
          if (reasoning) {
            message.reasoning = (message.reasoning || '') + reasoning;
          }
          message.status = 'streaming';
        });
      },
      (meta) => {
        applyAssistantMeta(assistantId, meta);
      },
      { signal: currentController.signal }
    );

    if (!streamedAnyToken) {
      const response = await askScienceAssistantInConversation(conversationId, requestPayload);
      providerTag.value = pickProviderTag(response.model, response.source);
      updateScienceMessage(assistantId, (message) => {
        message.content = response.answer;
        message.source = response.source;
        message.model = response.model;
        message.citations = response.citations || [];
        message.webSearchNotice = response.web_search_notice;
        message.status = 'done';
      });
    } else {
      updateScienceMessage(assistantId, (message) => {
        message.status = 'done';
      });
    }
  } catch (error: any) {
    if (error?.name === 'AbortError') {
      updateScienceMessage(assistantId, (message) => {
        message.status = 'done';
        if (!message.content) {
          message.content = '已停止生成';
        }
      });
      return;
    }

    if (streamedAnyToken) {
      updateScienceMessage(assistantId, (message) => {
        message.status = 'done';
      });
      return;
    }

    try {
      const fallback = await askScienceAssistantInConversation(conversationId, requestPayload);
      providerTag.value = pickProviderTag(fallback.model, fallback.source);
      updateScienceMessage(assistantId, (message) => {
        message.content = fallback.answer;
        message.source = fallback.source;
        message.model = fallback.model;
        message.citations = fallback.citations || [];
        message.webSearchNotice = fallback.web_search_notice;
        message.status = 'done';
      });
    } catch (fallbackError: any) {
      updateScienceMessage(assistantId, (message) => {
        message.content = getErrorMessage(fallbackError, 'AI 助手暂时不可用，请稍后重试');
        message.status = 'error';
      });
    }
  } finally {
    if (scienceAbortController === currentController) {
      scienceAbortController = null;
    }
    scienceLoading.value = false;

    try {
      await syncConversationList(conversationId);
    } catch {
      // ignore list refresh failures to keep chat usable
    }
  }
};

const stopScience = () => {
  if (scienceAbortController) {
    scienceAbortController.abort();
  }
};

watch([deepThinkingEnabled, smartSearchEnabled], ([deepThinking, smartSearch]) => {
  if (typeof window === 'undefined') return;
  window.sessionStorage.setItem(DEEP_THINKING_SESSION_KEY, deepThinking ? '1' : '0');
  window.sessionStorage.setItem(SMART_SEARCH_SESSION_KEY, smartSearch ? '1' : '0');
});

watch(open, (value) => {
  if (value) {
    void initializeConversations();
  }
});

watch(activeConversationId, () => {
  cancelHistoryTitleEdit();
});

watch(openedConversationMenuId, (menuId) => {
  if (typeof window === 'undefined') {
    return;
  }

  window.removeEventListener('click', handleOutsideConversationMenuClick);

  if (menuId !== null) {
    window.addEventListener('click', handleOutsideConversationMenuClick);
    return;
  }
});

watch(
  () => route.path,
  (path) => {
    syncAuthToken();
    if (path === '/login' || path === '/display') {
      open.value = false;
    }
  }
);

onMounted(() => {
  syncAuthToken();

  if (typeof window !== 'undefined') {
    deepThinkingEnabled.value = window.sessionStorage.getItem(DEEP_THINKING_SESSION_KEY) === '1';
    smartSearchEnabled.value = window.sessionStorage.getItem(SMART_SEARCH_SESSION_KEY) === '1';
    window.addEventListener('focus', syncAuthToken);
    window.addEventListener('storage', syncAuthToken);
  }

  if (shouldRender.value) {
    void initializeConversations();
  }

  window.addEventListener('ai-teaching-insert-availability', handleTeachingInsertAvailability as EventListener);
});

onUnmounted(() => {
  if (scienceAbortController) {
    scienceAbortController.abort();
  }

  if (typeof window !== 'undefined') {
    window.removeEventListener('focus', syncAuthToken);
    window.removeEventListener('storage', syncAuthToken);
    window.removeEventListener('click', handleOutsideConversationMenuClick);
  }

  window.removeEventListener('ai-teaching-insert-availability', handleTeachingInsertAvailability as EventListener);
});
</script>

<style scoped>
.ai-float-root {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 1990;
  --panel-width: min(920px, calc(100vw - 32px));
}

.ai-fab {
  width: 56px;
  height: 56px;
  border: none;
  background: linear-gradient(140deg, var(--color-plant-500), var(--color-plant-700));
  box-shadow: var(--shadow-soft-hover);
  position: relative;
}

.ai-fab::after {
  content: '';
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  border: 1px solid rgba(45, 157, 120, 0.3);
  animation: fabPulse 2.4s ease-out infinite;
}

.ai-float-panel {
  position: absolute;
  right: 0;
  bottom: 64px;
  width: var(--panel-width);
  height: min(82vh, 760px);
  max-height: 82vh;
  border-radius: 18px;
  padding: 12px;
  border: 1px solid var(--el-border-color-light);
  background:
    linear-gradient(160deg, var(--glass-bg-strong), color-mix(in srgb, var(--bg-card) 88%, transparent)),
    radial-gradient(circle at 0 0, var(--layout-glow-left), transparent 38%);
  box-shadow: var(--shadow-soft-hover);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.ai-float-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 2px 2px 8px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-plant-500) 0%, var(--color-plant-700) 100%);
  box-shadow: 0 0 0 4px rgba(45, 157, 120, 0.15);
}

.title-text {
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: 0.01em;
}

.header-actions :deep(.el-button) {
  border-radius: 999px;
}

.ai-float-body {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.conversation-pane {
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  background: var(--glass-bg);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.conversation-pane-header {
  padding: 10px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.conversation-pane-header :deep(.el-button) {
  width: 100%;
}

.conversation-list {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.conversation-item {
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  background: var(--bg-card);
  display: flex;
  position: relative;
  z-index: 0;
  align-items: center;
  gap: 6px;
  padding: 4px 6px;
  transition: all 0.2s ease;
}

.conversation-item.is-menu-open {
  z-index: 60;
}

.conversation-item:hover {
  transform: translateY(-1px);
  border-color: var(--el-border-color);
}

.conversation-main {
  border: none;
  background: transparent;
  flex: 1 1 auto;
  width: auto;
  min-width: 0;
  text-align: left;
  padding: 6px;
  cursor: pointer;
}

.conversation-main:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.conversation-menu-wrap {
  flex: 0 0 auto;
  position: relative;
  z-index: 80;
}

.conversation-inline-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 136px;
  padding: 4px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  background: var(--bg-card);
  box-shadow: 0 8px 22px rgba(31, 98, 61, 0.2);
  z-index: 90;
}

.conversation-menu-item {
  width: 100%;
  border: none;
  background: transparent;
  text-align: left;
  padding: 7px 8px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  color: var(--text-secondary);
}

.conversation-menu-item:hover {
  background: var(--el-fill-color-light);
}

.conversation-menu-item-danger {
  color: #c0382f;
}

.conversation-menu-item-danger:hover {
  background: rgba(214, 66, 56, 0.12);
}

.conversation-more-btn {
  opacity: 0.82;
  visibility: visible;
  pointer-events: auto;
  color: var(--text-tertiary);
  transition: opacity 0.16s ease;
}

.conversation-item:hover .conversation-more-btn,
.conversation-item.is-active .conversation-more-btn,
.conversation-item:focus-within .conversation-more-btn {
  opacity: 1;
}

.conversation-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.conversation-item.is-active {
  border-color: var(--el-color-primary);
  box-shadow: 0 6px 16px rgba(31, 98, 61, 0.14);
  background: color-mix(in srgb, var(--el-fill-color-light) 64%, var(--bg-card));
}

.conversation-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main);
  line-height: 1.4;
  min-width: 0;
  flex: 1;
  word-break: break-word;
}

.history-title-editor {
  width: 100%;
}

.chat-pane {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.conversation-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.conversation-title {
  color: var(--text-main);
  font-size: 14px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quick-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  align-items: center;
}

.quick-tag {
  cursor: pointer;
  border-radius: 999px;
}

.chat-window {
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  padding: 10px;
  overflow: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  background: var(--glass-bg);
  flex: 1;
  min-height: 0;
}

.scroll-bottom-btn {
  align-self: flex-end;
  margin-top: 8px;
  border-radius: 999px;
}

.chat-empty {
  color: var(--text-tertiary);
  font-size: 12px;
  line-height: 1.6;
}

.chat-reasoning {
  margin-bottom: 12px;
  background: rgba(45, 157, 120, 0.05);
  border: 1px solid rgba(45, 157, 120, 0.15);
  border-radius: 8px;
  padding: 8px;
}

.chat-reasoning summary {
  cursor: pointer;
  color: var(--color-plant-600);
  font-weight: 600;
  font-size: 0.85rem;
  user-select: none;
  outline: none;
}

.reasoning-content {
  margin-top: 8px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  white-space: pre-wrap;
  border-left: 2px solid var(--color-plant-500);
  padding-left: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.chat-msg {
  margin-bottom: 10px;
}

.chat-msg:last-child {
  margin-bottom: 0;
}

.chat-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-tertiary);
  margin-bottom: 4px;
}

.chat-msg.is-user .chat-meta {
  justify-content: flex-end;
}

.chat-bubble {
  max-width: 88%;
  border-radius: 12px;
  padding: 8px 10px;
  line-height: 1.55;
  white-space: normal;
  word-break: break-word;
  overflow-wrap: anywhere;
  font-size: 13px;
}

.chat-plain-text {
  white-space: pre-wrap;
}

.chat-msg.is-user .chat-bubble {
  margin-left: auto;
  color: var(--el-color-white);
  background: linear-gradient(135deg, var(--color-plant-500), var(--color-plant-700));
}

.chat-msg.is-assistant .chat-bubble {
  background: var(--bg-card);
  border: 1px solid var(--el-border-color-light);
  color: var(--text-main);
}

.chat-bubble.is-error {
  background: color-mix(in srgb, var(--el-color-danger) 12%, transparent);
  color: var(--el-color-danger);
}

.typing {
  display: inline-block;
  margin-left: 2px;
  animation: blink 1s steps(1, end) infinite;
}

.search-note {
  margin-top: 6px;
  color: var(--text-tertiary);
  font-size: 12px;
}

.source-wrap {
  margin-top: 8px;
}

.source-toggle {
  padding: 0;
  font-size: 12px;
}

.source-list {
  margin-top: 8px;
  padding: 8px;
  border: 1px dashed rgba(45, 157, 120, 0.32);
  border-radius: 10px;
  background: color-mix(in srgb, var(--el-fill-color-light) 72%, transparent);
}

.source-title {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.source-link {
  display: block;
  font-size: 12px;
  color: var(--el-color-primary);
  text-decoration: none;
  margin-bottom: 6px;
  line-height: 1.45;
}

.source-link:hover {
  text-decoration: underline;
}

.source-link-title {
  display: block;
  font-weight: 600;
}

.source-link-snippet {
  display: block;
  color: var(--text-secondary);
  margin-top: 2px;
}

.source-link-url {
  display: block;
  color: var(--text-tertiary);
  margin-top: 1px;
  word-break: break-all;
}

.chat-actions {
  margin-top: 6px;
  display: flex;
  justify-content: flex-start;
  gap: 8px;
}

.insert-tip {
  color: var(--text-tertiary);
  font-size: 12px;
}

.input-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 8px;
  margin-top: 10px;
}

.option-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 8px;
}

.option-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 12px;
}

.ai-float-pop-enter-active,
.ai-float-pop-leave-active {
  transition: all 0.22s ease;
}

.ai-float-pop-enter-from,
.ai-float-pop-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.98);
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.2s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

@keyframes blink {
  0%, 49% {
    opacity: 1;
  }
  50%, 100% {
    opacity: 0;
  }
}

@keyframes fabPulse {
  0% {
    transform: scale(1);
    opacity: 0.9;
  }
  70% {
    transform: scale(1.16);
    opacity: 0;
  }
  100% {
    transform: scale(1.16);
    opacity: 0;
  }
}

@media (max-width: 920px) {
  .ai-float-body {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .conversation-pane {
    max-height: 210px;
  }

  .chat-window {
    min-height: 0;
  }
}

@media (max-width: 768px) {
  .ai-float-root {
    left: 12px;
    right: 12px;
    bottom: 12px;
    --panel-width: calc(100vw - 24px);
  }

  .ai-float-panel {
    right: 0;
    bottom: 66px;
    max-height: 82vh;
  }

  .chat-bubble {
    max-width: 100%;
  }

  .conversation-more-btn {
    opacity: 1;
    visibility: visible;
    pointer-events: auto;
  }

  .input-row {
    grid-template-columns: 1fr;
  }
}
</style>
