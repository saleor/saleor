import { withStyles } from "@material-ui/core/styles";
import Tab from "@material-ui/core/Tab";
import Tabs from "@material-ui/core/Tabs";
import Typography from "@material-ui/core/Typography";
import ClearIcon from "@material-ui/icons/Clear";
import * as React from "react";

import i18n from "../../../i18n";
import { Filter } from "../../../products/components/ProductListCard";

interface OrderListFilterProps {
  currentTab: number;
  filtersList: Filter[];
}

const decorate = withStyles(theme => ({
  filterButton: {
    alignItems: "center",
    backgroundColor: "rgba(90, 179, 120, .25)",
    borderRadius: "19px",
    cursor: "pointer",
    display: "flex",
    height: "38px",
    justifyContent: "space-around",
    margin: "10px 0 10px 12px",
    minWidth: "160px",
    padding: "0 8px 0 16px"
  },
  filterContainer: {
    borderBottom: "1px solid #e8e8e8",
    display: "flex",
    flexWrap: "wrap" as "wrap",
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
  },
  tabLabel: {
    color: "#616161",
    fontSize: "0.875rem"
  },
  tabRoot: {
    minWidth: "80px",
    opacity: 1,
    paddingTop: `${theme.spacing.unit * 1}px`,
    textTransform: "initial" as "initial"
  },
  tabsRoot: {
    borderBottom: "1px solid #e0e0e0",
    paddingLeft: `${theme.spacing.unit * 3}px`
  }
}));

const OrderListFilter = decorate<OrderListFilterProps>(
  ({ classes, filtersList, currentTab }) => (
    <>
      <Tabs className={classes.tabsRoot} value={0} indicatorColor={"primary"}>
        <Tab
          disableRipple
          classes={{ root: classes.tabRoot, label: classes.tabLabel }}
          label={i18n.t("All Products")}
        />
        <Tab
          disableRipple
          classes={{ root: classes.tabRoot, label: classes.tabLabel }}
          label={i18n.t("Ready to fulfill")}
        />
        <Tab
          disableRipple
          classes={{ root: classes.tabRoot, label: classes.tabLabel }}
          label={i18n.t("Ready to capture")}
        />
        {(currentTab === 0 || undefined) &&
          filtersList &&
          filtersList.length > 0 && (
            <Tab
              value={0}
              disableRipple
              classes={{
                label: classes.tabLabel,
                root: classes.tabRoot
              }}
              label={i18n.t("Custom Filter")}
            />
          )}
      </Tabs>
      {(currentTab === 0 || undefined) &&
        filtersList &&
        filtersList.length > 0 && (
          <div className={classes.filterContainer}>
            {filtersList.map(filter => (
              <div className={classes.filterButton}>
                <Typography className={classes.filterText}>
                  {i18n.t(filter.label)}
                </Typography>
                <ClearIcon className={classes.filterIcon} />
              </div>
            ))}
          </div>
        )}
    </>
  )
);
OrderListFilter.displayName = "OrderListFilter";
export default OrderListFilter;
