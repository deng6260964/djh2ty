import { useState, useCallback } from 'react'
import { PAGE_SIZE } from '../utils/constants'

interface PaginationState {
  page: number
  pageSize: number
  total: number
}

interface UsePaginationReturn {
  page: number
  pageSize: number
  total: number
  setTotal: (total: number) => void
  onPageChange: (page: number, pageSize?: number) => void
  reset: () => void
  paginationProps: {
    current: number
    pageSize: number
    total: number
    onChange: (page: number, pageSize?: number) => void
    showSizeChanger: boolean
    showTotal: (total: number) => string
    pageSizeOptions: string[]
  }
}

export const usePagination = (defaultPageSize = PAGE_SIZE): UsePaginationReturn => {
  const [pagination, setPagination] = useState<PaginationState>({
    page: 1,
    pageSize: defaultPageSize,
    total: 0,
  })

  const setTotal = useCallback((total: number) => {
    setPagination((prev) => ({ ...prev, total }))
  }, [])

  const onPageChange = useCallback((page: number, pageSize?: number) => {
    setPagination((prev) => ({
      ...prev,
      page,
      pageSize: pageSize || prev.pageSize,
    }))
  }, [])

  const reset = useCallback(() => {
    setPagination((prev) => ({ ...prev, page: 1 }))
  }, [])

  return {
    page: pagination.page,
    pageSize: pagination.pageSize,
    total: pagination.total,
    setTotal,
    onPageChange,
    reset,
    paginationProps: {
      current: pagination.page,
      pageSize: pagination.pageSize,
      total: pagination.total,
      onChange: onPageChange,
      showSizeChanger: true,
      showTotal: (total: number) => `共 ${total} 条`,
      pageSizeOptions: ['10', '20', '50'],
    },
  }
}
