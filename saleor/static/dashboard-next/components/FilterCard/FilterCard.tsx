import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import CardHeader from "@material-ui/core/CardHeader";
import IconButton from "@material-ui/core/IconButton";
import RefreshIcon from "@material-ui/icons/Refresh";
import * as React from "react";

import i18n from "../../i18n";

export interface FilterCardProps {
  handleClear();
}

const FilterCard: React.StatelessComponent<FilterCardProps> = ({
  children,
  handleClear
}) => (
  <Card>
    <form>
      <CardHeader
        action={
          <IconButton onClick={handleClear}>
            <RefreshIcon />
          </IconButton>
        }
        title={i18n.t("Filters")}
      />
      <CardContent>{children}</CardContent>
    </form>
  </Card>
);
FilterCard.displayName = "FilterCard";
export default FilterCard;
