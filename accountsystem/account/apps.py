from django.apps import AppConfig


class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'account'
    _prewarmed = False

    def ready(self):
        # 避免 runserver 自动重载造成重复预热
        if AccountConfig._prewarmed:
            return
        AccountConfig._prewarmed = True
        try:
            from .ai.agent.agent import prewarm_runtime

            prewarm_runtime()
        except Exception as e:
            print(f"[PREWARM] app ready skipped: {e}")
