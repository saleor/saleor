def get_sort_by_choices(filter_set):
    return [(choice[0], choice[1].lower()) for choice in
            list(filter_set.filters['sort_by'].field.choices)[1::2]]


def get_now_sorted_by(filter_set, default_sort='name'):
    sort_by = filter_set.form.cleaned_data.get('sort_by')
    if sort_by:
        sort_by = sort_by[0].strip('-')
    else:
        sort_by = default_sort
    return sort_by
