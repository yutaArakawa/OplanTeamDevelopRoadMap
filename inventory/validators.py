import re

from django.core.exceptions import ValidationError


class CustomPasswordValidator:

    def validate(self, password, user=None):

        # 半角英数字のみ
        if not re.match(r'^[a-zA-Z0-9]+$', password):

            raise ValidationError(
                'パスワードは半角英数字のみ使用できます'
            )

    def get_help_text(self):

        return 'パスワードは半角英数字のみ使用できます'