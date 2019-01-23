import Card from "@material-ui/core/Card";
import { createStyles, WithStyles, withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import DateFormatter from "../../../components/DateFormatter";
import Money from "../../../components/Money";
import Percent from "../../../components/Percent";
import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListProps } from "../../../types";
import { VoucherDiscountValueType } from "../../../types/globalTypes";
import { VoucherList_vouchers_edges_node } from "../../types/VoucherList";

export interface VoucherListProps extends ListProps {
  defaultCurrency: string;
  vouchers: VoucherList_vouchers_edges_node[];
}

const styles = createStyles({
  tableRow: {
    cursor: "pointer"
  },
  textRight: {
    textAlign: "right"
  },
  wideColumn: {
    width: "40%"
  }
});

const VoucherList = withStyles(styles, {
  name: "VoucherList"
})(
  ({
    classes,
    defaultCurrency,
    disabled,
    onNextPage,
    onPreviousPage,
    onRowClick,
    pageInfo,
    vouchers
  }: VoucherListProps & WithStyles<typeof styles>) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell className={classes.wideColumn}>
              {i18n.t("Name", {
                context: "voucher list table header"
              })}
            </TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Min. Spent", {
                context: "voucher list table header"
              })}
            </TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Starts", {
                context: "voucher list table header"
              })}
            </TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Ends", {
                context: "voucher list table header"
              })}
            </TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Value", {
                context: "voucher list table header"
              })}
            </TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Uses", {
                context: "voucher list table header"
              })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={6}
              hasNextPage={pageInfo && !disabled ? pageInfo.hasNextPage : false}
              onNextPage={onNextPage}
              hasPreviousPage={
                pageInfo && !disabled ? pageInfo.hasPreviousPage : false
              }
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {renderCollection(
            vouchers,
            voucher => (
              <TableRow
                className={!!voucher ? classes.tableRow : undefined}
                hover={!!voucher}
                key={voucher ? voucher.id : "skeleton"}
              >
                <TableCell
                  className={classes.textRight}
                  onClick={voucher ? onRowClick(voucher.id) : undefined}
                >
                  {maybe<React.ReactNode>(() => voucher.name, <Skeleton />)}
                </TableCell>
                <TableCell className={classes.textRight}>
                  {voucher && voucher.minAmountSpent ? (
                    <Money money={voucher.minAmountSpent} />
                  ) : voucher && voucher.minAmountSpent === null ? (
                    "-"
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell className={classes.textRight}>
                  {voucher && voucher.startDate ? (
                    <DateFormatter date={voucher.startDate} />
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell className={classes.textRight}>
                  {voucher && voucher.endDate ? (
                    <DateFormatter date={voucher.endDate} />
                  ) : voucher && voucher.endDate === null ? (
                    "-"
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell
                  className={classes.textRight}
                  onClick={voucher ? onRowClick(voucher.id) : undefined}
                >
                  {voucher &&
                  voucher.discountValueType &&
                  voucher.discountValue ? (
                    voucher.discountValueType ===
                    VoucherDiscountValueType.FIXED ? (
                      <Money
                        money={{
                          amount: voucher.discountValue,
                          currency: defaultCurrency
                        }}
                      />
                    ) : (
                      <Percent amount={voucher.discountValue} />
                    )
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell className={classes.textRight}>
                  {voucher && voucher.usageLimit ? (
                    voucher.usageLimit
                  ) : voucher && voucher.usageLimit === null ? (
                    "-"
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={6}>{i18n.t("No vouchers found")}</TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
VoucherList.displayName = "VoucherList";
export default VoucherList;
