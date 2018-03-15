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

export interface FilterCardProps {
  handleClear();
  handleSubmit(t);
}

const FilterCard = decorate<FilterCardProps>(props => {
  const { children, classes, handleClear, handleSubmit } = props;
  return (
    <Card>
      <CardContent className={classes.filterCardContent}>
        <Typography variant="display1">{i18n.t("Filters")}</Typography>
      </CardContent>
      <form onSubmit={handleSubmit}>
        <CardContent>{children}</CardContent>
        <CardActions className={classes.filterCardActions}>
          <Button color="secondary" onClick={handleSubmit}>
            {i18n.t("Filter", { context: "label" })}
          </Button>
          <Button color="default" onClick={handleClear}>
            {i18n.t("Clear", { context: "label" })}
          </Button>
        </CardActions>
      </form>
    </Card>
  );
});

export default FilterCard;
