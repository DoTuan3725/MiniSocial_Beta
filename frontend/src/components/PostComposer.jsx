import { useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ImagePlus, X, Globe2, Users, Lock } from 'lucide-react';
import { postApi } from '../api/endpoints';
import { errorMessage } from '../lib/errors';
import { useAuth } from '../store/auth';
import { toast } from '../store/toast';
import { Avatar, Spinner } from './ui';

const MAX_FILES = 10;
const MAX_MB = 10;
const PRIVACY = [
  { value: 'PUBLIC', label: 'Công khai', icon: Globe2 },
  { value: 'FRIENDS', label: 'Bạn bè', icon: Users },
  { value: 'PRIVATE', label: 'Chỉ mình tôi', icon: Lock },
];

/** UC-11: soạn bài viết (văn bản + tối đa 10 ảnh/video, mỗi tệp <= 10MB). */
export default function PostComposer({ groupId, invalidateKeys = [['feed']] }) {
  const user = useAuth((s) => s.user);
  const qc = useQueryClient();
  const fileRef = useRef(null);
  const [content, setContent] = useState('');
  const [privacy, setPrivacy] = useState('FRIENDS');
  const [files, setFiles] = useState([]);

  const m = useMutation({
    mutationFn: () => {
      const fd = new FormData();
      fd.append('content', content);
      if (groupId) fd.append('group_id', groupId);
      else fd.append('privacy', privacy);
      files.forEach((f) => fd.append('files', f.file));
      return postApi.create(fd);
    },
    onSuccess: (post) => {
      toast[post.is_flagged ? 'error' : 'success'](
        post.is_flagged
          ? 'Bài viết chứa từ ngữ không phù hợp, đang chờ quản trị viên xem xét.'
          : 'Đã đăng bài viết',
      );
      files.forEach((f) => URL.revokeObjectURL(f.preview));
      setContent('');
      setFiles([]);
      invalidateKeys.forEach((k) => qc.invalidateQueries({ queryKey: k }));
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  const addFiles = (list) => {
    const next = [...files];
    for (const file of list) {
      if (next.length >= MAX_FILES) {
        toast.error(`Mỗi bài viết tối đa ${MAX_FILES} tệp`);
        break;
      }
      if (file.size > MAX_MB * 1024 * 1024) {
        toast.error(`"${file.name}" lớn hơn ${MAX_MB}MB`);
        continue;
      }
      next.push({ file, preview: URL.createObjectURL(file), isVideo: file.type.startsWith('video/') });
    }
    setFiles(next);
  };

  const canPost = (content.trim() || files.length) && !m.isPending;

  return (
    <div className="card border-l-4 border-amber p-4">
      <div className="flex gap-3">
        <Avatar user={user} />
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder={
            groupId
              ? 'Viết gì đó cho nhóm...'
              : `${user?.full_name?.split(' ').pop() || 'Bạn'} ơi, bạn đang nghĩ gì?`
          }
          className="min-h-[72px] flex-1 resize-none border-0 bg-transparent text-[15px] placeholder:text-muted focus:outline-none"
          maxLength={10000}
          aria-label="Nội dung bài viết"
        />
      </div>
      {files.length > 0 && (
        <div className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-4">
          {files.map((f, i) => (
            <div key={f.preview} className="relative aspect-square overflow-hidden rounded-lg bg-ink-50">
              {f.isVideo ? (
                <video src={f.preview} className="h-full w-full object-cover" muted />
              ) : (
                <img src={f.preview} alt="" className="h-full w-full object-cover" />
              )}
              <button
                type="button"
                onClick={() => setFiles(files.filter((_, j) => j !== i))}
                className="absolute right-1 top-1 rounded-full bg-ink-900/70 p-1 text-white"
                aria-label="Bỏ tệp"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
      <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-line pt-3">
        <input
          ref={fileRef}
          type="file"
          multiple
          accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm,video/quicktime"
          className="hidden"
          onChange={(e) => {
            addFiles(Array.from(e.target.files || []));
            e.target.value = '';
          }}
        />
        <button type="button" className="btn-ghost px-3" onClick={() => fileRef.current?.click()}>
          <ImagePlus className="h-4 w-4 text-success" /> Ảnh/Video
        </button>
        {!groupId && (
          <select
            value={privacy}
            onChange={(e) => setPrivacy(e.target.value)}
            className="rounded-lg border border-line bg-white px-2 py-2 text-sm"
            aria-label="Ai có thể xem"
          >
            {PRIVACY.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        )}
        <button className="btn-primary ml-auto" disabled={!canPost} onClick={() => m.mutate()}>
          {m.isPending ? <Spinner className="h-4 w-4 text-white" /> : 'Đăng'}
        </button>
      </div>
    </div>
  );
}
