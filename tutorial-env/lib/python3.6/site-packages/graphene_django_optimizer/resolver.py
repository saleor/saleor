from .hints import OptimizationHints


def resolver_hints(*args, **kwargs):
    optimization_hints = OptimizationHints(*args, **kwargs)

    def apply_resolver_hints(resolver):
        resolver.optimization_hints = optimization_hints
        return resolver

    return apply_resolver_hints
