import { useCallback, useEffect, useState } from 'react'

export type PagedParams = {
  page?: number
  limit?: number
}

type Fetcher<TParams extends PagedParams> = (
  params: TParams,
) => Promise<{ total: number; page: number; limit: number } & Record<string, unknown>>

type UsePagedListOptions<TParams extends PagedParams> = {
  fetcher: Fetcher<TParams>
  itemsKey: string
  initialParams: TParams
  /** Debounce delay (ms) for changes to non-pagination params (e.g. search). 0 disables. */
  debounceMs?: number
}

export function usePagedList<TItem, TParams extends PagedParams>(
  options: UsePagedListOptions<TParams>,
) {
  const { fetcher, itemsKey, initialParams, debounceMs = 350 } = options

  const [params, setParamsState] = useState<TParams>(initialParams)
  const [items, setItems] = useState<TItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const load = useCallback(
    async (next: TParams) => {
      try {
        setLoading(true)
        setError(null)
        const res = await fetcher(next)
        setItems((res[itemsKey] as TItem[]) ?? [])
        setTotal(res.total)
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'))
      } finally {
        setLoading(false)
      }
    },
    [fetcher, itemsKey],
  )

  useEffect(() => {
    if (debounceMs <= 0) {
      load(params)
      return
    }
    const id = setTimeout(() => load(params), debounceMs)
    return () => clearTimeout(id)
  }, [params, load, debounceMs])

  const setPage = useCallback(
    (page: number) => setParamsState((p) => ({ ...p, page })),
    [],
  )

  const setLimit = useCallback(
    (limit: number) =>
      setParamsState((p) => ({ ...p, limit, page: 1 })),
    [],
  )

  const setParams = useCallback(
    (updater: (prev: TParams) => TParams) =>
      setParamsState((prev) => ({ ...updater(prev), page: 1 })),
    [],
  )

  const refetch = useCallback(() => load(params), [load, params])

  return {
    items,
    total,
    page: params.page ?? 1,
    limit: params.limit ?? 10,
    params,
    loading,
    error,
    setPage,
    setLimit,
    setParams,
    refetch,
  }
}
