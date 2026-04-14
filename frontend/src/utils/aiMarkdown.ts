import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js/lib/common';

const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: true,
  highlight: (rawCode: string, rawLang: string) => {
    const code = rawCode || '';
    const lang = (rawLang || '').trim().toLowerCase();

    try {
      if (lang && hljs.getLanguage(lang)) {
        const highlighted = hljs.highlight(code, { language: lang, ignoreIllegals: true }).value;
        return `<pre class="hljs"><code class="hljs language-${lang}">${highlighted}</code></pre>`;
      }

      const highlighted = hljs.highlightAuto(code).value;
      return `<pre class="hljs"><code class="hljs">${highlighted}</code></pre>`;
    } catch {
      return `<pre class="hljs"><code class="hljs">${md.utils.escapeHtml(code)}</code></pre>`;
    }
  },
});

const defaultLinkOpen = md.renderer.rules.link_open;
md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  token.attrSet('target', '_blank');
  token.attrSet('rel', 'noopener noreferrer nofollow');
  return defaultLinkOpen ? defaultLinkOpen(tokens, idx, options, env, self) : self.renderToken(tokens, idx, options);
};

const defaultFence = md.renderer.rules.fence;
md.renderer.rules.fence = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  const info = (token.info || '').trim().toLowerCase();

  if (info === 'mermaid') {
    const source = token.content || '';
    const encoded = encodeURIComponent(source);
    const escaped = md.utils.escapeHtml(source);
    return `<div class="ai-mermaid-holder"><pre class="ai-mermaid-source" data-mermaid-source="${encoded}">${escaped}</pre></div>`;
  }

  return defaultFence ? defaultFence(tokens, idx, options, env, self) : self.renderToken(tokens, idx, options);
};

const decorateTaskList = (html: string): string => {
  const withTaskItems = html.replace(
    /<li>\s*\[([ xX])\]\s*([\s\S]*?)<\/li>/g,
    (_match, marker: string, body: string) => {
      const checked = marker.toLowerCase() === 'x' ? ' checked' : '';
      return `<li class="ai-task-list-item"><label><input type="checkbox" disabled${checked} /><span>${body}</span></label></li>`;
    }
  );

  return withTaskItems.replace(/<ul>\s*(<li class="ai-task-list-item">)/g, '<ul class="ai-task-list">$1');
};

export const renderAssistantMarkdown = (content: string): string => {
  const normalized = (content || '').trim();
  if (!normalized) {
    return '';
  }

  return decorateTaskList(md.render(normalized));
};
