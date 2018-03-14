import Card, { CardContent } from "material-ui/Card";
import Typography from "material-ui/Typography";
import * as React from "react";

import i18n from "../../i18n";

interface ErrorMessageCardProps {
  message: string;
}

export const ErrorMessageCard: React.StatelessComponent<
  ErrorMessageCardProps
> = ({ message }) => (
  <Card>
    <CardContent>
      <Typography variant="display1">
        {i18n.t("Error", { context: "title" })}
      </Typography>
      <Typography variant="body1">{message}</Typography>
    </CardContent>
  </Card>
);

export default ErrorMessageCard;
