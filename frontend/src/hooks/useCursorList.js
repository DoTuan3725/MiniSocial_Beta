import { useInfiniteQuery } from '@tanstack/react-query';
import { cursorOf } from '../api/endpoints';

/** Bọc useInfiniteQuery cho API phân trang con trỏ { results, next }. */
export function useCursorList(key, fetcher, options = {}) {
  const query = useInfiniteQuery({
    queryKey: key,
    queryFn: ({ pageParam }) => fetcher(pageParam),
    initialPageParam: undefined,
    getNextPageParam: (last) => cursorOf(last?.next),
    ...options,
  });
  const items = query.data?.pages.flatMap((p) => p.results) ?? [];
  const firstPage = query.data?.pages[0];
  return { ...query, items, firstPage };
}
