import blue from "@material-ui/core/colors/blue";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import Typography from "@material-ui/core/Typography";
import CloseIcon from "@material-ui/icons/Close";
import * as classNames from "classnames";
import * as React from "react";

import EditableTableCell from "../../../components/EditableTableCell";
import Money from "../../../components/Money";
import Skeleton from "../../../components/Skeleton";
import TableCellAvatar from "../../../components/TableCellAvatar";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";

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
    flexBox: {
      display: "flex",
      flexDirection: "column" as "column",
      height: theme.spacing.unit * 12,
      justifyContent: "space-evenly"
    },
    link: {
      color: blue[500],
      cursor: "pointer"
    },
    textRight: {
      textAlign: "right" as "right"
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
        {renderCollection(
          products,
          product => (
            <TableRow key={product ? product.id : "skeleton"}>
              {product && isDraft ? (
                <TableCell className={classes.avatarCell}>
                  <IconButton
                    onClick={onOrderLineRemove && onOrderLineRemove(product.id)}
                    disabled={!onOrderLineRemove}
                    className={classes.deleteIcon}
                  >
                    <CloseIcon />
                  </IconButton>
                </TableCell>
              ) : (
                <TableCellAvatar thumbnail={product && product.thumbnailUrl} />
              )}
              <TableCell>
                {product ? (
                  <span
                    onClick={onRowClick && onRowClick(product.id)}
                    className={classes.link}
                  >
                    {product.name}
                  </span>
                ) : (
                  <Skeleton />
                )}
              </TableCell>
              <TableCell>{product ? product.sku : <Skeleton />}</TableCell>
              <TableCell className={classes.textRight}>
                {product && product.price && product.price.gross ? (
                  <Money
                    amount={product.price.gross.amount}
                    currency={product.price.gross.currency}
                  />
                ) : (
                  <Skeleton />
                )}
              </TableCell>
              {product && isDraft && onOrderLineChange ? (
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
                  {product ? product.quantity : <Skeleton />}
                </TableCell>
              )}
              <TableCell className={classes.textRight}>
                {product && product.price && product.price.gross ? (
                  <Money
                    amount={product.price.gross.amount * product.quantity}
                    currency={product.price.gross.currency}
                  />
                ) : (
                  <Skeleton />
                )}
              </TableCell>
            </TableRow>
          ),
          () => (
            <TableRow>
              <TableCell className={classes.avatarCell} />
              <TableCell colSpan={2}>{i18n.t("No products found")}</TableCell>
            </TableRow>
          )
        )}
        <TableRow>
          <TableCell colSpan={5} className={classes.textRight}>
            <div className={classes.flexBox}>
              <Typography>{i18n.t("Subtotal")}</Typography>
              <Typography
                className={classNames({ [classes.link]: isDraft })}
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
                <Money
                  amount={subtotal.amount}
                  currency={subtotal.currency}
                  typographyProps={{ component: "p" }}
                />
              ) : (
                <Skeleton />
              )}
              {shippingMethod && shippingMethod.price ? (
                <Money
                  amount={shippingMethod.price.amount}
                  currency={shippingMethod.price.currency}
                  typographyProps={{ component: "p" }}
                />
              ) : (
                <Skeleton />
              )}
              {total ? (
                <Money
                  amount={total.amount}
                  currency={total.currency}
                  typographyProps={{ component: "p" }}
                />
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
                  <Money
                    amount={paid.amount}
                    currency={paid.currency}
                    typographyProps={{ component: "p" }}
                  />
                ) : (
                  <Skeleton />
                )}
                {refunded ? (
                  <Money
                    amount={-refunded.amount}
                    currency={refunded.currency}
                    typographyProps={{ component: "p" }}
                  />
                ) : (
                  <Skeleton />
                )}
                {net ? (
                  <Money
                    amount={net.amount}
                    currency={net.currency}
                    typographyProps={{ component: "p" }}
                  />
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
