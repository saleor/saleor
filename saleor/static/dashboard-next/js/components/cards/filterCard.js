import React, { Component, Fragment } from "react";
import Button from "material-ui/Button";
import Card, { CardContent, CardActions } from "material-ui/Card";
import FilterListIcon from "material-ui-icons/FilterList";
import PropTypes from "prop-types";
import Typography from "material-ui/Typography";
import grey from "material-ui/colors/grey";
import { withStyles } from "material-ui/styles";

import { pgettext } from "../../i18n";

const styles = theme => ({
  filterCard: {
    transitionDuration: "200ms",
    [theme.breakpoints.down("sm")]: {
      maxHeight: 76,
      overflow: "hidden"
    }
  },
  filterCardExpandIconContainer: {
    position: "absolute",
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
    position: "relative",
    borderBottomColor: grey[300],
    borderBottomStyle: "solid",
    borderBottomWidth: 1
  },
  filterCardActions: {
    flexDirection: "row-reverse"
  }
});

class FilterCardComponent extends Component {
  static propTypes = {
    buttonClearLabel: PropTypes.string,
    buttonSubmitLabel: PropTypes.string,
    cardTitle: PropTypes.string,
    children: PropTypes.object,
    classes: PropTypes.object,
    handleClear: PropTypes.func,
    handleSubmit: PropTypes.func,
    noFiltersAvailableLabel: PropTypes.string
  };

  static defaultProps = {
    buttonClearLabel: pgettext("Filter bar clear fields", "Clear"),
    buttonSubmitLabel: pgettext("Filter bar submit", "Filter"),
    cardTitle: pgettext("Filter menu label", "Filters"),
    noFiltersAvailableLabel: pgettext(
      "Filter bar no filters",
      "No filters available"
    )
  };

  constructor(props) {
    super(props);
    this.state = {
      collapsed: true
    };
    this.handleFilterListIconClick = this.handleFilterListIconClick.bind(this);
  }

  handleFilterListIconClick() {
    this.setState(prevState => ({ collapsed: !prevState.collapsed }));
  }

  render() {
    const {
      buttonClearLabel,
      buttonSubmitLabel,
      cardTitle,
      children,
      classes,
      handleClear,
      handleSubmit,
      noFiltersAvailableLabel
    } = this.props;
    return (
      <Card
        className={classes.filterCard}
        style={this.state.collapsed ? {} : { maxHeight: 1000 }}
      >
        <CardContent className={classes.filterCardContent}>
          <div className={classes.filterCardExpandIconContainer}>
            <FilterListIcon onClick={this.handleFilterListIconClick} />
          </div>
          <Typography variant="display1">{cardTitle}</Typography>
        </CardContent>
        <form onSubmit={handleSubmit}>
          <CardContent>
            {children ? (
              <Fragment>
                {children}
                <CardActions className={classes.filterCardActions}>
                  <Button color="secondary" onClick={handleSubmit}>
                    {buttonSubmitLabel}
                  </Button>
                  <Button color="default" onClick={handleClear}>
                    {buttonClearLabel}
                  </Button>
                </CardActions>
              </Fragment>
            ) : (
              <Typography>{noFiltersAvailableLabel}</Typography>
            )}
          </CardContent>
        </form>
      </Card>
    );
  }
}

const FilterCard = withStyles(styles)(FilterCardComponent);

export { FilterCard as default, FilterCardComponent };
