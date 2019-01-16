import Card from "@material-ui/core/Card";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
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
import { maybe, renderCollection } from "../../../misc";
import { Home_productTopToday_edges_node } from "../../types/Home";

const styles = (theme: Theme) =>
  createStyles({
    avatarProps: {
      height: 64,
      width: 64
    },
    avatarSpacing: {
      paddingBottom: theme.spacing.unit * 2,
      paddingTop: theme.spacing.unit * 2
    },
    noProducts: {
      paddingBottom: 20,
      paddingTop: 20
    },
    tableRow: {
      cursor: "pointer"
    }
  });

interface HomeProductListProps extends WithStyles<typeof styles> {
  topProducts: Home_productTopToday_edges_node[];
  onRowClick: (productId: string, variantId: string) => void;
}

export const HomeProductList = withStyles(styles, { name: "HomeProductList" })(
  ({ classes, topProducts, onRowClick }: HomeProductListProps) => (
    <Card>
      <CardTitle title={i18n.t("Top products")} />
      <Table>
        <TableBody>
          {renderCollection(
            topProducts,
            variant => (
              <TableRow
                key={variant ? variant.id : "skeleton"}
                hover={!!variant}
                className={classNames({
                  [classes.tableRow]: !!variant
                })}
                onClick={
                  !!variant
                    ? () => onRowClick(variant.product.id, variant.id)
                    : undefined
                }
              >
                <TableCellAvatar
                  className={classes.avatarSpacing}
                  thumbnail={maybe(() => variant.product.thumbnail.url)}
                  avatarProps={classes.avatarProps}
                />

                <TableCell>
                  {variant ? (
                    <>
                      <Typography color={"primary"}>
                        {variant.product.name}
                      </Typography>
                      <Typography color={"textSecondary"}>
                        {maybe(() =>
                          variant.attributes
                            .map(attribute => attribute.value)
                            .sort((a, b) =>
                              a.sortOrder > b.sortOrder ? 1 : -1
                            )
                            .map(attribute => attribute.name)
                            .join(" / ")
                        )}
                      </Typography>
                      <Typography color={"textSecondary"}>
                        {i18n.t("{{ordersCount}} Orders", {
                          ordersCount: variant.quantityOrdered
                        })}
                      </Typography>
                    </>
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>

                <TableCell>
                  <Typography align={"right"}>
                    {maybe(
                      () => (
                        <Money money={variant.revenue.gross} />
                      ),
                      <Skeleton />
                    )}
                  </Typography>
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell className={classes.noProducts}>
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

HomeProductList.displayName = "HomeProductList";
export default HomeProductList;
