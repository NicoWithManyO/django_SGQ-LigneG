from production.models import Shift

print(f'Nombre de shifts: {Shift.objects.count()}')
print('Derniers shifts:')
for s in Shift.objects.order_by('-created_at')[:3]:
    print(f'  - {s.shift_id} créé le {s.created_at}')