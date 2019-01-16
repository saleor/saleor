import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface OrderCustomerNoteProps {
  note: string;
}

export const OrderCustomerNote: React.StatelessComponent<
  OrderCustomerNoteProps
> = ({ note }) => (
  <Card>
    <CardTitle
      title={i18n.t("Notes", {
        context: "customer notes"
      })}
    />
    <CardContent>
      {note === undefined ? (
        <Skeleton />
      ) : note === "" ? (
        <Typography color="textSecondary">
          {i18n.t("No notes from customer")}
        </Typography>
      ) : (
        <Typography>{note}</Typography>
      )}
    </CardContent>
  </Card>
);
export default OrderCustomerNote;
