import RefreshIcon from "@material-ui/icons/Refresh";
import Card, { CardContent, CardHeader } from "material-ui/Card";
import IconButton from "material-ui/IconButton";
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

export default FilterCard;
