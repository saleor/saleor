import Cached from "@material-ui/icons/Cached";
import Avatar from "material-ui/Avatar";
import Button from "material-ui/Button";
import Card, { CardActions } from "material-ui/Card";
import { withStyles } from "material-ui/styles";
import Table, {
  TableBody,
  TableCell,
  TableHead,
  TableRow
} from "material-ui/Table";
import * as React from "react";

import { transformFulfillmentStatus } from "../..";
import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel/StatusLabel";
import i18n from "../../../i18n";

interface OrderFulfillmentProps {
  id?: string;
  status?: string;
  products?: Array<{
    quantity: number;
    product: {
      id: string;
      name: string;
      thumbnailUrl: string;
    };
  }>;
}

const decorate = withStyles(theme => ({
  avatarCell: {
    paddingLeft: theme.spacing.unit * 2,
    paddingRight: theme.spacing.unit * 3,
    width: theme.spacing.unit * 5
  },
  cardActions: {
    direction: "rtl" as "rtl"
  },
  root: {
    marginTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("sm")]: {
      marginTop: theme.spacing.unit
    }
  },
  textRight: {
    textAlign: "right" as "right"
  }
}));
const OrderFulfillment = decorate<OrderFulfillmentProps>(
  ({ classes, id, status, products }) => (
    <Card className={classes.root}>
      <PageHeader
        title={id ? i18n.t("Fulfillment #{{ id }}", { id }) : undefined}
      >
        {status && (
          <StatusLabel
            status={transformFulfillmentStatus(status).status}
            label={transformFulfillmentStatus(status).localized}
          />
        )}
      </PageHeader>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell />
            <TableCell>{i18n.t("Product")}</TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Quantity")}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {products ? (
            products.map(productLine => (
              <TableRow>
                <TableCell className={classes.avatarCell}>
                  <Avatar src={productLine.product.thumbnailUrl} />
                </TableCell>
                <TableCell>{productLine.product.name}</TableCell>
                <TableCell className={classes.textRight}>
                  {productLine.quantity}
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell className={classes.avatarCell}>
                <Avatar>
                  <Cached />
                </Avatar>
              </TableCell>
              <TableCell>
                <Skeleton />
              </TableCell>
              <TableCell>
                <Skeleton />
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
      <CardActions className={classes.cardActions}>
        <Button>{i18n.t("Packing slip")}</Button>
        <Button>{i18n.t("Add tracking number")}</Button>
        <Button>{i18n.t("Cancel shipment")}</Button>
      </CardActions>
    </Card>
  )
);
export default OrderFulfillment;
