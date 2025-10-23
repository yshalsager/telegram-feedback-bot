from typing import ClassVar

from django.db import migrations, models
from django.db.migrations.operations.base import Operation


class Migration(migrations.Migration):
    dependencies: ClassVar[list[tuple[str, str]]] = [
        ('feedback_bot', '0002_broadcastmessage'),
    ]

    operations: ClassVar[list[Operation]] = [
        migrations.AddField(
            model_name='banneduser',
            name='reason',
            field=models.TextField(blank=True, default=''),
        ),
    ]
