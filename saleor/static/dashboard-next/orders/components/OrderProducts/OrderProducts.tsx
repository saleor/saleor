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
interface OrderProductsProps {
  products?: Array<{
    id: string;
    name: string;
    sku: string;
    thumbnailUrl: string;
    price: TaxedMoneyType;
    quantity: number;
  }>;
  subtotal: MoneyType;
  total: MoneyType;
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
  }
}));
const OrderProducts = decorate<OrderProductsProps>(
  ({ classes, products, subtotal, total, onRowClick }) => (
    <Card>
      <PageHeader title={i18n.t("Ordered items")} />
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
        <TableFooter>
          <TableRow>
            <TableCell colSpan={5} className={classes.textRight}>
              <Typography>{i18n.t("Subtotal")}</Typography>
              <Typography>{i18n.t("Shipping")}</Typography>
              <Typography>
                <b>{i18n.t("Total")}</b>
              </Typography>
            </TableCell>
            <TableCell className={classes.textRight}>
              {subtotal ? (
                <Money amount={subtotal.amount} currency={subtotal.currency} />
              ) : (
                <p>
                  <Skeleton />
                </p>
              )}
              {subtotal ? (
                <Money amount={subtotal.amount} currency={subtotal.currency} />
              ) : (
                <p>
                  <Skeleton />
                </p>
              )}
              {total ? (
                <Money amount={total.amount} currency={total.currency} />
              ) : (
                <p>
                  <Skeleton />
                </p>
              )}
            </TableCell>
          </TableRow>
        </TableFooter>
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
        </TableBody>
      </Table>
      {/* <CardActions className={classes.cardActions}>
        <Button>{i18n.t("Fulfill")}</Button>
      </CardActions> */}
    </Card>
  )
);
export default OrderProducts;
