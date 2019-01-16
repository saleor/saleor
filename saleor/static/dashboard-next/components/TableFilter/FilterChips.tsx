import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import AddIcon from "@material-ui/icons/Add";
import ClearIcon from "@material-ui/icons/Clear";
import * as classNames from "classnames";
import * as React from "react";

import i18n from "../../i18n";

export interface Filter {
  label: string;
  onClick: () => void;
}

const styles = createStyles({
  addFilterButtonPrimary: {
    "&:hover": {
      backgroundColor: "rgba(90, 179, 120, .25)"
    },
    backgroundColor: "#ffffff",
    border: "2px dashed #5AB378",
    width: "135px"
  },
  addFilterButtonSecondary: {
    "&:hover": {
      backgroundColor: "rgba(3, 169, 244, .25)"
    },
    backgroundColor: "#ffffff",
    border: "2px dashed #03A9F4",
    width: "135px"
  },
  addFilterText: {
    fontWeight: 600 as 600,
    marginRight: "12px"
  },
  filterButton: {
    alignItems: "center",
    backgroundColor: "rgba(90, 179, 120, .25)",
    borderRadius: "19px",
    cursor: "pointer",
    display: "flex",
    height: "38px",
    justifyContent: "space-around",
    margin: "10px 0 0 12px",
    minWidth: "160px",
    padding: "0 8px 0 16px"
  },
  filterContainer: {
    borderBottom: "1px solid #e8e8e8",
    display: "flex",
    flexWrap: "wrap",
    paddingBottom: "10px",
    paddingLeft: "12px"
  },
  filterIcon: {
    color: "#616161",
    height: "20px",
    width: "20px"
  },
  filterText: {
    fontWeight: 400 as 400,
    marginRight: "12px"
  }
});

interface FilterChipProps extends WithStyles<typeof styles> {
  filtersList: Filter[];
}

export const FilterChips = withStyles(styles, { name: "FilterChips" })(
  ({ classes, filtersList }: FilterChipProps) => (
    <div className={classes.filterContainer}>
      {filtersList.map(filter => (
        <div
          className={classes.filterButton}
          onClick={filter.onClick}
          key={filter.label}
        >
          <Typography className={classes.filterText}>{filter.label}</Typography>
          <ClearIcon className={classes.filterIcon} />
        </div>
      ))}
      <div
        className={classNames({
          [classes.filterButton]: true,
          [filtersList.length > 0
            ? classes.addFilterButtonPrimary
            : classes.addFilterButtonSecondary]: true
        })}
      >
        <AddIcon color={filtersList.length > 0 ? "primary" : "secondary"} />
        <Typography className={classes.addFilterText}>
          {i18n.t("Add Filter")}
        </Typography>
      </div>
    </div>
  )
);

export default FilterChips;
