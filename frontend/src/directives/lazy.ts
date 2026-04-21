import type { Directive, DirectiveBinding } from 'vue';

type LazyImageValue =
  | string
  | {
      src: string;
      loadingSrc?: string;
      errorSrc?: string;
      rootMargin?: string;
    };

type LazyImageElement = HTMLImageElement & {
  __lazyCleanup__?: () => void;
  __lazyBoundSrc__?: string;
};

const TRANSPARENT_PIXEL = 'data:image/gif;base64,R0lGODlhAQABAAAAACw=';
const DEFAULT_ROOT_MARGIN = '160px';

const cleanupObserver = (el: LazyImageElement) => {
  if (el.__lazyCleanup__) {
    el.__lazyCleanup__();
    el.__lazyCleanup__ = undefined;
  }
};

const parseLazyValue = (value: LazyImageValue) => {
  if (typeof value === 'string') {
    return {
      src: value,
      loadingSrc: '',
      errorSrc: '',
      rootMargin: DEFAULT_ROOT_MARGIN,
    };
  }

  return {
    src: value?.src || '',
    loadingSrc: value?.loadingSrc || '',
    errorSrc: value?.errorSrc || '',
    rootMargin: value?.rootMargin || DEFAULT_ROOT_MARGIN,
  };
};

const preloadAndSwap = (el: LazyImageElement, src: string, errorSrc: string) => {
  if (!src || el.__lazyBoundSrc__ === src) {
    return;
  }

  const img = new Image();
  img.onload = () => {
    el.src = src;
    el.__lazyBoundSrc__ = src;
  };
  img.onerror = () => {
    if (errorSrc) {
      el.src = errorSrc;
    }
  };
  img.src = src;
};

const bindLazyImage = (el: LazyImageElement, binding: DirectiveBinding<LazyImageValue>) => {
  cleanupObserver(el);

  const { src, loadingSrc, errorSrc, rootMargin } = parseLazyValue(binding.value);
  if (!src) {
    return;
  }

  if (loadingSrc) {
    el.src = loadingSrc;
  } else if (!el.getAttribute('src')) {
    el.src = TRANSPARENT_PIXEL;
  }

  el.loading = 'lazy';

  if (typeof window === 'undefined' || !('IntersectionObserver' in window)) {
    preloadAndSwap(el, src, errorSrc);
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting || entry.intersectionRatio > 0) {
          preloadAndSwap(el, src, errorSrc);
          observer.unobserve(el);
          observer.disconnect();
          break;
        }
      }
    },
    { rootMargin },
  );

  observer.observe(el);
  el.__lazyCleanup__ = () => observer.disconnect();
};

const getSourceKey = (value: LazyImageValue | undefined) => {
  if (!value) {
    return '';
  }
  if (typeof value === 'string') {
    return value;
  }
  return value.src || '';
};

const lazyDirective: Directive<HTMLImageElement, LazyImageValue> = {
  mounted(el, binding) {
    bindLazyImage(el as LazyImageElement, binding);
  },
  updated(el, binding) {
    if (getSourceKey(binding.value) !== getSourceKey(binding.oldValue)) {
      bindLazyImage(el as LazyImageElement, binding);
    }
  },
  unmounted(el) {
    cleanupObserver(el as LazyImageElement);
  },
};

export default lazyDirective;
