import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import { createVoucherName, VoucherType } from "../..";
import DateFormatter from "../../../components/DateFormatter";
import Money from "../../../components/Money";
import Percent from "../../../components/Percent";
import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";
import { ListProps } from "../../../types";

interface VoucherListProps extends ListProps {
  currency?: string;
  vouchers?: Array<{
    id: string;
    name: string;
    type: VoucherType;
    startDate: string | null;
    endDate: string | null;
    discountValueType: "PERCENTAGE" | "FIXED" | string;
    discountValue: number;
    limit: {
      amount: number;
      currency: string;
    } | null;
    product: {
      name: string;
    } | null;
    category: {
      name: string;
    } | null;
  }>;
}

const decorate = withStyles(theme => ({
  link: {
    color: theme.palette.secondary.main,
    cursor: "pointer" as "pointer"
  },
  textRight: { textAlign: "right" as "right" }
}));
const VoucherList = decorate<VoucherListProps>(
  ({
    classes,
    currency,
    disabled,
    pageInfo,
    vouchers,
    onNextPage,
    onPreviousPage,
    onRowClick
  }) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{i18n.t("Name", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("Start date", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("End date", { context: "object" })}</TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Discount", { context: "object" })}
            </TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Limit", { context: "object" })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={5}
              hasNextPage={
                pageInfo && !disabled ? pageInfo.hasNextPage : undefined
              }
              onNextPage={onNextPage}
              hasPreviousPage={
                pageInfo && !disabled ? pageInfo.hasPreviousPage : undefined
              }
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {renderCollection(
            vouchers,
            voucher => (
              <TableRow key={voucher ? voucher.id : "skeleton"}>
                <TableCell>
                  {voucher ? (
                    <span
                      onClick={onRowClick && onRowClick(voucher.id)}
                      className={classes.link}
                    >
                      {voucher ? (
                        voucher.name !== null ? (
                          voucher.name
                        ) : (
                          createVoucherName(voucher, currency)
                        )
                      ) : (
                        <Skeleton />
                      )}
                    </span>
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell>
                  {voucher ? (
                    voucher.startDate !== null ? (
                      <DateFormatter date={voucher.startDate} />
                    ) : (
                      "-"
                    )
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell>
                  {voucher ? (
                    voucher.endDate !== null ? (
                      <DateFormatter date={voucher.endDate} />
                    ) : (
                      "-"
                    )
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell className={classes.textRight}>
                  {voucher &&
                  voucher.discountValueType &&
                  voucher.discountValue ? (
                    voucher.discountValueType === "PERCENTAGE" ? (
                      <Percent amount={voucher.discountValue} />
                    ) : (
                      <Money
                        money={{
                          amount: voucher.discountValue,
                          currency
                        }}
                      />
                    )
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell className={classes.textRight}>
                  {voucher ? (
                    voucher.limit !== null ? (
                      <Money money={voucher.limit} />
                    ) : (
                      "-"
                    )
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={5}>{i18n.t("No vouchers found")}</TableCell>
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
