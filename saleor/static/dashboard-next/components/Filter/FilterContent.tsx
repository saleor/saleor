import Button from "@material-ui/core/Button";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import i18n from "../../i18n";
import { getMenuItemByValue, isLeaf, walkToRoot } from "../../utils/menu";
import FormSpacer from "../FormSpacer";
import SingleSelectField from "../SingleSelectField";
import FilterElement from "./FilterElement";
import { IFilter } from "./types";

export interface FilterContentSubmitData {
  name: string;
  value: string | string[];
}
export interface FilterContentProps {
  filters: IFilter;
  onSubmit: (data: FilterContentSubmitData) => void;
}

const styles = (theme: Theme) => createStyles({});
const FilterContent = withStyles(styles, { name: "FilterContent" })(
  ({
    classes,
    filters,
    onSubmit
  }: FilterContentProps & WithStyles<typeof styles>) => {
    const [menuValue, setMenuValue] = React.useState<string>("");
    const [filterValue, setFilterValue] = React.useState<string | string[]>("");

    const activeMenu = menuValue
      ? getMenuItemByValue(filters, menuValue)
      : undefined;
    const menus = menuValue
      ? walkToRoot(filters, menuValue).slice(-1)
      : undefined;

    const onMenuChange = (event: React.ChangeEvent<any>) => {
      setMenuValue(event.target.value);
      setFilterValue("");
    };

    return (
      <>
        <SingleSelectField
          choices={filters.map(filterItem => ({
            label: filterItem.label,
            value: filterItem.value
          }))}
          onChange={onMenuChange}
          selectProps={{
            placeholder: i18n.t("Select Filter...")
          }}
          value={menus ? menus[0].value : menuValue}
        />
        <FormSpacer />
        {menus &&
          menus.map((filterItem, filterItemIndex) => (
            <>
              <SingleSelectField
                choices={filterItem.children.map(filterItem => ({
                  label: filterItem.label,
                  value: filterItem.value
                }))}
                onChange={onMenuChange}
                selectProps={{
                  placeholder: i18n.t("Select Filter...")
                }}
                value={
                  filterItemIndex === menus.length - 1
                    ? menuValue
                    : menus[filterItemIndex - 1].label.toString()
                }
              />
              <FormSpacer />
            </>
          ))}
        {activeMenu && isLeaf(activeMenu) && (
          <>
            <FilterElement
              filter={activeMenu}
              value={filterValue}
              onChange={value => setFilterValue(value)}
            />
            {filterValue && (
              <Button
                color="primary"
                onClick={() =>
                  onSubmit({
                    name: activeMenu.value,
                    value: filterValue
                  })
                }
              >
                {i18n.t("Add filter")}
              </Button>
            )}
          </>
        )}
      </>
    );
  }
);
FilterContent.displayName = "FilterContent";
export default FilterContent;
