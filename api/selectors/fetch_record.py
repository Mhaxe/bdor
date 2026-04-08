from api.models import FetchRecord

def delete_fetch_record():
    FetchRecord.objects.all().delete()