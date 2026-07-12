# bot/core/mood_system.py
"""
Система настроений для бота Сумеречная Искорка.
(Заглушка, будет доработана позже)

Автор: MADAO81
Версия: 1.0
"""


class MoodSystem:
    """Заглушка для системы настроения."""

    def __init__(self):
        self.current_mood = "happy"

    async def determine_mood(self):
        return "happy", None

    def get_mood_text(self, mood: str) -> str:
        return "📚 У меня отличное настроение!"

    def get_mood_emoji(self, mood: str) -> str:
        return "📚"

    def should_comment(self) -> bool:
        return True