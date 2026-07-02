import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "accountsystem.settings")
django.setup()

from django.core.management import call_command
from io import StringIO
from django.db import connection
from comment.models import UserComment, UserFollow, UserPost
from user.models import User

# 1) migrate --plan should show nothing pending locally
out = StringIO()
call_command("migrate", "--plan", stdout=out)
plan = out.getvalue()
pending = [line for line in plan.splitlines() if line.strip().startswith("[ ]")]
print("=== Pending migrations ===")
print("NONE" if not pending else "\n".join(pending))

# 2) community tables exist
with connection.cursor() as c:
    c.execute("SHOW TABLES LIKE 'user_community%'")
    tables = sorted(r[0] for r in c.fetchall())
print("\n=== Community tables ===")
for t in tables:
    print(" ", t)

required = {
    "user_community_post",
    "user_community_comment",
    "user_community_image",
    "user_community_post_like",
    "user_community_follow",
    "user_community_notice",
}
missing = required - set(tables)
print("Missing:", missing or "none")

# 3) ORM queries that previously 500'd
print("\n=== ORM smoke test ===")
print("UserComment fields OK:", UserComment.objects.count(), "rows")
print("UserFollow fields OK:", UserFollow.objects.count(), "rows")
if User.objects.exists():
    u = User.objects.first()
    fc = UserFollow.objects.filter(user=u).count()
    fwc = UserFollow.objects.filter(followed_user=u).count()
    print(f"User {u.id} following={fc} followers={fwc}")

# 4) comment column mapping
with connection.cursor() as c:
    c.execute("SHOW COLUMNS FROM user_community_comment")
    cols = {r[0] for r in c.fetchall()}
for col in ("parent_id", "root_id", "reply_to_id"):
    print(f"column {col}:", "OK" if col in cols else "MISSING")

print("\n=== Result ===")
print("PASS" if not pending and not missing else "FAIL")
