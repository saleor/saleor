from promise import Promise

from ..utils import base64, unbase64, is_str
from .connectiontypes import Connection, PageInfo, Edge


def connection_from_list(data, args=None, **kwargs):
    '''
    A simple function that accepts an array and connection arguments, and returns
    a connection object for use in GraphQL. It uses array offsets as pagination,
    so pagination will only work if the array is static.
    '''
    _len = len(data)
    return connection_from_list_slice(
        data,
        args,
        slice_start=0,
        list_length=_len,
        list_slice_length=_len,
        **kwargs
    )


def connection_from_promised_list(data_promise, args=None, **kwargs):
    '''
    A version of `connectionFromArray` that takes a promised array, and returns a
    promised connection.
    '''
    return data_promise.then(lambda data: connection_from_list(data, args, **kwargs))


def connection_from_list_slice(list_slice, args=None, connection_type=None,
                               edge_type=None, pageinfo_type=None,
                               slice_start=0, list_length=0, list_slice_length=None):
    '''
    Given a slice (subset) of an array, returns a connection object for use in
    GraphQL.
    This function is similar to `connectionFromArray`, but is intended for use
    cases where you know the cardinality of the connection, consider it too large
    to materialize the entire array, and instead wish pass in a slice of the
    total result large enough to cover the range specified in `args`.
    '''
    connection_type = connection_type or Connection
    edge_type = edge_type or Edge
    pageinfo_type = pageinfo_type or PageInfo

    args = args or {}

    before = args.get('before')
    after = args.get('after')
    first = args.get('first')
    last = args.get('last')
    if list_slice_length is None:
        list_slice_length = len(list_slice)
    slice_end = slice_start + list_slice_length
    before_offset = get_offset_with_default(before, list_length)
    after_offset = get_offset_with_default(after, -1)

    start_offset = max(
        slice_start - 1,
        after_offset,
        -1
    ) + 1
    end_offset = min(
        slice_end,
        before_offset,
        list_length
    )
    if isinstance(first, int):
        end_offset = min(
            end_offset,
            start_offset + first
        )
    if isinstance(last, int):
        start_offset = max(
            start_offset,
            end_offset - last
        )

    # If supplied slice is too large, trim it down before mapping over it.
    _slice = list_slice[
        max(start_offset - slice_start, 0):
        list_slice_length - (slice_end - end_offset)
    ]
    edges = [
        edge_type(
            node=node,
            cursor=offset_to_cursor(start_offset + i)
        )
        for i, node in enumerate(_slice)
    ]


    first_edge_cursor = edges[0].cursor if edges else None
    last_edge_cursor = edges[-1].cursor if edges else None
    lower_bound = after_offset + 1 if after else 0
    upper_bound = before_offset if before else list_length

    return connection_type(
        edges=edges,
        page_info=pageinfo_type(
            start_cursor=first_edge_cursor,
            end_cursor=last_edge_cursor,
            has_previous_page=isinstance(last, int) and start_offset > lower_bound,
            has_next_page=isinstance(first, int) and end_offset < upper_bound
        )
    )


PREFIX = 'arrayconnection:'


def connection_from_promised_list_slice(data_promise, args=None, **kwargs):
    return data_promise.then(lambda data: connection_from_list_slice(data, args, **kwargs))


def offset_to_cursor(offset):
    '''
    Creates the cursor string from an offset.
    '''
    return base64(PREFIX + str(offset))


def cursor_to_offset(cursor):
    '''
    Rederives the offset from the cursor string.
    '''
    try:
        return int(unbase64(cursor)[len(PREFIX):])
    except:
        return None


def cursor_for_object_in_connection(data, _object):
    '''
    Return the cursor associated with an object in an array.
    '''
    if _object not in data:
        return None

    offset = data.index(_object)
    return offset_to_cursor(offset)


def get_offset_with_default(cursor=None, default_offset=0):
    '''
    Given an optional cursor and a default offset, returns the offset
    to use; if the cursor contains a valid offset, that will be used,
    otherwise it will be the default.
    '''
    if not is_str(cursor):
        return default_offset

    offset = cursor_to_offset(cursor)
    try:
        return int(offset)
    except:
        return default_offset
