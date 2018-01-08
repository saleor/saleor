from django.db.models import F


def increase_voucher_usage(voucher):
    voucher.used = F('used') + 1
    voucher.save(update_fields=['used'])


def decrease_voucher_usage(voucher):
    voucher.used = F('used') - 1
    voucher.save(update_fields=['used'])
