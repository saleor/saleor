import Cached from "@material-ui/icons/Cached";
import Avatar from "material-ui/Avatar";
import Button from "material-ui/Button";
import Card, { CardActions, CardContent } from "material-ui/Card";
import blue from "material-ui/colors/blue";
import { withStyles } from "material-ui/styles";
import Table, {
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableRow
} from "material-ui/Table";
import Typography from "material-ui/Typography";
import * as React from "react";

import Money from "../../../components/Money";
import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface TaxedMoneyType {
  gross: {
    amount: number;
    currency: string;
  };
}
interface MoneyType {
  amount: number;
  currency: string;
}
export interface OrderProductsProps {
  displayPayment?: boolean;
  net?: MoneyType;
  paid?: MoneyType;
  products?: Array<{
    id: string;
    name: string;
    price: TaxedMoneyType;
    quantity: number;
    sku: string;
    thumbnailUrl: string;
  }>;
  refunded?: MoneyType;
  subtotal?: MoneyType;
  total?: MoneyType;
  onRowClick?(id: string);
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
  denseTable: {
    "& td, & th": {
      paddingRight: theme.spacing.unit * 3
    }
  },
  link: {
    color: blue[500],
    cursor: "pointer"
  },
  textRight: {
    textAlign: "right" as "right"
  },
  flexBox: {
    display: "flex",
    flexDirection: "column" as "column",
    height: theme.spacing.unit * 12,
    justifyContent: "space-evenly"
  }
}));
const OrderProducts = decorate<OrderProductsProps>(
  ({
    classes,
    displayPayment,
    net,
    paid,
    products,
    refunded,
    subtotal,
    total,
    onRowClick
  }) => (
    <Table className={classes.denseTable}>
      <TableHead>
        <TableRow>
          <TableCell className={classes.avatarCell} />
          <TableCell>{i18n.t("Name", { context: "object" })}</TableCell>
          <TableCell>{i18n.t("SKU", { context: "object" })}</TableCell>
          <TableCell className={classes.textRight}>
            {i18n.t("Unit price", { context: "object" })}
          </TableCell>
          <TableCell className={classes.textRight}>
            {i18n.t("Quantity", { context: "object" })}
          </TableCell>
          <TableCell className={classes.textRight}>
            {i18n.t("Price", { context: "object" })}
          </TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {products === undefined || products === null ? (
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
            <TableCell>
              <Skeleton />
            </TableCell>
            <TableCell>
              <Skeleton />
            </TableCell>
            <TableCell>
              <Skeleton />
            </TableCell>
          </TableRow>
        ) : products.length > 0 ? (
          products.map(product => (
            <TableRow key={product.id}>
              <TableCell className={classes.avatarCell}>
                <Avatar src={product.thumbnailUrl} />
              </TableCell>
              <TableCell>
                <span
                  onClick={onRowClick ? onRowClick(product.id) : () => {}}
                  className={onRowClick ? classes.link : ""}
                >
                  {product.name}
                </span>
              </TableCell>
              <TableCell>{product.sku}</TableCell>
              <TableCell className={classes.textRight}>
                <Money
                  amount={product.price.gross.amount}
                  currency={product.price.gross.currency}
                />
              </TableCell>
              <TableCell className={classes.textRight}>
                {product.quantity}
              </TableCell>
              <TableCell className={classes.textRight}>
                <Money
                  amount={product.price.gross.amount * product.quantity}
                  currency={product.price.gross.currency}
                />
              </TableCell>
            </TableRow>
          ))
        ) : (
          <TableRow>
            <TableCell className={classes.avatarCell} />
            <TableCell colSpan={2}>{i18n.t("No products found")}</TableCell>
          </TableRow>
        )}
        <TableRow>
          <TableCell colSpan={5} className={classes.textRight}>
            <div className={classes.flexBox}>
              <Typography>{i18n.t("Subtotal")}</Typography>
              <Typography>{i18n.t("Shipping")}</Typography>
              <Typography>
                <b>{i18n.t("Total")}</b>
              </Typography>
            </div>
          </TableCell>
          <TableCell className={classes.textRight}>
            <div className={classes.flexBox}>
              {subtotal ? (
                <Money amount={subtotal.amount} currency={subtotal.currency} />
              ) : (
                <Skeleton />
              )}
              {subtotal ? (
                <Money amount={subtotal.amount} currency={subtotal.currency} />
              ) : (
                <Skeleton />
              )}
              {total ? (
                <Money amount={total.amount} currency={total.currency} />
              ) : (
                <Skeleton />
              )}
            </div>
          </TableCell>
        </TableRow>
        {displayPayment && (
          <TableRow>
            <TableCell colSpan={5} className={classes.textRight}>
              <div className={classes.flexBox}>
                <Typography>{i18n.t("Paid by customer")}</Typography>
                <Typography>{i18n.t("Refunded")}</Typography>
                <Typography>
                  <b>{i18n.t("Net payment")}</b>
                </Typography>
              </div>
            </TableCell>
            <TableCell className={classes.textRight}>
              <div className={classes.flexBox}>
                {paid ? (
                  <Money amount={paid.amount} currency={paid.currency} />
                ) : (
                  <Skeleton />
                )}
                {refunded ? (
                  <Money
                    amount={-refunded.amount}
                    currency={refunded.currency}
                  />
                ) : (
                  <Skeleton />
                )}
                {net ? (
                  <Money amount={net.amount} currency={net.currency} />
                ) : (
                  <Skeleton />
                )}
              </div>
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  )
);
export default OrderProducts;
