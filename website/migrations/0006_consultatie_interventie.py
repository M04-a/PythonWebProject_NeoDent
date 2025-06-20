# Generated by Django 4.2.21 on 2025-06-05 19:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0005_remove_programare_serviciu'),
    ]

    operations = [
        migrations.CreateModel(
            name='Consultatie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dinte', models.CharField(max_length=5)),
                ('tip', models.CharField(choices=[('initiala', 'Consultație inițială'), ('control', 'Control post-tratament'), ('urgenta', 'Urgență')], max_length=50)),
                ('observatii', models.TextField(blank=True)),
                ('cost_total', models.DecimalField(decimal_places=2, max_digits=8)),
                ('nume_medic', models.CharField(max_length=255)),
                ('data_creata', models.DateTimeField(auto_now_add=True)),
                ('programare', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='website.programare')),
            ],
        ),
        migrations.CreateModel(
            name='Interventie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clasa', models.CharField(max_length=100)),
                ('denumire', models.CharField(max_length=255)),
                ('cost', models.DecimalField(decimal_places=2, max_digits=7)),
                ('consultatie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interventii', to='website.consultatie')),
            ],
        ),
    ]
