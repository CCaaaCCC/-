import { reactive } from 'vue';

type PaginationState = {
  page: number;
  page_size: number;
  total: number;
};

export function usePagination(initialPage = 1, initialPageSize = 20) {
  const pagination = reactive<PaginationState>({
    page: initialPage,
    page_size: initialPageSize,
    total: 0,
  });

  const clampPage = () => {
    const safePageSize = Math.max(1, pagination.page_size);
    const totalPages = Math.max(1, Math.ceil(pagination.total / safePageSize));
    if (pagination.page < 1) {
      pagination.page = 1;
      return;
    }
    if (pagination.page > totalPages) {
      pagination.page = totalPages;
    }
  };

  const resetPage = () => {
    pagination.page = 1;
  };

  const setTotal = (value: number) => {
    pagination.total = Number.isFinite(value) ? Math.max(0, value) : 0;
    clampPage();
  };

  const changePageSize = (size: number) => {
    pagination.page_size = Math.max(1, size);
    pagination.page = 1;
    clampPage();
  };

  return {
    pagination,
    resetPage,
    setTotal,
    changePageSize,
  };
}
