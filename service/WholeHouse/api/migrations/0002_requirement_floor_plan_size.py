# E1：Requirement 增加户型图大小字段
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="requirement",
            name="floor_plan_size",
            field=models.PositiveBigIntegerField(default=0, verbose_name="户型图大小(字节)"),
        ),
    ]
