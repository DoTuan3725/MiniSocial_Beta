import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { FileX } from 'lucide-react';
import { postApi } from '../api/endpoints';
import PostCard from '../components/PostCard';
import { EmptyState, PageLoader } from '../components/ui';

export default function PostPage() {
  const { postId } = useParams();
  const q = useQuery({ queryKey: ['post', postId], queryFn: () => postApi.detail(postId), retry: false });
  return (
    <div className="mx-auto max-w-[640px]">
      {q.isLoading && <PageLoader />}
      {q.isError && (
        <EmptyState icon={FileX} title="Không xem được bài viết">
          Bài viết đã bị xóa hoặc bạn không có quyền xem.
        </EmptyState>
      )}
      {q.data && <PostCard post={q.data} queryKeys={[['post', postId]]} />}
    </div>
  );
}
