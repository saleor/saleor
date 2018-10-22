import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";
import Money from "../../../components/Money";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";

import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import TableCellAvatar from "../../../components/TableCellAvatar";

interface MoneyType {
  amount: number;
  currency: string;
}
interface HomeProductListProps {
  topProducts?: Array<{
    id: string;
    name: string;
    orders: number;
    price: MoneyType;
    thumbnailUrl: string;
    variant: string;
  }>;
  onRowClick: (id: string) => () => void;
  disabled: boolean;
}

const decorate = withStyles(theme => ({
  avatarSize: {
    height: "64px",
    width: "64px"
  },
  tableRowPointer: {
    cursor: "pointer" as "pointer"
  },
  tableRowSize: {
    paddingBottom: theme.spacing.unit * 2,
    paddingTop: theme.spacing.unit * 2
  }
}));

export const HomeProductList = decorate<HomeProductListProps>(
  ({ classes, topProducts, onRowClick }) => (
    <Table>
      <TableBody>
        {renderCollection(
          topProducts,
          product => (
            <TableRow
              key={product ? product.id : "skeleton"}
              hover={!!product}
              className={classNames({
                [classes.tableRowPointer]: !!product
              })}
              onClick={!!product ? onRowClick(product.id) : undefined}
            >
              <TableCellAvatar
                className={classes.tableRowSize}
                thumbnail={product && product.thumbnailUrl}
                avatarSize={classes.avatarSize}
              />
              {product ? (
                <TableCell>
                  <Typography color={"primary"} variant="body1">
                    {product.name}
                  </Typography>
                  <Typography color={"textSecondary"} variant="body1">
                    {product.variant}
                  </Typography>
                  <Typography color={"textSecondary"} variant="body1">
                    {i18n.t("{{ordersCount}} Orders", {
                      ordersCount: product.orders
                    })}
                  </Typography>
                </TableCell>
              ) : (
                <Skeleton />
              )}

              <TableCell>
                <Typography variant="body1" align={"right"}>
                  {product &&
                  product.price !== undefined &&
                  product.price.amount !== undefined &&
                  product.price.currency !== undefined ? (
                    <Money
                      amount={product.price.amount}
                      currency={product.price.currency}
                    />
                  ) : (
                    <Skeleton />
                  )}
                </Typography>
              </TableCell>
            </TableRow>
          ),
          () => (
            <TableRow>
              <TableCell>
                <Typography variant="body1">
                  {i18n.t("No products found")}
                </Typography>
              </TableCell>
            </TableRow>
          )
        )}
      </TableBody>
    </Table>
  )
);

export default HomeProductList;
