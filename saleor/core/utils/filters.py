def get_now_sorted_by(filter_set, default_sort='name'):
    sort_by = filter_set.form.cleaned_data.get('sort_by')
    if sort_by:
        sort_by = sort_by[0].strip('-')
    else:
        sort_by = default_sort
    return sort_by
