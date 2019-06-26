import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import Typography from "@material-ui/core/Typography";
import React from "react";

import CardSpacer from "@saleor/components/CardSpacer";
import CardTitle from "@saleor/components/CardTitle";
import Date from "@saleor/components/Date";
import FormSpacer from "@saleor/components/FormSpacer";
import Hr from "@saleor/components/Hr";
import Money from "@saleor/components/Money";
import Percent from "@saleor/components/Percent";
import Skeleton from "@saleor/components/Skeleton";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { VoucherDiscountValueType } from "../../../types/globalTypes";
import { translateVoucherTypes } from "../../translations";
import { VoucherDetails_voucher } from "../../types/VoucherDetails";

export interface VoucherSummaryProps {
  defaultCurrency: string;
  voucher: VoucherDetails_voucher;
}

const VoucherSummary: React.StatelessComponent<VoucherSummaryProps> = ({
  defaultCurrency,
  voucher
}) => {
  const translatedVoucherTypes = translateVoucherTypes();

  return (
    <Card>
      <CardTitle title={i18n.t("Summary")} />
      <CardContent>
        <Typography variant="caption">{i18n.t("Code")}</Typography>
        <Typography>
          {maybe<React.ReactNode>(() => voucher.code, <Skeleton />)}
        </Typography>
        <FormSpacer />

        <Typography variant="caption">{i18n.t("Applies to")}</Typography>
        <Typography>
          {maybe<React.ReactNode>(
            () => translatedVoucherTypes[voucher.type],
            <Skeleton />
          )}
        </Typography>
        <FormSpacer />

        <Typography variant="caption">{i18n.t("Value")}</Typography>
        <Typography>
          {maybe<React.ReactNode>(
            () =>
              voucher.discountValueType === VoucherDiscountValueType.FIXED ? (
                <Money
                  money={{
                    amount: voucher.discountValue,
                    currency: defaultCurrency
                  }}
                />
              ) : (
                <Percent amount={voucher.discountValue} />
              ),
            <Skeleton />
          )}
        </Typography>

        <CardSpacer />
        <Hr />
        <CardSpacer />

        <Typography variant="caption">{i18n.t("Start Date")}</Typography>
        <Typography>
          {maybe<React.ReactNode>(
            () => (
              <Date date={voucher.startDate} plain />
            ),
            <Skeleton />
          )}
        </Typography>
        <FormSpacer />

        <Typography variant="caption">{i18n.t("End Date")}</Typography>
        <Typography>
          {maybe<React.ReactNode>(
            () =>
              voucher.endDate === null ? (
                "-"
              ) : (
                <Date date={voucher.endDate} plain />
              ),
            <Skeleton />
          )}
        </Typography>

        <CardSpacer />
        <Hr />
        <CardSpacer />

        <Typography variant="caption">{i18n.t("Min. Order Value")}</Typography>
        <Typography>
          {maybe<React.ReactNode>(
            () =>
              voucher.minAmountSpent ? (
                <Money money={voucher.minAmountSpent} />
              ) : (
                "-"
              ),
            <Skeleton />
          )}
        </Typography>
        <FormSpacer />

        <Typography variant="caption">{i18n.t("Usage Limit")}</Typography>
        <Typography>
          {maybe<React.ReactNode>(
            () => (voucher.usageLimit === null ? "-" : voucher.usageLimit),
            <Skeleton />
          )}
        </Typography>
      </CardContent>
    </Card>
  );
};
VoucherSummary.displayName = "VoucherSummary";
export default VoucherSummary;
