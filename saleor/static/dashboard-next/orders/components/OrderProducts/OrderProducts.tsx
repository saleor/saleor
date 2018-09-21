import blue from "@material-ui/core/colors/blue";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
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
  authorized?: MoneyType;
  isDraft?: boolean;
  lines?: Array<{
    id: string;
    productName: string;
    unitPrice: TaxedMoneyType;
    quantity: number;
    productSku: string;
    thumbnailUrl: string;
  }>;
  paid?: MoneyType;
  shippingMethodName?: string;
  shippingPrice?: {
    gross: MoneyType;
  };
  subtotal?: MoneyType;
  tax?: MoneyType;
  total?: MoneyType;
  onOrderLineChange?(id: string): (value: string) => void;
  onOrderLineRemove(id: string);
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
    noBorder: {
      border: "none"
    },
    textRight: {
      textAlign: "right" as "right"
    },
    thinRow: {
      height: 24
    }
  }),
  { name: "OrderProducts" }
);
const OrderProducts = decorate<OrderProductsProps>(
  ({
    authorized,
    classes,
    isDraft,
    lines,
    paid,
    shippingMethodName,
    shippingPrice,
    subtotal,
    tax,
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
          lines,
          product => (
            <TableRow key={product ? product.id : "skeleton"}>
              {product && isDraft ? (
                <TableCell className={classes.avatarCell}>
                  <IconButton
                    onClick={() => onOrderLineRemove(product.id)}
                    disabled={!onOrderLineRemove}
                    className={classes.deleteIcon}
                  >
                    <CloseIcon />
                  </IconButton>
                </TableCell>
              ) : product ? (
                <TableCellAvatar thumbnail={product.thumbnailUrl} />
              ) : (
                <TableCellAvatar />
              )}
              <TableCell>
                {product ? (
                  <span
                    onClick={onRowClick && onRowClick(product.id)}
                    className={classes.link}
                  >
                    {product.productName}
                  </span>
                ) : (
                  <Skeleton />
                )}
              </TableCell>
              <TableCell>
                {product ? product.productSku : <Skeleton />}
              </TableCell>
              <TableCell className={classes.textRight}>
                {product && product.unitPrice && product.unitPrice.gross ? (
                  <Money
                    amount={product.unitPrice.gross.amount}
                    currency={product.unitPrice.gross.currency}
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
                {product && product.unitPrice && product.unitPrice.gross ? (
                  <Money
                    amount={product.unitPrice.gross.amount * product.quantity}
                    currency={product.unitPrice.gross.currency}
                  />
                ) : (
                  <Skeleton />
                )}
              </TableCell>
            </TableRow>
          ),
          () => (
            <TableRow>
              <TableCell colSpan={6}>{i18n.t("No products found")}</TableCell>
            </TableRow>
          )
        )}
        <TableRow className={classes.thinRow} />
        <TableRow className={classes.thinRow}>
          <TableCell className={classes.noBorder} colSpan={5}>
            {i18n.t("Subtotal")}
          </TableCell>
          <TableCell
            className={classNames([classes.noBorder, classes.textRight])}
          >
            {subtotal ? (
              <Money
                amount={subtotal.amount}
                currency={subtotal.currency}
                typographyProps={{ component: "p" }}
              />
            ) : (
              <Skeleton />
            )}
          </TableCell>
        </TableRow>
        <TableRow className={classes.thinRow}>
          <TableCell
            colSpan={5}
            className={classNames({
              [classes.link]: isDraft,
              [classes.noBorder]: true
            })}
            onClick={isDraft ? onShippingMethodClick : undefined}
          >
            {shippingMethodName ? shippingMethodName : i18n.t("Shipping")}
          </TableCell>
          <TableCell
            className={classNames([classes.noBorder, classes.textRight])}
          >
            {shippingPrice && shippingPrice.gross ? (
              <Money
                amount={shippingPrice.gross.amount}
                currency={shippingPrice.gross.currency}
              />
            ) : (
              <Skeleton />
            )}
          </TableCell>
        </TableRow>
        {tax &&
          tax.amount > 0 && (
            <TableRow className={classes.thinRow}>
              <TableCell className={classes.noBorder} colSpan={5}>
                {i18n.t("Tax (included)")}
              </TableCell>
              <TableCell
                className={classNames([classes.noBorder, classes.textRight])}
              >
                <Money amount={tax.amount} currency={tax.currency} />
              </TableCell>
            </TableRow>
          )}
        <TableRow className={classes.thinRow}>
          <TableCell className={classes.noBorder} colSpan={5}>
            <b>{i18n.t("Total")}</b>
          </TableCell>
          <TableCell
            className={classNames([classes.noBorder, classes.textRight])}
          >
            {total ? (
              <Money amount={total.amount} currency={total.currency} />
            ) : (
              <Skeleton />
            )}
          </TableCell>
        </TableRow>
        {!isDraft && (
          <>
            <TableRow className={classes.thinRow}>
              <TableCell colSpan={5} className={classes.noBorder}>
                {i18n.t("Authorized")}
              </TableCell>
              <TableCell
                className={classNames([classes.noBorder, classes.textRight])}
              >
                {authorized ? (
                  <Money
                    amount={authorized.amount}
                    currency={authorized.currency}
                  />
                ) : (
                  <Skeleton />
                )}
              </TableCell>
            </TableRow>
            <TableRow className={classes.thinRow}>
              <TableCell colSpan={5} className={classes.noBorder}>
                <b>{i18n.t("Net payment")}</b>
              </TableCell>
              <TableCell
                className={classNames([classes.noBorder, classes.textRight])}
              >
                {paid ? (
                  <Money amount={paid.amount} currency={paid.currency} />
                ) : (
                  <Skeleton />
                )}
              </TableCell>
            </TableRow>
          </>
        )}
        <TableRow className={classes.thinRow} />
      </TableBody>
    </Table>
  )
);
export default OrderProducts;
