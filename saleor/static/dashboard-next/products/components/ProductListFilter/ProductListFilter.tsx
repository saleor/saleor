import { withStyles } from "@material-ui/core/styles";
import ClearIcon from "@material-ui/icons/Clear";
// import Typographt from "@material-ui/core/Typography";
import Tab from "@material-ui/core/Tab";
import Tabs from "@material-ui/core/Tabs";
import * as React from "react";

// import i18n from "../../../i18n";

interface ProductListFilterProps {
  disabled?: boolean;
}

const decorate = withStyles(theme => ({
  clearIcon: {
color: "#b2b2b2",
heigh: "18px,
wodth" 18px"
  }
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
  tabWrapper: {
    flexDirection: "row-reverse" as "row-reverse"
  },
  tabsRoot: {
    borderBottom: "1px solid #e0e0e0",
    paddingLeft: `${theme.spacing.unit * 3}px`
  }
}));

const ProductListFilter = decorate<ProductListFilterProps>(({ classes }) => (
  <Tabs className={classes.tabsRoot} value={0} indicatorColor={"primary"}>
    <Tab
      disableRipple
      classes={{ root: classes.tabRoot, label: classes.tabLabel }}
      label={"All Products"}
    />
    <Tab
      disableRipple
      classes={{ root: classes.tabRoot, label: classes.tabLabel }}
      label={"Available"}
    />
    <Tab
      disableRipple
      classes={{ root: classes.tabRoot, label: classes.tabLabel }}
      label={"Out of stock"}
    />
    <Tab
      disableRipple
      classes={{
        label: classes.tabLabel,
        root: classes.tabRoot,
        wrapper: classes.tabWrapper
      }}
      label={"Custom filter"}
      icon={<ClearIcon />}
    />
  </Tabs>
));
ProductListFilter.displayName = "ProductListFilter";
export default ProductListFilter;
