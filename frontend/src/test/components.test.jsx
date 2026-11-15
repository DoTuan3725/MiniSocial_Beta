import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { Avatar, EmptyState } from '../components/ui';

describe('Avatar', () => {
  it('hiển thị chữ viết tắt khi chưa có ảnh', () => {
    render(<Avatar user={{ id: '1', full_name: 'Nguyễn Văn Đức', avatar_url: '' }} />);
    expect(screen.getByText('VĐ')).toBeInTheDocument();
  });
});

describe('EmptyState', () => {
  it('hiển thị tiêu đề và nút hành động', () => {
    render(
      <MemoryRouter>
        <EmptyState title="Bảng tin còn trống" action={<button>Tìm bạn bè</button>}>
          Hãy kết bạn
        </EmptyState>
      </MemoryRouter>,
    );
    expect(screen.getByText('Bảng tin còn trống')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Tìm bạn bè' })).toBeInTheDocument();
  });
});
