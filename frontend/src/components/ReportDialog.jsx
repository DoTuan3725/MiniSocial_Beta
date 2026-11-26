import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { reportApi } from '../api/endpoints';
import { errorMessage } from '../lib/errors';
import { toast } from '../store/toast';
import { Modal } from './ui';

const TARGET_LABEL = { POST: 'bài viết', COMMENT: 'bình luận', USER: 'tài khoản' };

/** UC-27: báo cáo vi phạm (đa hình: bài viết / bình luận / tài khoản). */
export default function ReportDialog({ target, onClose }) {
  const [reason, setReason] = useState('');
  const [details, setDetails] = useState('');
  const reasons = useQuery({ queryKey: ['report-reasons'], queryFn: reportApi.reasons, staleTime: Infinity });
  const m = useMutation({
    mutationFn: () => reportApi.submit({ target_type: target.type, target_id: target.id, reason, details }),
    onSuccess: () => {
      toast.success('Đã gửi báo cáo. Quản trị viên sẽ xem xét sớm.');
      onClose();
    },
    onError: (e) => toast.error(errorMessage(e)),
  });
  return (
    <Modal open={!!target} onClose={onClose} title={`Báo cáo ${TARGET_LABEL[target?.type] || ''}`}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          m.mutate();
        }}
        className="space-y-4"
      >
        <fieldset className="space-y-2">
          <legend className="label">Vấn đề bạn gặp phải</legend>
          {(reasons.data || []).map((r) => (
            <label
              key={r.value}
              className="flex cursor-pointer items-center gap-3 rounded-lg border border-line px-3 py-2.5 text-sm hover:bg-paper has-[:checked]:border-ink has-[:checked]:bg-ink-50"
            >
              <input
                type="radio"
                name="reason"
                value={r.value}
                checked={reason === r.value}
                onChange={() => setReason(r.value)}
                className="accent-ink"
              />
              {r.label}
            </label>
          ))}
        </fieldset>
        <div>
          <label className="label" htmlFor="report-details">
            Mô tả thêm (không bắt buộc)
          </label>
          <textarea
            id="report-details"
            className="input min-h-20"
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            maxLength={2000}
          />
        </div>
        <button className="btn-primary w-full" disabled={!reason || m.isPending}>
          Gửi báo cáo
        </button>
      </form>
    </Modal>
  );
}
