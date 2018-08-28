import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import { transformFulfillmentStatus } from "../..";
import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel/StatusLabel";
import TableCellAvatar from "../../../components/TableCellAvatar";
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
  trackingCode?: string;
  onFulfillmentCancel?();
  onTrackingCodeAdd?();
  onPackingSlipClick?();
}

const decorate = withStyles(
  theme => ({
    avatarCell: {
      paddingLeft: theme.spacing.unit * 2,
      paddingRight: theme.spacing.unit * 3,
      width: theme.spacing.unit * 5
    },
    root: {
      marginTop: theme.spacing.unit * 2,
      [theme.breakpoints.down("sm")]: {
        marginTop: theme.spacing.unit
      }
    },
    statusBar: {
      paddingTop: 0
    },
    textLeft: {
      textAlign: [["left"], "!important"] as any
    }
  }),
  { name: "OrderFulfillment" }
);
const OrderFulfillment = decorate<OrderFulfillmentProps>(
  ({
    classes,
    id,
    status,
    products,
    trackingCode,
    onFulfillmentCancel,
    onTrackingCodeAdd,
    onPackingSlipClick
  }) => (
    <Card className={classes.root}>
      <CardTitle
        title={id ? i18n.t("Fulfillment #{{ id }}", { id }) : undefined}
        toolbar={
          status !== "cancelled" && (
            <Button
              color="secondary"
              variant="flat"
              onClick={onPackingSlipClick}
            >
              {i18n.t("Packing slip")}
            </Button>
          )
        }
      >
        {status && (
          <StatusLabel
            status={transformFulfillmentStatus(status).status}
            label={transformFulfillmentStatus(status).localized}
            typographyProps={{ variant: "body1" }}
          />
        )}
      </CardTitle>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell />
            <TableCell className={classes.textLeft}>
              {i18n.t("Product")}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {products ? (
            products.map(productLine => (
              <TableRow key={productLine.product.id}>
                <TableCellAvatar thumbnail={productLine.product.thumbnailUrl} />
                <TableCell className={classes.textLeft}>
                  {productLine.product.name} x {productLine.quantity}
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCellAvatar />
              <TableCell>
                <Skeleton />
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
      {status !== "cancelled" && (
        <CardActions>
          <Button onClick={onTrackingCodeAdd}>
            {trackingCode
              ? i18n.t("Add tracking number")
              : i18n.t("Edit tracking number")}
          </Button>
          <Button onClick={onFulfillmentCancel}>
            {i18n.t("Cancel shipment")}
          </Button>
        </CardActions>
      )}
    </Card>
  )
);
export default OrderFulfillment;
