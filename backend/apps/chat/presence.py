"""
Trạng thái Online trên Redis (RAM, không ghi MySQL):
  presence:conn:<uid>   số kết nối WebSocket đang mở (nhiều tab)
  presence:online:<uid> tồn tại = đang online; TTL 70s, được làm mới bởi ping 30s/lần
TTL giúp tự dọn trạng thái "online ma" nếu server dừng đột ngột.
"""

from django.conf import settings

from common.redis_client import get_redis


def connect(user_id):
    r = get_redis()
    pipe = r.pipeline()
    pipe.incr(f"presence:conn:{user_id}")
    pipe.expire(f"presence:conn:{user_id}", 3600)
    pipe.exists(f"presence:online:{user_id}")
    pipe.set(f"presence:online:{user_id}", 1, ex=settings.PRESENCE_TTL_SECONDS)
    _, _, was_online, _ = pipe.execute()
    return not was_online  # True nếu vừa chuyển từ offline -> online


def heartbeat(user_id):
    r = get_redis()
    r.set(f"presence:online:{user_id}", 1, ex=settings.PRESENCE_TTL_SECONDS)
    r.expire(f"presence:conn:{user_id}", 3600)


def disconnect(user_id):
    r = get_redis()
    remaining = r.decr(f"presence:conn:{user_id}")
    if remaining <= 0:
        r.delete(f"presence:conn:{user_id}", f"presence:online:{user_id}")
        return True  # vừa offline hẳn
    return False


def online_ids(user_ids):
    ids = [str(u) for u in user_ids]
    if not ids:
        return set()
    values = get_redis().mget([f"presence:online:{u}" for u in ids])
    return {uid for uid, v in zip(ids, values) if v}
