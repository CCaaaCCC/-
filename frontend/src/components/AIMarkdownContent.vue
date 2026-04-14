<template>
  <div ref="containerRef" class="ai-markdown-content" v-html="renderedHtml"></div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import 'katex/dist/katex.min.css';
import { renderAssistantMarkdown } from '../utils/aiMarkdown';

const props = defineProps<{
  content: string;
}>();

const containerRef = ref<HTMLElement | null>(null);
const renderedHtml = computed(() => renderAssistantMarkdown(props.content || ''));

type MermaidRuntime = typeof import('mermaid')['default'];

let mermaidRuntimePromise: Promise<MermaidRuntime> | null = null;
let mathRendererPromise: Promise<(element: HTMLElement, options?: Record<string, unknown>) => void> | null = null;
let mermaidReady = false;

const loadMermaidRuntime = async (): Promise<MermaidRuntime> => {
  if (!mermaidRuntimePromise) {
    mermaidRuntimePromise = import('mermaid').then((module) => module.default);
  }
  return mermaidRuntimePromise;
};

const loadMathRenderer = async (): Promise<(element: HTMLElement, options?: Record<string, unknown>) => void> => {
  if (!mathRendererPromise) {
    mathRendererPromise = import('katex/contrib/auto-render').then((module) => module.default);
  }
  return mathRendererPromise;
};

const escapeHtml = (value: string): string => {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
};

const ensureMermaid = async (): Promise<MermaidRuntime> => {
  const runtime = await loadMermaidRuntime();
  if (mermaidReady) {
    return runtime;
  }

  const resolvedTheme = typeof document !== 'undefined'
    ? document.documentElement.getAttribute('data-theme-resolved')
    : null;

  runtime.initialize({
    startOnLoad: false,
    securityLevel: 'strict',
    theme: resolvedTheme === 'dark' ? 'dark' : 'default',
  });
  mermaidReady = true;
  return runtime;
};

const renderMathBlocks = async (root: HTMLElement) => {
  const rawText = root.textContent || '';
  if (!rawText.includes('$')) {
    return;
  }

  const renderMathInElement = await loadMathRenderer();
  renderMathInElement(root, {
    delimiters: [
      { left: '$$', right: '$$', display: true },
      { left: '$', right: '$', display: false },
    ],
    throwOnError: false,
    strict: 'ignore',
  });
};

const renderMermaidBlocks = async (root: HTMLElement) => {
  const blocks = Array.from(root.querySelectorAll<HTMLElement>('pre.ai-mermaid-source[data-mermaid-source]'));
  if (!blocks.length) {
    return;
  }

  const mermaid = await ensureMermaid();

  for (let index = 0; index < blocks.length; index += 1) {
    const block = blocks[index];
    let source = '';
    try {
      source = decodeURIComponent(block.dataset.mermaidSource || '').trim();
    } catch {
      source = (block.textContent || '').trim();
    }

    if (!source) {
      continue;
    }

    const elementId = `ai-mermaid-${Date.now()}-${index}`;
    try {
      const { svg } = await mermaid.render(elementId, source);
      const wrapper = document.createElement('div');
      wrapper.className = 'ai-mermaid-rendered';
      wrapper.innerHTML = svg;
      block.replaceWith(wrapper);
    } catch {
      block.classList.add('ai-mermaid-fallback');
      block.innerHTML = escapeHtml(source);
    }
  }
};

const enhanceRenderedContent = async () => {
  await nextTick();
  const root = containerRef.value;
  if (!root) {
    return;
  }

  try {
    await renderMathBlocks(root);
  } catch {
    // Keep the markdown readable even if formula rendering fails.
  }

  await renderMermaidBlocks(root);
};

watch(renderedHtml, () => {
  void enhanceRenderedContent();
});

onMounted(() => {
  void enhanceRenderedContent();
});
</script>

<style scoped>
.ai-markdown-content {
  color: inherit;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.ai-markdown-content :deep(*) {
  max-width: 100%;
}

.ai-markdown-content :deep(p),
.ai-markdown-content :deep(ul),
.ai-markdown-content :deep(ol),
.ai-markdown-content :deep(blockquote),
.ai-markdown-content :deep(table),
.ai-markdown-content :deep(pre) {
  margin: 0 0 0.6rem;
}

.ai-markdown-content :deep(p:last-child),
.ai-markdown-content :deep(ul:last-child),
.ai-markdown-content :deep(ol:last-child),
.ai-markdown-content :deep(blockquote:last-child),
.ai-markdown-content :deep(table:last-child),
.ai-markdown-content :deep(pre:last-child) {
  margin-bottom: 0;
}

.ai-markdown-content :deep(h1),
.ai-markdown-content :deep(h2),
.ai-markdown-content :deep(h3),
.ai-markdown-content :deep(h4) {
  margin: 0.8rem 0 0.5rem;
  line-height: 1.35;
  color: var(--text-main);
}

.ai-markdown-content :deep(h1) {
  font-size: 1.08rem;
}

.ai-markdown-content :deep(h2) {
  font-size: 1rem;
}

.ai-markdown-content :deep(h3),
.ai-markdown-content :deep(h4) {
  font-size: 0.94rem;
}

.ai-markdown-content :deep(blockquote) {
  border-left: 3px solid color-mix(in srgb, var(--color-plant-500) 70%, transparent);
  padding: 0.2rem 0 0.2rem 0.65rem;
  color: var(--text-secondary);
}

.ai-markdown-content :deep(code) {
  font-family: 'Cascadia Mono', 'JetBrains Mono', Consolas, monospace;
  font-size: 0.85em;
}

.ai-markdown-content :deep(p code),
.ai-markdown-content :deep(li code),
.ai-markdown-content :deep(blockquote code) {
  background: color-mix(in srgb, var(--el-fill-color-light) 72%, transparent);
  border-radius: 6px;
  padding: 0.12rem 0.34rem;
}

.ai-markdown-content :deep(pre.hljs) {
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  background: color-mix(in srgb, var(--bg-card) 90%, var(--el-fill-color-darker));
  padding: 0.68rem 0.75rem;
  overflow-x: auto;
}

.ai-markdown-content :deep(pre.hljs code.hljs) {
  color: var(--text-main);
  background: transparent;
  padding: 0;
}

.ai-markdown-content :deep(.hljs-keyword),
.ai-markdown-content :deep(.hljs-selector-tag),
.ai-markdown-content :deep(.hljs-title.function_) {
  color: #2d7d57;
}

.ai-markdown-content :deep(.hljs-string),
.ai-markdown-content :deep(.hljs-title),
.ai-markdown-content :deep(.hljs-section) {
  color: #a24c0f;
}

.ai-markdown-content :deep(.hljs-number),
.ai-markdown-content :deep(.hljs-literal),
.ai-markdown-content :deep(.hljs-variable) {
  color: #6f42c1;
}

.ai-markdown-content :deep(.hljs-comment),
.ai-markdown-content :deep(.hljs-quote) {
  color: var(--text-tertiary);
}

.ai-markdown-content :deep(.ai-task-list) {
  list-style: none;
  padding-left: 0.1rem;
}

.ai-markdown-content :deep(.ai-task-list-item label) {
  display: inline-flex;
  align-items: flex-start;
  gap: 0.45rem;
}

.ai-markdown-content :deep(.ai-task-list-item input[type='checkbox']) {
  margin-top: 0.2rem;
}

.ai-markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
}

.ai-markdown-content :deep(th),
.ai-markdown-content :deep(td) {
  border: 1px solid var(--el-border-color-light);
  padding: 0.42rem 0.5rem;
  text-align: left;
}

.ai-markdown-content :deep(th) {
  background: color-mix(in srgb, var(--el-fill-color-light) 72%, transparent);
  color: var(--text-main);
}

.ai-markdown-content :deep(.katex-display) {
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 0.2rem;
}

.ai-markdown-content :deep(.ai-mermaid-holder) {
  margin: 0.55rem 0;
}

.ai-markdown-content :deep(.ai-mermaid-rendered) {
  overflow-x: auto;
  padding: 0.4rem;
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  background: color-mix(in srgb, var(--bg-card) 88%, var(--el-fill-color-light));
}

.ai-markdown-content :deep(.ai-mermaid-fallback) {
  border: 1px dashed var(--el-border-color);
  border-radius: 10px;
  padding: 0.55rem;
  color: var(--text-secondary);
  white-space: pre-wrap;
}
</style>
