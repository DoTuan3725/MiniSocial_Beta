import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { postApi } from '../api/endpoints';
import { errorMessage } from '../lib/errors';
import { timeAgo } from '../lib/format';
import { useAuth } from '../store/auth';
import { toast } from '../store/toast';
import { Avatar, Spinner, UserLink } from './ui';

function CommentForm({ onSubmit, initial = '', placeholder = 'Viết bình luận...', autoFocus, busy }) {
  const [text, setText] = useState(initial);
  const user = useAuth((s) => s.user);
  return (
    <form
      className="flex items-start gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        if (!text.trim()) return;
        onSubmit(text, () => setText(''));
      }}
    >
      <Avatar user={user} size={32} />
      <input
        className="input rounded-full py-2"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        maxLength={2000}
        aria-label={placeholder}
      />
      <button className="btn-primary rounded-full px-3 py-2" disabled={busy || !text.trim()}>
        Gửi
      </button>
    </form>
  );
}

function CommentNode({ node, postId, depth }) {
  const qc = useQueryClient();
  const [replying, setReplying] = useState(false);
  const [editing, setEditing] = useState(false);
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['comments', postId] });
    qc.invalidateQueries({ queryKey: ['post-count', postId] });
  };
  const reply = useMutation({
    mutationFn: ({ text }) => postApi.comment(postId, text, node.id),
    onSuccess: refresh,
    onError: (e) => toast.error(errorMessage(e)),
  });
  const edit = useMutation({
    mutationFn: (text) => postApi.editComment(node.id, text),
    onSuccess: () => {
      setEditing(false);
      refresh();
    },
    onError: (e) => toast.error(errorMessage(e)),
  });
  const remove = useMutation({
    mutationFn: () => postApi.deleteComment(node.id),
    onSuccess: refresh,
    onError: (e) => toast.error(errorMessage(e)),
  });

  return (
    <div className="flex gap-2">
      <Avatar user={node.user} size={32} />
      <div className="min-w-0 flex-1">
        {editing ? (
          <CommentForm
            initial={node.content}
            onSubmit={(t) => edit.mutate(t)}
            busy={edit.isPending}
            autoFocus
          />
        ) : (
          <div className="inline-block max-w-full rounded-2xl bg-paper px-3 py-2">
            <UserLink user={node.user} className="text-sm" />
            <p className="whitespace-pre-wrap break-words text-sm">{node.content}</p>
          </div>
        )}
        <div className="mt-1 flex gap-3 px-2 text-xs text-muted">
          <span>{timeAgo(node.created_at)}</span>
          {node.is_edited && <span>Đã sửa</span>}
          {depth < 3 && (
            <button className="font-semibold hover:underline" onClick={() => setReplying(!replying)}>
              Trả lời
            </button>
          )}
          {node.can_edit && (
            <button className="font-semibold hover:underline" onClick={() => setEditing(!editing)}>
              Sửa
            </button>
          )}
          {node.can_delete && (
            <button
              className="font-semibold hover:underline"
              onClick={() => window.confirm('Xóa bình luận này và các trả lời?') && remove.mutate()}
            >
              Xóa
            </button>
          )}
        </div>
        {replying && (
          <div className="mt-2">
            <CommentForm
              placeholder={`Trả lời ${node.user?.full_name || ''}...`}
              autoFocus
              busy={reply.isPending}
              onSubmit={(text, reset) =>
                reply.mutate(
                  { text },
                  {
                    onSuccess: () => {
                      reset();
                      setReplying(false);
                    },
                  },
                )
              }
            />
          </div>
        )}
        {node.replies?.length > 0 && (
          <div className="mt-2 space-y-3 border-l-2 border-line pl-3">
            {node.replies.map((r) => (
              <CommentNode key={r.id} node={r} postId={postId} depth={depth + 1} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/** UC-15: cây bình luận đa cấp (parent_id). */
export default function CommentThread({ postId, onCountChange }) {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ['comments', postId], queryFn: () => postApi.comments(postId) });
  const add = useMutation({
    mutationFn: (text) => postApi.comment(postId, text),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['comments', postId] });
      onCountChange?.(1);
    },
    onError: (e) => toast.error(errorMessage(e)),
  });
  return (
    <div className="space-y-3 border-t border-line px-4 py-3">
      {q.isLoading ? (
        <Spinner />
      ) : (
        (q.data || []).map((c) => <CommentNode key={c.id} node={c} postId={postId} depth={1} />)
      )}
      <CommentForm busy={add.isPending} onSubmit={(text, reset) => add.mutate(text, { onSuccess: reset })} />
    </div>
  );
}
