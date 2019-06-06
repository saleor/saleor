import ButtonBase from "@material-ui/core/ButtonBase";
import Grow from "@material-ui/core/Grow";
import Paper from "@material-ui/core/Paper";
import Popper from "@material-ui/core/Popper";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import { fade } from "@material-ui/core/styles/colorManipulator";
import Typography from "@material-ui/core/Typography";
import ArrowDropDownIcon from "@material-ui/icons/ArrowDropDown";
import * as classNames from "classnames";
import * as React from "react";

import { FilterContent } from ".";
import i18n from "../../i18n";
import { FilterContentSubmitData } from "./FilterContent";
import { IFilter } from "./types";

export interface FilterProps {
  currencySymbol: string;
  menu: IFilter;
  filterLabel: string;
  onFilterAdd: (filter: FilterContentSubmitData) => void;
}

const styles = (theme: Theme) =>
  createStyles({
    addFilterButton: {
      "&$filterButton": {
        "&:hover, &:focus": {
          backgroundColor: fade(theme.palette.primary.main, 0.1)
        },
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.primary.main}`,
        cursor: "pointer",
        marginBottom: 0,
        marginRight: theme.spacing.unit * 2,
        marginTop: 0,
        transition: theme.transitions.duration.short + "ms"
      }
    },
    addFilterButtonActive: {
      "&$addFilterButton": {
        backgroundColor: fade(theme.palette.primary.main, 0.1)
      }
    },
    addFilterIcon: {
      transition: theme.transitions.duration.short + "ms"
    },
    addFilterText: {
      color: theme.palette.primary.main,
      fontSize: 14,
      fontWeight: 600 as 600,
      marginRight: 4,
      textTransform: "uppercase"
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
    filterLabel: {
      marginBottom: theme.spacing.unit
    },
    paper: {
      marginTop: theme.spacing.unit * 2,
      padding: theme.spacing.unit * 2,
      width: 240
    },
    popover: {
      zIndex: 1
    },
    rotate: {
      transform: "rotate(180deg)"
    }
  });
const Filter = withStyles(styles, { name: "Filter" })(
  ({
    classes,
    currencySymbol,
    filterLabel,
    menu,
    onFilterAdd
  }: FilterProps & WithStyles<typeof styles>) => {
    const anchor = React.useRef<HTMLDivElement>();
    const [isFilterMenuOpened, setFilterMenuOpened] = React.useState(false);

    return (
      <div ref={anchor}>
        <ButtonBase
          className={classNames(classes.filterButton, classes.addFilterButton, {
            [classes.addFilterButtonActive]: isFilterMenuOpened
          })}
          onClick={() => setFilterMenuOpened(!isFilterMenuOpened)}
        >
          <Typography className={classes.addFilterText}>
            {i18n.t("Add Filter")}
          </Typography>
          <ArrowDropDownIcon
            color="primary"
            className={classNames(classes.addFilterIcon, {
              [classes.rotate]: isFilterMenuOpened
            })}
          />
        </ButtonBase>
        <Popper
          className={classes.popover}
          open={isFilterMenuOpened}
          anchorEl={anchor.current}
          transition
          disablePortal
          placement="bottom-start"
        >
          {({ TransitionProps, placement }) => (
            <Grow
              {...TransitionProps}
              style={{
                transformOrigin:
                  placement === "bottom" ? "right top" : "right bottom"
              }}
            >
              <Paper className={classes.paper}>
                <Typography className={classes.filterLabel}>
                  {filterLabel}
                </Typography>
                <FilterContent
                  currencySymbol={currencySymbol}
                  filters={menu}
                  onSubmit={data => {
                    onFilterAdd(data);
                    setFilterMenuOpened(false);
                  }}
                />
              </Paper>
            </Grow>
          )}
        </Popper>
      </div>
    );
  }
);
Filter.displayName = "Filter";
export default Filter;
