import Avatar from "@material-ui/core/Avatar";
import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import CardContent from "@material-ui/core/CardContent";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import Cached from "@material-ui/icons/Cached";
import PrintIcon from "@material-ui/icons/Print";
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
    textRight: {
      textAlign: "right" as "right"
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
      <PageHeader
        title={id ? i18n.t("Fulfillment #{{ id }}", { id }) : undefined}
      >
        {status !== "cancelled" && (
          <IconButton
            disabled={!onPackingSlipClick}
            onClick={onPackingSlipClick}
          >
            <PrintIcon />
          </IconButton>
        )}
      </PageHeader>
      {status && (
        <CardContent className={classes.statusBar}>
          <StatusLabel
            status={transformFulfillmentStatus(status).status}
            label={transformFulfillmentStatus(status).localized}
          />
        </CardContent>
      )}
      <Table>
        <TableHead>
          <TableRow>
            <TableCell />
            <TableCell>{i18n.t("Product")}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {products ? (
            products.map(productLine => (
              <TableRow key={productLine.product.id}>
                <TableCell className={classes.avatarCell}>
                  <Avatar src={productLine.product.thumbnailUrl} />
                </TableCell>
                <TableCell>
                  {productLine.product.name} x {productLine.quantity}
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
            </TableRow>
          )}
        </TableBody>
      </Table>
      {status !== "cancelled" && (
        <CardActions>
          <Button disabled={!onTrackingCodeAdd} onClick={onTrackingCodeAdd}>
            {trackingCode
              ? i18n.t("Add tracking number")
              : i18n.t("Edit tracking number")}
          </Button>
          <Button disabled={!onFulfillmentCancel} onClick={onFulfillmentCancel}>
            {i18n.t("Cancel shipment")}
          </Button>
        </CardActions>
      )}
    </Card>
  )
);
export default OrderFulfillment;
