import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import Typography from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Money from "../../../components/Money";
import Skeleton from "../../../components/Skeleton";
import TableCellAvatar from "../../../components/TableCellAvatar";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";

interface MoneyType {
  amount: number;
  currency: string;
}
interface HomeProductListProps {
  topProducts: Array<{
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
  avatarSpacing: {
    paddingBottom: theme.spacing.unit * 2,
    paddingTop: theme.spacing.unit * 2
  },
  tableRow: {
    cursor: "pointer" as "pointer"
  }
}));

export const HomeProductList = decorate<HomeProductListProps>(
  ({ classes, topProducts, onRowClick }) => (
    <Card>
      <CardTitle title={i18n.t("Top products")} />
      <Table>
        <TableBody>
          {renderCollection(
            topProducts,
            product => (
              <TableRow
                key={product ? product.id : "skeleton"}
                hover={!!product}
                className={classNames({
                  [classes.tableRow]: !!product
                })}
                onClick={!!product ? onRowClick(product.id) : undefined}
              >
                <TableCellAvatar
                  className={classes.avatarSpacing}
                  thumbnail={product && product.thumbnailUrl}
                  avatarSize={classes.avatarSize}
                />

                <TableCell>
                  {product ? (
                    <>
                      <Typography color={"primary"}>{product.name}</Typography>
                      <Typography color={"textSecondary"}>
                        {product.variant}
                      </Typography>
                      <Typography color={"textSecondary"}>
                        {i18n.t("{{ordersCount}} Orders", {
                          ordersCount: product.orders
                        })}
                      </Typography>
                    </>
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>

                <TableCell>
                  <Typography align={"right"}>
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
                  <Typography>{i18n.t("No products found")}</Typography>
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);

export default HomeProductList;
