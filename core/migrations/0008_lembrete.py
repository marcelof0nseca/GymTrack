from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_meta_data_inicio'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lembrete',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=120)),
                ('data_hora', models.DateTimeField()),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lembretes', to='auth.user')),
            ],
            options={
                'ordering': ['data_hora', 'id'],
            },
        ),
    ]