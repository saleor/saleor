import Card, { CardContent } from "material-ui/Card";
import Typography from "material-ui/Typography";
import * as React from "react";

import { pgettext } from "../../i18n";

interface ErrorMessageCardProps {
  message: string;
}
export const ErrorMessageCard: React.StatelessComponent<
  ErrorMessageCardProps
> = ({ message }) => (
  <Card>
    <CardContent>
      <Typography variant={"display1"}>
        {pgettext("Dashboard error message card title", "Error")}
      </Typography>
      <Typography variant={"body1"}>{message}</Typography>
    </CardContent>
  </Card>
);
