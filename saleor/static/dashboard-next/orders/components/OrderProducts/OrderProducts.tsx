import Avatar from "@material-ui/core/Avatar";
import blue from "@material-ui/core/colors/blue";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import Typography from "@material-ui/core/Typography";
import Cached from "@material-ui/icons/Cached";
import CloseIcon from "@material-ui/icons/Close";
import * as React from "react";

import EditableTableCell from "../../../components/EditableTableCell";
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
  isDraft?: boolean;
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
  shippingMethod?: {
    name: string;
    price: MoneyType;
  };
  refunded?: MoneyType;
  subtotal?: MoneyType;
  total?: MoneyType;
  onOrderLineChange?(id: string): (value: string) => () => void;
  onOrderLineRemove?(id: string): () => any;
  onRowClick?(id: string): () => any;
  onShippingMethodClick?();
}

const decorate = withStyles(
  theme => ({
    avatarCell: {
      paddingLeft: theme.spacing.unit * 2,
      paddingRight: theme.spacing.unit * 3,
      width: theme.spacing.unit * 5
    },
    cardActions: {
      direction: "rtl" as "rtl"
    },
    deleteIcon: {
      height: 40,
      width: 40
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
  }),
  { name: "OrderProducts" }
);
const OrderProducts = decorate<OrderProductsProps>(
  ({
    classes,
    isDraft,
    net,
    paid,
    products,
    refunded,
    shippingMethod,
    subtotal,
    total,
    onOrderLineChange,
    onOrderLineRemove,
    onRowClick,
    onShippingMethodClick
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
              {isDraft ? (
                <TableCell className={classes.avatarCell}>
                  <IconButton
                    onClick={
                      !!onOrderLineRemove
                        ? onOrderLineRemove(product.id)
                        : undefined
                    }
                    disabled={!onOrderLineRemove}
                    className={classes.deleteIcon}
                  >
                    <CloseIcon />
                  </IconButton>
                </TableCell>
              ) : (
                <TableCell className={classes.avatarCell}>
                  <Avatar src={product.thumbnailUrl} />
                </TableCell>
              )}
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
              {isDraft && !!onOrderLineChange ? (
                <EditableTableCell
                  className={classes.textRight}
                  InputProps={{
                    label: i18n.t("Quantity"),
                    type: "number"
                  }}
                  value={product.quantity.toString()}
                  onConfirm={onOrderLineChange(product.id)}
                />
              ) : (
                <TableCell className={classes.textRight}>
                  {product.quantity}
                </TableCell>
              )}
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
              <Typography
                className={
                  isDraft && !!onShippingMethodClick ? classes.link : ""
                }
                onClick={onShippingMethodClick}
              >
                {shippingMethod ? shippingMethod.name : i18n.t("Shipping")}
              </Typography>
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
              {shippingMethod && shippingMethod.price ? (
                <Money
                  amount={shippingMethod.price.amount}
                  currency={shippingMethod.price.currency}
                />
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
        {!isDraft && (
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
