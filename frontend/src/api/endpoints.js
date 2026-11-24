import { http, unwrap } from './client';

const get = (url, params) => http.get(url, { params }).then(unwrap);
const post = (url, body, config) => http.post(url, body, config).then(unwrap);
const patch = (url, body) => http.patch(url, body).then(unwrap);
const del = (url) => http.delete(url).then(unwrap);

/** Lấy cursor từ link 'next' của Cursor Pagination. */
export const cursorOf = (link) =>
  link ? new URL(link, 'http://localhost').searchParams.get('cursor') || undefined : undefined;

export const authApi = {
  register: (body) => post('/auth/register/', body),
  verifyEmail: (body) => post('/auth/verify-email/', body),
  requestOtp: (email, purpose) => post('/auth/otp/request/', { email, purpose }),
  login: (body) => post('/auth/login/', body),
  loginOtp: (body) => post('/auth/login/otp/', body),
  logout: () => post('/auth/logout/'),
  forgot: (email) => post('/auth/password/forgot/', { email }),
  reset: (body) => post('/auth/password/reset/', body),
  changePassword: (body) => post('/auth/password/change/', body),
};

export const userApi = {
  me: () => get('/users/me/'),
  updateMe: (body) => patch('/users/me/', body),
  profile: (id) => get(`/users/${id}/`),
  search: (q) => get('/users/search/', { q }),
  suggestions: () => get('/users/suggestions/'),
  friends: (userId) => get('/users/friends/', userId ? { user_id: userId } : undefined),
  requests: (direction = 'received') => get('/users/friends/requests/', { direction }),
  sendRequest: (userId) => post('/users/friends/requests/', { user_id: userId }),
  accept: (id) => post(`/users/friends/requests/${id}/accept/`),
  decline: (id) => post(`/users/friends/requests/${id}/decline/`),
  cancel: (id) => del(`/users/friends/requests/${id}/`),
  unfriend: (userId) => del(`/users/friends/${userId}/`),
  blocks: () => get('/users/blocks/'),
  block: (userId) => post('/users/blocks/', { user_id: userId }),
  unblock: (userId) => del(`/users/blocks/${userId}/`),
};

export const postApi = {
  feed: (cursor) => get('/posts/feed/', cursor ? { cursor } : undefined),
  byUser: (userId, cursor) => get(`/posts/user/${userId}/`, cursor ? { cursor } : undefined),
  byGroup: (groupId, cursor) => get(`/posts/group/${groupId}/`, cursor ? { cursor } : undefined),
  detail: (id) => get(`/posts/${id}/`),
  create: (formData) => post('/posts/', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  update: (id, body) => patch(`/posts/${id}/`, body),
  remove: (id) => del(`/posts/${id}/`),
  pin: (id) => post(`/posts/${id}/pin/`),
  like: (id) => post(`/posts/${id}/like/`),
  likers: (id) => get(`/posts/${id}/like/`),
  comments: (id) => get(`/posts/${id}/comments/`),
  comment: (id, content, parentId) =>
    post(`/posts/${id}/comments/`, { content, parent_id: parentId || null }),
  editComment: (id, content) => patch(`/posts/comments/${id}/`, { content }),
  deleteComment: (id) => del(`/posts/comments/${id}/`),
  share: (id, content) => post(`/posts/${id}/share/`, { content }),
  shares: (userId) => get(`/posts/user/${userId}/shares/`),
};

export const mediaApi = {
  upload: (file, purpose) => {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('purpose', purpose);
    return post('/media/upload/', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
};

export const groupApi = {
  list: (params) => get('/groups/', params),
  detail: (id) => get(`/groups/${id}/`),
  create: (body) => post('/groups/', body),
  update: (id, body) => patch(`/groups/${id}/`, body),
  remove: (id) => del(`/groups/${id}/`),
  join: (id) => post(`/groups/${id}/join/`),
  leave: (id) => post(`/groups/${id}/leave/`),
  members: (id, status = 'ACCEPTED') => get(`/groups/${id}/members/`, { status }),
  approve: (id, memberId) => post(`/groups/${id}/members/${memberId}/approve/`),
  reject: (id, memberId) => post(`/groups/${id}/members/${memberId}/reject/`),
  setRole: (id, memberId, role) => patch(`/groups/${id}/members/${memberId}/`, { role }),
  kick: (id, memberId) => del(`/groups/${id}/members/${memberId}/`),
};

export const chatApi = {
  conversations: () => get('/chat/conversations/'),
  conversation: (id) => get(`/chat/conversations/${id}/`),
  direct: (userId) => post('/chat/conversations/direct/', { user_id: userId }),
  createGroup: (title, memberIds) => post('/chat/conversations/group/', { title, member_ids: memberIds }),
  addMembers: (id, userIds) => post(`/chat/conversations/${id}/members/`, { user_ids: userIds }),
  removeMember: (id, userId) => del(`/chat/conversations/${id}/members/${userId}/`),
  messages: (id, cursor) => get(`/chat/conversations/${id}/messages/`, cursor ? { cursor } : undefined),
  send: (id, body) => post(`/chat/conversations/${id}/messages/`, body),
  read: (id) => post(`/chat/conversations/${id}/read/`),
  presence: () => get('/chat/presence/'),
  unread: () => get('/chat/unread/'),
};

export const notificationApi = {
  list: (cursor) => get('/notifications/', cursor ? { cursor } : undefined),
  unread: () => get('/notifications/unread-count/'),
  read: (id) => post(`/notifications/${id}/read/`),
  readAll: () => post('/notifications/read-all/'),
};

export const reportApi = {
  reasons: () => get('/admin/reports/reasons/'),
  submit: (body) => post('/admin/reports/', body),
};

export const adminApi = {
  dashboard: () => get('/admin/manage/dashboard/'),
  reports: (status, cursor) => get('/admin/manage/reports/', { status, ...(cursor ? { cursor } : {}) }),
  resolve: (id, body) => post(`/admin/manage/reports/${id}/resolve/`, body),
  users: (params) => get('/admin/manage/users/', params),
  ban: (id, reason) => post(`/admin/manage/users/${id}/ban/`, { reason }),
  unban: (id) => post(`/admin/manage/users/${id}/unban/`),
};
