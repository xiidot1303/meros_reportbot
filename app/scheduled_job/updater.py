from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events, DjangoJobStore
from app.scheduled_job import smartup_job, soliq_job, price_job, debt_job
from bot.scheduled_job import mailing
from bot.services.redis_service import save_langs_to_redis
from asgiref.sync import async_to_sync

class jobs:
    scheduler = BackgroundScheduler(timezone='Asia/Tashkent')
    scheduler.add_jobstore(DjangoJobStore(), 'djangojobstore')
    register_events(scheduler)
    # scheduler.add_job(, 'interval', minutes=5)
    # `async_to_sync` hides the wrapped coroutine's name, so set it explicitly —
    # it is what `run_job` uses to address this job.
    scheduler.add_job(
        async_to_sync(mailing.send_message), 
        'interval', minutes=5, name='send_message')

    scheduler.add_job(
        smartup_job.fetch_clients, 
        'interval', minutes=15)

    scheduler.add_job(
        smartup_job.check_orders, 
        'interval', minutes=7)

    scheduler.add_job(
        soliq_job.sync_facturas_for_active_cabinets,
        'interval', minutes=10)

    scheduler.add_job(
        price_job.sync_prices,
        'interval', minutes=10)

    # overdue-payment alerts go out once a day, in the early afternoon
    scheduler.add_job(
        debt_job.notify_overdue_payments,
        'cron', hour=14, minute=0, name='notify_overdue_payments')

    # bot
    scheduler.add_job(save_langs_to_redis, 'interval', minutes=20)
    
