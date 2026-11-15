/** Lấy thông báo lỗi tiếng Việt từ phản hồi chuẩn { success:false, message, errors }. */
export function errorMessage(err, fallback = 'Đã có lỗi xảy ra, vui lòng thử lại.') {
  const data = err?.response?.data;
  if (!data) return err?.message === 'Network Error' ? 'Không kết nối được máy chủ.' : fallback;
  const fieldErrors = data.errors && typeof data.errors === 'object' ? Object.values(data.errors).flat() : [];
  const firstField = fieldErrors.find((x) => typeof x === 'string');
  if ((data.message === 'Dữ liệu không hợp lệ' || data.message?.startsWith('Mật khẩu')) && firstField) {
    return firstField;
  }
  return data.message || firstField || fallback;
}

export function errorCode(err) {
  return err?.response?.data?.code;
}
