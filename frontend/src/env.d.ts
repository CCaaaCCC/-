/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module 'katex/contrib/auto-render' {
  const renderMathInElement: (element: HTMLElement, options?: Record<string, unknown>) => void;
  export default renderMathInElement;
}
