from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('academy', '0004_diagnosticsubmission_recommendations_and_more')]

    operations = [
        migrations.AddField(
            model_name='diagnosticquestion', name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='diagnosticoption', name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='diagnosticrecommendation', name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
