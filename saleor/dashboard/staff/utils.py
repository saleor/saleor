def remove_staff_member(staff):
    """Removes staff member account only if has no orders placed.
    Otherwise, switches is_staff status to False."""
    if staff.orders.exists():
        staff.is_staff = False
        staff.save()
    else:
        staff.delete()
