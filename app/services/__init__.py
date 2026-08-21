from django.shortcuts import get_object_or_404
from django.db.models import Q
from app.utils import *
from asgiref.sync import *

async def update_model_object(model_obj, update_dict):
    for key, value in update_dict.items():
        setattr(model_obj, key, value)
    await model_obj.asave()


async def filter_objects_sync(model_class, filters):
    return [obj async for obj in model_class.objects.filter(**filters).values()]