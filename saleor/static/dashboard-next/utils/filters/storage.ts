interface UserFilter<TUrlFilters> {
  name: string;
  data: TUrlFilters;
}

export type GetFilterTabsOutput<TUrlFilters> = Array<UserFilter<TUrlFilters>>;

function getFilterTabs<TUrlFilters>(
  key: string
): GetFilterTabsOutput<TUrlFilters> {
  return JSON.parse(localStorage.getItem(key)) || [];
}

function saveFilterTab<TUrlFilters>(
  name: string,
  data: TUrlFilters,
  key: string
) {
  const userFilters = getFilterTabs<TUrlFilters>(key);

  localStorage.setItem(
    key,
    JSON.stringify([
      ...userFilters,
      {
        data,
        name
      }
    ])
  );
}

function deleteFilterTab(id: number, key: string) {
  const userFilters = getFilterTabs(key);

  localStorage.setItem(
    key,
    JSON.stringify([...userFilters.slice(0, id - 1), ...userFilters.slice(id)])
  );
}

function createFilterTabUtils<TUrlFilters>(key: string) {
  return {
    deleteFilterTab: (id: number) => deleteFilterTab(id, key),
    getFilterTabs: () => getFilterTabs<TUrlFilters>(key),
    saveFilterTab: (name: string, data: TUrlFilters) =>
      saveFilterTab<TUrlFilters>(name, data, key)
  };
}

export default createFilterTabUtils;
