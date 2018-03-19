import Button from "material-ui/Button";
import Card, { CardContent, CardActions, CardHeader } from "material-ui/Card";
import IconButton from "material-ui/IconButton";
import Cancel from "material-ui-icons/Cancel";
import { withStyles } from "material-ui/styles";
import * as React from "react";

import i18n from "../../i18n";

const decorate = withStyles(theme => ({
  filterCardActions: {
    flexDirection: "row-reverse" as "row-reverse"
  }
}));

export interface FilterCardProps {
  handleClear();
  handleSubmit();
}

const FilterCard = decorate<FilterCardProps>(props => {
  const { children, classes, handleClear, handleSubmit } = props;
  return (
    <Card>
      <form onSubmit={handleSubmit}>
        <CardHeader
          action={
            <IconButton onClick={handleClear}>
              <Cancel />
            </IconButton>
          }
          title={i18n.t("Filters")}
        />
        <CardContent>{children}</CardContent>
        <CardActions className={classes.filterCardActions}>
          <Button onClick={handleClear} variant="raised">
            {i18n.t("Filter", { context: "label" })}
          </Button>
        </CardActions>
      </form>
    </Card>
  );
});

export default FilterCard;
