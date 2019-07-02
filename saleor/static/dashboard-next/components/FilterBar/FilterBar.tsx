import React from "react";

import i18n from "../../i18n";
import { FilterProps } from "../../types";
import Debounce from "../Debounce";
import { IFilter } from "../Filter/types";
import FilterTabs, { FilterChips, FilterTab } from "../TableFilter";

export interface FilterBarProps<TUrlFilters = object>
  extends FilterProps<TUrlFilters> {
  filterMenu: IFilter;
}

const FilterBar: React.FC<FilterBarProps> = ({
  allTabLabel,
  currencySymbol,
  filterLabel,
  filtersList,
  filterTabs,
  filterMenu,
  currentTab,
  initialSearch,
  searchPlaceholder,
  onAll,
  onSearchChange,
  onFilterAdd,
  onFilterSave,
  onTabChange,
  onFilterDelete
}) => {
  const [search, setSearch] = React.useState(initialSearch);
  React.useEffect(() => setSearch(initialSearch), [currentTab, initialSearch]);

  const isCustom = currentTab === filterTabs.length + 1;

  return (
    <>
      <FilterTabs currentTab={currentTab}>
        <FilterTab label={allTabLabel} onClick={onAll} />
        {filterTabs.map((tab, tabIndex) => (
          <FilterTab
            onClick={() => onTabChange(tabIndex + 1)}
            label={tab.name}
          />
        ))}
        {isCustom && (
          <FilterTab
            onClick={() => undefined}
            label={i18n.t("Custom Filter")}
          />
        )}
      </FilterTabs>
      <Debounce debounceFn={onSearchChange}>
        {debounceSearchChange => {
          const handleSearchChange = (event: React.ChangeEvent<any>) => {
            const value = event.target.value;
            setSearch(value);
            debounceSearchChange(value);
          };

          return (
            <FilterChips
              currencySymbol={currencySymbol}
              menu={filterMenu}
              filtersList={filtersList}
              filterLabel={filterLabel}
              placeholder={searchPlaceholder}
              search={search}
              onSearchChange={handleSearchChange}
              onFilterAdd={onFilterAdd}
              onFilterSave={onFilterSave}
              isCustomSearch={isCustom}
              onFilterDelete={onFilterDelete}
            />
          );
        }}
      </Debounce>
    </>
  );
};
FilterBar.displayName = "FilterBar";
export default FilterBar;
