from render_block.base import BlockNotFound

def jinja2_render_block(template, block_name, context):
    # Get the underlying jinja2.environment.Template object.
    template = template.template

    # Create a new Context instance.
    context = template.new_context(context)

    # Try to find the wanted block.
    try:
        gen = template.blocks[block_name](context)
    except KeyError:
        raise BlockNotFound("block with name '%s' does not exist" % block_name)

    # The result from above is a generator which yields unicode strings.
    return u''.join([s for s in gen])
