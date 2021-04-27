# Generated by Django 3.0.1 on 2021-02-08 04:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inv', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invproj',
            name='bank',
        ),
        migrations.RemoveField(
            model_name='invproj',
            name='currency',
        ),
        migrations.AddField(
            model_name='invproj',
            name='acct',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='inv.Account', verbose_name='账户'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='invproj',
            name='local_irr',
            field=models.DecimalField(decimal_places=4, max_digits=16, null=True, verbose_name='本币年化率'),
        ),
    ]
