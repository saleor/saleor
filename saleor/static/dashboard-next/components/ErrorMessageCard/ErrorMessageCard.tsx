import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import i18n from "../../i18n";

interface ErrorMessageCardProps {
  message: string;
}

const ErrorMessageCard: React.StatelessComponent<ErrorMessageCardProps> = ({
  message
}) => (
  <Card>
    <CardContent>
      <Typography variant="headline" component="h2">
        {i18n.t("Error", { context: "title" })}
      </Typography>
      <Typography variant="body1">{message}</Typography>
    </CardContent>
  </Card>
);
ErrorMessageCard.displayName = "ErrorMessageCard";
export default ErrorMessageCard;
