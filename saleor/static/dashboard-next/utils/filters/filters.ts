function createFilterUtils<TQueryParams, TFilters>(filters: object) {
  function getActiveFilters(params: TQueryParams): TFilters {
    return Object.keys(params)
      .filter(key => Object.keys(filters).includes(key))
      .reduce(
        (acc, key) => {
          acc[key] = params[key];
          return acc;
        },
        {} as any
      );
  }

  function areFiltersApplied(params: TQueryParams): boolean {
    return Object.keys(getActiveFilters(params)).some(key => !!params[key]);
  }

  return {
    areFiltersApplied,
    getActiveFilters
  };
}

export default createFilterUtils;
