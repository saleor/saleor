import ButtonBase from "@material-ui/core/ButtonBase";
import { Theme } from "@material-ui/core/styles";
import { fade } from "@material-ui/core/styles/colorManipulator";
import TextField, { TextFieldProps } from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import ClearIcon from "@material-ui/icons/Clear";
import { createStyles, makeStyles, useTheme } from "@material-ui/styles";
import React from "react";

import i18n from "../../i18n";
import Filter, { FilterContentSubmitData, IFilter } from "../Filter";
import Hr from "../Hr";
import Link from "../Link";

export interface Filter {
  label: string;
  onClick: () => void;
}

const useInputStyles = makeStyles({
  input: {
    padding: "10px 12px"
  },
  root: {
    flex: 1
  }
});

const Search: React.FC<TextFieldProps> = props => {
  const classes = useInputStyles({});
  return (
    <TextField
      {...props}
      className={classes.root}
      inputProps={{
        className: classes.input
      }}
    />
  );
};

const useStyles = makeStyles(
  (theme: Theme) =>
    createStyles({
      actionContainer: {
        display: "flex",
        flexWrap: "wrap",
        padding: `${theme.spacing.unit}px ${theme.spacing.unit * 3}px`
      },
      filterButton: {
        alignItems: "center",
        backgroundColor: fade(theme.palette.primary.main, 0.6),
        borderRadius: "19px",
        display: "flex",
        height: "38px",
        justifyContent: "space-around",
        margin: `0 ${theme.spacing.unit * 2}px ${theme.spacing.unit}px`,
        marginLeft: 0,
        padding: "0 16px"
      },
      filterChipContainer: {
        display: "flex",
        flex: 1,
        flexWrap: "wrap"
      },
      filterContainer: {
        borderBottom: "1px solid #e8e8e8",
        display: "flex",
        marginTop: theme.spacing.unit,
        padding: `0 ${theme.spacing.unit * 3}px ${theme.spacing.unit}px`
      },
      filterIcon: {
        color: theme.palette.common.white,
        height: 16,
        width: 16
      },
      filterIconContainer: {
        WebkitAppearance: "none",
        background: "transparent",
        border: "none",
        borderRadius: "100%",
        cursor: "pointer",
        height: 32,
        marginRight: -13,
        padding: 8,
        width: 32
      },
      filterLabel: {
        marginBottom: theme.spacing.unit
      },
      filterText: {
        color: theme.palette.common.white,
        fontSize: 12,
        fontWeight: 400 as 400
      }
    }),
  {
    name: "FilterChips"
  }
);

interface FilterChipProps {
  currencySymbol: string;
  menu: IFilter;
  filtersList: Filter[];
  filterLabel: string;
  placeholder: string;
  search: string;
  isCustomSearch: boolean;
  onSearchChange: (event: React.ChangeEvent<any>) => void;
  onFilterAdd: (filter: FilterContentSubmitData) => void;
  onFilterDelete: () => void;
  onFilterSave: () => void;
}

export const FilterChips: React.FC<FilterChipProps> = ({
  currencySymbol,
  filtersList,
  menu,
  filterLabel,
  placeholder,
  onSearchChange,
  search,
  onFilterAdd,
  onFilterSave,
  onFilterDelete,
  isCustomSearch
}) => {
  const theme = useTheme();
  const classes = useStyles({ theme });

  return (
    <>
      <div className={classes.actionContainer}>
        <Filter
          currencySymbol={currencySymbol}
          menu={menu}
          filterLabel={filterLabel}
          onFilterAdd={onFilterAdd}
        />
        <Search
          fullWidth
          placeholder={placeholder}
          value={search}
          onChange={onSearchChange}
        />
      </div>
      {search || (filtersList && filtersList.length) ? (
        <div className={classes.filterContainer}>
          <div className={classes.filterChipContainer}>
            {filtersList.map(filter => (
              <div className={classes.filterButton} key={filter.label}>
                <Typography className={classes.filterText}>
                  {filter.label}
                </Typography>
                <ButtonBase
                  className={classes.filterIconContainer}
                  onClick={filter.onClick}
                >
                  <ClearIcon className={classes.filterIcon} />
                </ButtonBase>
              </div>
            ))}
          </div>
          {isCustomSearch ? (
            <Link onClick={onFilterSave}>{i18n.t("Save Custom Search")}</Link>
          ) : (
            <Link onClick={onFilterDelete}>{i18n.t("Delete Search")}</Link>
          )}
        </div>
      ) : (
        <Hr />
      )}
    </>
  );
};

export default FilterChips;
