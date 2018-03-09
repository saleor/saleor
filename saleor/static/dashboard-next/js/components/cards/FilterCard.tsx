import Button from "material-ui/Button";
import Card, { CardContent, CardActions } from "material-ui/Card";
import FilterListIcon from "material-ui-icons/FilterList";
import Typography from "material-ui/Typography";
import grey from "material-ui/colors/grey";
import { withStyles, WithStyles } from "material-ui/styles";
import * as React from "react";
import { Component } from "react";

import i18n from "../../i18n";

const decorate = withStyles(theme => ({
  filterCard: {
    transitionDuration: "200ms",
    [theme.breakpoints.down("sm")]: {
      maxHeight: 76,
      overflow: "hidden"
    }
  },
  filterCardExpandIconContainer: {
    position: "absolute" as "absolute",
    top: 21,
    right: 20,
    [theme.breakpoints.up("md")]: {
      display: "none"
    },
    "& svg": {
      width: 24,
      height: 24,
      fill: "#9e9e9e",
      cursor: "pointer"
    }
  },
  filterCardContent: {
    position: "relative" as "relative",
    borderBottomColor: grey[300],
    borderBottomStyle: "solid",
    borderBottomWidth: 1
  },
  filterCardActions: {
    flexDirection: "row-reverse" as "row-reverse"
  }
}));

interface FilterCardComponentProps {
  handleClear();
  handleSubmit();
}

interface FilterCardComponentState {
  collapsed: boolean;
}

export const FilterCard = decorate(
  class FilterCardComponent extends Component<
    FilterCardComponentProps &
      WithStyles<
        | "filterCard"
        | "filterCardExpandIconContainer"
        | "filterCardContent"
        | "filterCardActions"
      >,
    FilterCardComponentState
  > {
    state = {
      collapsed: true
    };

    handleFilterListIconClick = () => {
      this.setState(prevState => ({ collapsed: !prevState.collapsed }));
    };

    render() {
      const { children, classes, handleClear, handleSubmit } = this.props;
      return (
        <Card
          className={classes.filterCard}
          style={this.state.collapsed ? {} : { maxHeight: 1000 }}
        >
          <CardContent className={classes.filterCardContent}>
            <div className={classes.filterCardExpandIconContainer}>
              <FilterListIcon onClick={this.handleFilterListIconClick} />
            </div>
            <Typography variant="display1">{i18n.t("Filters")}</Typography>
          </CardContent>
          <form onSubmit={handleSubmit}>
            <CardContent>
              {children}
              <CardActions className={classes.filterCardActions}>
                <Button color="secondary" onClick={handleSubmit}>
                  {i18n.t("Filter", { context: "label" })}
                </Button>
                <Button color="default" onClick={handleClear}>
                  {i18n.t("Clear", { context: "label" })}
                </Button>
              </CardActions>
            </CardContent>
          </form>
        </Card>
      );
    }
  }
);
